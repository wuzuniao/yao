"""
服务间内部接口（挂在 /internal 前缀，仅供 auth 统一认证服务调用）
--------------------------------------------------------------------------
安全：全部端点经 X-Service-Token 校验（与 auth 服务侧 oauth_clients 表中
yao 行的 callback_service_token 一致，即本服务 .env 的 AUTH_SERVICE_TOKEN），
并以 HTTPS（域名）传输。

端点清单（auth 侧的对应回调封装见其 services/business_callback.py）：
- POST /internal/users/{user_id}/purge   账号删除清理（幂等：无业务数据亦返回成功）
- POST /internal/users/merge             账号合并（绑定邮箱触发，从账号业务数据迁移到主账号）
"""
from __future__ import annotations

import json
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_db
from ...core.security import Security
from ...models.plan import CheckinPlan, PlanNotificationChannel, PlanNotificationTime
from ...models.notification_channel import NotificationChannel
from ...models.notification_log import NotificationLog
from ...models.checkin_record import CheckinRecord
from ...schemas.notification_channel import CHANNEL_TYPE_ZNX, CHANNEL_TYPE_WECHAT
from ...services.notification_channel_service import NotificationChannelService

router = APIRouter()


async def require_service_token(
    x_service_token: str | None = Header(default=None, alias="X-Service-Token"),
) -> None:
    """
    /internal/* 内部接口守卫：校验 X-Service-Token（恒定时间比较防时序攻击）
    :raises HTTPException: 401 未携带或令牌不匹配
    """
    if not settings.AUTH_SERVICE_TOKEN or not x_service_token:
        raise HTTPException(status_code=401, detail="服务间通信令牌无效")
    if not secrets.compare_digest(x_service_token, settings.AUTH_SERVICE_TOKEN):
        raise HTTPException(status_code=401, detail="服务间通信令牌无效")


class MergeUsers(BaseModel):
    """账号合并请求体（auth 的 business_callback.notify_user_merge 发起）"""

    from_user_id: int  # 从账号（被合并删除的账号）
    to_user_id: int    # 主账号（合并后保留的账号）

    @field_validator("from_user_id", "to_user_id")
    @classmethod
    def validate_user_id(cls, v: int) -> int:
        return Security.validate_positive_int(v, field_name="用户ID")


async def _merge_channel_references(
    db: AsyncSession, from_channel_id: int, to_channel_id: int
) -> None:
    """
    将引用旧渠道的记录迁移到新渠道，并处理 plan_notification_channels 唯一冲突
    （自 yao 原用户模块的渠道引用合并逻辑平移，行为不变）
    :param from_channel_id: 待删除的旧渠道ID
    :param to_channel_id: 保留的目标渠道ID
    """
    # 1. 找出同时存在新旧渠道关联的计划ID（会产生唯一冲突）
    conflict_result = await db.execute(
        select(PlanNotificationChannel.plan_id).where(
            PlanNotificationChannel.channel_id == from_channel_id,
            PlanNotificationChannel.plan_id.in_(
                select(PlanNotificationChannel.plan_id).where(
                    PlanNotificationChannel.channel_id == to_channel_id
                )
            ),
        )
    )
    conflict_plan_ids = [row[0] for row in conflict_result.all()]

    # 2. 删除旧渠道侧会产生冲突的关联记录
    if conflict_plan_ids:
        await db.execute(
            delete(PlanNotificationChannel).where(
                PlanNotificationChannel.channel_id == from_channel_id,
                PlanNotificationChannel.plan_id.in_(conflict_plan_ids),
            )
        )

    # 3. 将其余关联记录的 channel_id 指向新渠道
    await db.execute(
        update(PlanNotificationChannel)
        .where(PlanNotificationChannel.channel_id == from_channel_id)
        .values(channel_id=to_channel_id)
    )

    # 4. 同步更新通知日志中的渠道引用（历史记录跟随合并后的渠道）
    await db.execute(
        update(NotificationLog)
        .where(NotificationLog.channel_id == from_channel_id)
        .values(channel_id=to_channel_id)
    )


