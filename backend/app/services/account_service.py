"""
账号生命周期业务服务（删除清理 / 合并迁移）
--------------------------------------------------------------------------
拆分说明：账号删除与合并改由业务项目（本服务）主动执行——
- 删除：调度器轮询 auth 待清理列表（GET /internal/purge/pending）→
  purge_user_business_data 幂等清理业务库 → 经 auth_client.report_purge 上报
  （auth 收齐第一方上报后标记用户已删除）
- 合并：auth bind-email 邮箱冲突创建合并任务 → 前端调 POST /api/v1/account/merge →
  request_account_merge 从 auth 获取真实主账号 → merge_business_data 迁移业务库
  → confirm 上报（失败落 merge_sync_tasks 由后台循环重试）

各服务数据库独立事务：本服务业务库迁移与 auth 用户库合并分别提交，
完成状态记录于 merge_sync_tasks（本地）与 auth user_merge_tasks。
"""
from __future__ import annotations

import json

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import auth_client
from ..models.plan import CheckinPlan, PlanNotificationChannel, PlanNotificationTime
from ..models.notification_channel import NotificationChannel
from ..models.notification_log import NotificationLog
from ..models.checkin_record import CheckinRecord
from ..models.merge_task import MERGE_SYNC_DONE, MERGE_SYNC_PENDING, MergeSyncTask
from ..schemas.notification_channel import CHANNEL_TYPE_WECHAT, CHANNEL_TYPE_ZNX
from ..services.notification_channel_service import NotificationChannelService


async def purge_user_business_data(db: AsyncSession, user_id: int) -> None:
    """
    幂等清理用户全部业务数据（注销冷静期到期后由调度器调用）
    - 清理范围：checkin_records / plan_notification_times / plan_notification_channels /
      notification_logs / notification_channels / checkin_plans
    - 幂等：目标用户无业务数据亦正常返回（上报前用户会重复出现在待清理列表中）
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


async def _merge_channel_references(
    db: AsyncSession, from_channel_id: int, to_channel_id: int
) -> None:
    """
    将引用旧渠道的记录迁移到新渠道，并处理 plan_notification_channels 唯一冲突
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


async def merge_business_data(db: AsyncSession, from_user_id: int, to_user_id: int) -> None:
    """
    合并从账号的业务库数据到主账号
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


async def request_account_merge(db: AsyncSession, from_user_id: int) -> str:
    """
    账号合并请求（前端 POST /api/v1/account/merge 触发）
    - 从 auth 查询合并任务获取真实主账号 ID（不接受前端传入，防伪造目标账号）
    - 同事务完成业务数据迁移 + 落本地同步记录（pending）
    - confirm 上报 auth 执行用户库合并，成功置 done；失败保留 pending 由
      后台循环重试（retry_pending_merges）
    :param from_user_id: 当前登录用户ID（从账号，来自 JWT）
    :return: "completed"（合并完成）/ "processing"（已迁移，待后台重试上报）
    :raises ValueError: 无待合并任务
    """
    # 1. 本地已完成：幂等返回
    task_result = await db.execute(
        select(MergeSyncTask).where(MergeSyncTask.from_user_id == from_user_id)
    )
    local_task = task_result.scalar_one_or_none()
    if local_task and local_task.status == MERGE_SYNC_DONE:
        return "completed"

    # 2. 从 auth 获取合并任务（无任务 404 → None）
    task = await auth_client.get_merge_task(from_user_id)
    if task is None:
        if local_task:
            # 残局兜底：本地 pending 但 auth 任务已不存在（auth 已合并完成），
            # 补记 done 幂等返回
            local_task.status = MERGE_SYNC_DONE
            await db.commit()
            return "completed"
        raise ValueError("无待合并任务")
    to_user_id = task["to_user_id"]
    if to_user_id == from_user_id:
        raise ValueError("从账号与主账号不能相同")

    # 3. 同事务：业务数据迁移 + 落同步记录（迁移幂等，重复调用无副作用）
    await merge_business_data(db, from_user_id, to_user_id)
    if local_task:
        # 以 auth 任务下发的最新主账号为准（用户可能改绑了其他邮箱）
        local_task.to_user_id = to_user_id
        local_task.status = MERGE_SYNC_PENDING
    else:
        db.add(MergeSyncTask(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            status=MERGE_SYNC_PENDING,
        ))
    await db.commit()

    # 4. confirm 上报（auth 执行用户库合并）；失败由后台循环重试
    try:
        await auth_client.confirm_merge(from_user_id, to_user_id)
    except Exception:
        return "processing"
    local_task = (await db.execute(
        select(MergeSyncTask).where(MergeSyncTask.from_user_id == from_user_id)
    )).scalar_one()
    local_task.status = MERGE_SYNC_DONE
    await db.commit()
    return "completed"


async def retry_pending_merges(db: AsyncSession) -> int:
    """
    重试上报待确认的合并记录（后台循环调用；confirm 失败的补偿路径）
    :return: 本轮成功确认的记录数
    """
    result = await db.execute(
        select(MergeSyncTask).where(MergeSyncTask.status == MERGE_SYNC_PENDING)
    )
    pending_tasks = result.scalars().all()
    confirmed = 0
    for task in pending_tasks:
        try:
            await auth_client.confirm_merge(task.from_user_id, task.to_user_id)
        except Exception:
            # auth 不可达或合并被拒：保留 pending，下一轮重试
            continue
        task.status = MERGE_SYNC_DONE
        confirmed += 1
    if confirmed > 0:
        await db.commit()
    return confirmed
