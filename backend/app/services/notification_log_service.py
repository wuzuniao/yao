from typing import Any

from sqlalchemy import select, and_, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification_log import NotificationLog
from ..models.notification_channel import NotificationChannel
from ..models.plan import CheckinPlan
from ..schemas.notification_channel import CHANNEL_TYPE_ZNX
from ..schemas.notification_log import LOG_STATUS_SUCCESS, LOG_STATUS_UNREAD


class NotificationLogService:
    """
    通知发送记录业务逻辑服务
    --------------------------------------------------------------------------
    - 站内信列表：查询当前用户所有站内信记录（关联计划名称/备注），支持分页
    - 标记已读：将未读站内信（status=2）更新为已读（status=0）
    - 未读数量：用于通知按钮图标切换（tongzhi_1/tongzhi_0）
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_znx_by_user(
        self, user_id: int, page: int = 1, limit: int = 20
    ) -> dict[str, Any]:
        """
        查询用户站内信列表（分页）
        - JOIN notification_channels 过滤 channel_type='站内信'
        - LEFT JOIN checkin_plans 获取计划名称/备注（计划可能已删除，显示"已删除计划"）
        - 按 send_time 倒序（最新消息在前）
        - 返回 items + total + has_more + unread_count
        """
        offset = (page - 1) * limit
        # 使用 outerjoin 关联计划：计划已删除时仍展示该条消息（plan_name 显示占位）
        result = await self.db.execute(
            select(
                NotificationLog.id,
                NotificationLog.plan_id,
                NotificationLog.channel_id,
                NotificationLog.send_time,
                NotificationLog.status,
                CheckinPlan.name.label("plan_name"),
                CheckinPlan.remark.label("plan_remark"),
            )
            .select_from(NotificationLog)
            .join(
                NotificationChannel,
                NotificationLog.channel_id == NotificationChannel.id,
            )
            .outerjoin(CheckinPlan, NotificationLog.plan_id == CheckinPlan.id)
            .where(
                and_(
                    NotificationLog.user_id == user_id,
                    NotificationChannel.channel_type == CHANNEL_TYPE_ZNX,
                )
            )
            .order_by(NotificationLog.send_time.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = result.all()
        items = [
            {
                "id": row.id,
                "plan_id": row.plan_id,
                "plan_name": row.plan_name or "(已删除计划)",
                "plan_remark": row.plan_remark or "",
                "channel_id": row.channel_id,
                "send_time": row.send_time.isoformat() if row.send_time else None,
                "status": row.status,
                "is_unread": row.status == LOG_STATUS_UNREAD,
            }
            for row in rows
        ]

        # 总数（用于分页判断）
        total_result = await self.db.execute(
            select(sa_func.count(NotificationLog.id))
            .select_from(NotificationLog)
            .join(
                NotificationChannel,
                NotificationLog.channel_id == NotificationChannel.id,
            )
            .where(
                and_(
                    NotificationLog.user_id == user_id,
                    NotificationChannel.channel_type == CHANNEL_TYPE_ZNX,
                )
            )
        )
        total = int(total_result.scalar() or 0)

        # 未读数量（用于通知图标切换）
        unread_count = await self.count_unread(user_id)

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": (offset + limit) < total,
            "unread_count": unread_count,
        }

    async def count_unread(self, user_id: int) -> int:
        """统计用户未读站内信数量（status=2，用于通知图标切换）"""
        result = await self.db.execute(
            select(sa_func.count(NotificationLog.id))
            .select_from(NotificationLog)
            .join(
                NotificationChannel,
                NotificationLog.channel_id == NotificationChannel.id,
            )
            .where(
                and_(
                    NotificationLog.user_id == user_id,
                    NotificationChannel.channel_type == CHANNEL_TYPE_ZNX,
                    NotificationLog.status == LOG_STATUS_UNREAD,
                )
            )
        )
        return int(result.scalar() or 0)

    async def mark_as_read(self, log_id: int, user_id: int) -> NotificationLog:
        """
        标记站内信为已读
        - 校验记录存在且属于该用户
        - 仅未读（status=2）记录可标记，已读记录直接返回保持不变
        - 更新 status 为 0（已读/成功）
        """
        result = await self.db.execute(
            select(NotificationLog).where(NotificationLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            raise ValueError("消息不存在")
        if log.user_id != user_id:
            raise ValueError("无权操作该消息")
        if log.status != LOG_STATUS_UNREAD:
            # 已读记录无需重复标记，直接返回
            return log
        log.status = LOG_STATUS_SUCCESS
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"标记已读失败：{e}") from e
        await self.db.refresh(log)
        return log