async def _merge_business_data(db: AsyncSession, from_user_id: int, to_user_id: int) -> None:
    """
    合并从账号的业务库数据到主账号
    （自 yao 原用户模块的业务数据合并逻辑平移，行为不变）
    - checkin_plans / checkin_records / notification_logs：直接更新 user_id
    - notification_channels：站内信/微信需去重合并；其他类型直接转移归属
    """
    # 1. 业务表 user_id 整体迁移
    await db.execute(
        update(CheckinPlan)
        .where(CheckinPlan.user_id == from_user_id)
        .values(user_id=to_user_id)
    )
    await db.execute(
        update(CheckinRecord)
        .where(CheckinRecord.user_id == from_user_id)
        .values(user_id=to_user_id)
    )
    await db.execute(
        update(NotificationLog)
        .where(NotificationLog.user_id == from_user_id)
        .values(user_id=to_user_id)
    )

    # 2. 通知渠道：按类型分别处理
    sub_channels_result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.user_id == from_user_id)
    )
    sub_channels = sub_channels_result.scalars().all()

    main_channels_result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.user_id == to_user_id)
    )
    main_channels_by_type = {
        ch.channel_type: ch for ch in main_channels_result.scalars().all()
    }

    for ch in sub_channels:
        if ch.channel_type == CHANNEL_TYPE_ZNX:
            # 站内信：系统默认渠道，一个用户仅保留一条
            main_znx = main_channels_by_type.get(CHANNEL_TYPE_ZNX)
            if main_znx:
                await _merge_channel_references(db, ch.id, main_znx.id)
                await db.delete(ch)
            else:
                ch.user_id = to_user_id
                ch.channel_value = str(to_user_id)
        elif ch.channel_type == CHANNEL_TYPE_WECHAT:
            # 微信：额度制渠道，合并 granted/sent 额度
            main_wx = main_channels_by_type.get(CHANNEL_TYPE_WECHAT)
            if main_wx:
                sub_quota = NotificationChannelService.parse_wechat_channel_value(ch.channel_value)
                main_quota = NotificationChannelService.parse_wechat_channel_value(main_wx.channel_value)
                merged_quota = {
                    "granted": sub_quota["granted"] + main_quota["granted"],
                    "sent": sub_quota["sent"] + main_quota["sent"],
                }
                main_wx.channel_value = json.dumps(merged_quota, ensure_ascii=False)
                main_wx.enabled = True
                await _merge_channel_references(db, ch.id, main_wx.id)
                await db.delete(ch)
            else:
                ch.user_id = to_user_id
        else:
            # 邮件等其他自定义渠道：直接转移归属
            ch.user_id = to_user_id


@router.post(
    "/users/{user_id}/purge",
    dependencies=[Depends(require_service_token)],
)
async def purge_user_business_data(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    账号删除清理（auth 的账号删除流程第一步回调）
    - 幂等：目标用户无业务数据亦返回成功（auth 侧据此决定是否删除用户库数据）
    - 清理范围（原 purge_expired_deletions 第 1-6 步逻辑平移）：
      plan_notification_times / plan_notification_channels / checkin_records /
      notification_logs / notification_channels / checkin_plans
    """
    # 1. 查询该用户所有的计划 ID（用于删除计划关联表）
    plan_ids_result = await db.execute(
        select(CheckinPlan.id).where(CheckinPlan.user_id == user_id)
    )
    plan_ids = plan_ids_result.scalars().all()

    # 2. 先删引用方：打卡记录（checkin_records 对 plan_notification_times 有
    #    物理 ForeignKey 声明，测试库 create_all 会建出约束，须先删引用行）
    await db.execute(
        delete(CheckinRecord).where(CheckinRecord.user_id == user_id)
    )

    # 3. 删除计划关联的时间点和渠道关联（通过 plan_id 过滤）
    if plan_ids:
        await db.execute(
            delete(PlanNotificationTime).where(
                PlanNotificationTime.plan_id.in_(plan_ids)
            )
        )
        await db.execute(
            delete(PlanNotificationChannel).where(
                PlanNotificationChannel.plan_id.in_(plan_ids)
            )
        )

    # 4. 删除通知发送记录（user_id 过滤）
    await db.execute(
        delete(NotificationLog).where(NotificationLog.user_id == user_id)
    )

    # 5. 删除通知渠道配置（user_id 过滤）
    await db.execute(
        delete(NotificationChannel).where(NotificationChannel.user_id == user_id)
    )

    # 6. 删除打卡计划主表（user_id 过滤）
    await db.execute(
        delete(CheckinPlan).where(CheckinPlan.user_id == user_id)
    )

    await db.commit()
    return {"code": 0, "msg": "success", "data": None}


@router.post("/users/merge", dependencies=[Depends(require_service_token)])
async def merge_users(payload: MergeUsers, db: AsyncSession = Depends(get_db)):
    """
    账号合并（auth 的 bind_email 触发账号合并时回调）
    - 将 from_user_id（从账号）的业务数据全部迁移到 to_user_id（主账号）名下
    - 站内信/微信渠道去重合并（微信额度 granted/sent 累加），邮件渠道直接转移
    - 任一步骤失败抛出异常（HTTP 500），auth 侧中止合并（无半合并状态）
    """
    if payload.from_user_id == payload.to_user_id:
        raise HTTPException(status_code=400, detail="从账号与主账号不能相同")
    await _merge_business_data(db, payload.from_user_id, payload.to_user_id)
    await db.commit()
    return {"code": 0, "msg": "success", "data": None}
