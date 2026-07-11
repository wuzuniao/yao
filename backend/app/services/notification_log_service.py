from datetime import datetime, time as dt_time, timedelta
from typing import Any

from sqlalchemy import select, and_, func as sa_func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.checkin_record import CheckinRecord
from ..models.notification_log import NotificationLog
from ..models.notification_channel import NotificationChannel
from ..models.plan import CheckinPlan
from ..schemas.notification_channel import CHANNEL_TYPE_ZNX
from ..schemas.notification_log import LOG_STATUS_SUCCESS, LOG_STATUS_UNREAD
from .checkin_service import CheckinService


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

    async def _auto_mark_read_if_checked(self, user_id: int) -> None:
        """
        自动标记已读：扫描未读站内信，若对应提醒时间的匹配区间内已有打卡记录，则标记为已读
        - 匹配区间复用 CheckinService._get_match_intervals（按相邻中点划分，覆盖全天 0:00-24:00）
        - plan_time_id 为 NULL / 计划已删除 / notify_date 为 NULL / 无打卡记录 → 保持未读
        - 已读（status=0）记录不参与判定
        """
        # 1. 查询该用户所有未读站内信记录
        unread_result = await self.db.execute(
            select(NotificationLog)
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
        unread_logs = list(unread_result.scalars().all())
        if not unread_logs:
            return

        # 2. 批量加载相关计划的提醒时间（selectinload 避免 N+1）
        plan_ids = {log.plan_id for log in unread_logs if log.plan_time_id is not None}
        plan_times_map: dict[int, list] = {}
        if plan_ids:
            plans_result = await self.db.execute(
                select(CheckinPlan)
                .where(CheckinPlan.id.in_(plan_ids))
                .options(selectinload(CheckinPlan.notification_times))
            )
            for plan in plans_result.scalars().all():
                plan_times_map[plan.id] = sorted(
                    plan.notification_times, key=lambda nt: nt.notification_time
                )

        # 3. 逐条判定匹配区间内是否有打卡记录
        marked = False
        for log in unread_logs:
            if log.plan_time_id is None or log.notify_date is None:
                continue
            times = plan_times_map.get(log.plan_id)
            if not times:
                # 计划已删除 → 无法获取提醒时间，保持未读
                continue
            # 定位 plan_time_id 在排序后提醒时间列表中的索引
            idx = next(
                (i for i, nt in enumerate(times) if nt.id == log.plan_time_id), None
            )
            if idx is None:
                continue
            # 计算匹配区间并查询该区间内是否有打卡记录
            intervals = CheckinService._get_match_intervals(times)
            start_min, end_min = intervals[idx]
            day_start = datetime.combine(log.notify_date, dt_time(0, 0, 0))
            interval_start = day_start + timedelta(minutes=start_min)
            interval_end = day_start + timedelta(minutes=end_min)
            check_result = await self.db.execute(
                select(CheckinRecord.id)
                .where(
                    and_(
                        CheckinRecord.user_id == user_id,
                        CheckinRecord.plan_id == log.plan_id,
                        CheckinRecord.actual_time >= interval_start,
                        CheckinRecord.actual_time < interval_end,
                    )
                )
                .limit(1)
            )
            if check_result.scalar_one_or_none() is not None:
                log.status = LOG_STATUS_SUCCESS
                marked = True

        # 4. 提交事务（失败则回滚，不影响后续列表查询）
        if marked:
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()

    async def list_znx_by_user(
        self, user_id: int, page: int = 1, limit: int = 20
    ) -> dict[str, Any]:
        """
        查询用户站内信列表（分页）
        - 先自动标记已读：扫描未读站内信，匹配区间内有打卡记录的更新为已读
        - JOIN notification_channels 过滤 channel_type='站内信'
        - LEFT JOIN checkin_plans 获取计划名称/备注（计划可能已删除，显示"已删除计划"）
        - 按 send_time 倒序（最新消息在前）
        - 返回 items + total + has_more + unread_count
        - items 字段：id/plan_name/plan_remark/send_time/is_unread
        """
        # 自动标记已读：扫描未读站内信，匹配区间内有打卡记录的更新为已读
        await self._auto_mark_read_if_checked(user_id)

        offset = (page - 1) * limit
        # 使用 outerjoin 关联计划：计划已删除时仍展示该条消息（plan_name 显示占位）
        result = await self.db.execute(
            select(
                NotificationLog.id,
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
                "plan_name": row.plan_name or "(已删除计划)",
                "plan_remark": row.plan_remark or "",
                "send_time": row.send_time.isoformat() if row.send_time else None,
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

    async def mark_all_as_read(self, user_id: int) -> int:
        """
        全部标记为已读（用户主动操作）
        - 查询该用户所有 status=2 的站内信记录（JOIN notification_channels 过滤 channel_type='站内信'）
        - 批量更新 status=0（LOG_STATUS_SUCCESS）
        - 返回更新条数 updated_count；若无未读记录，返回 0，不报错
        - 不判断打卡记录，直接将所有未读站内信标记为已读
        """
        # 子查询：所有站内信渠道ID（channel_type='站内信'）
        channel_ids_subq = select(NotificationChannel.id).where(
            NotificationChannel.channel_type == CHANNEL_TYPE_ZNX
        )
        # 批量更新：该用户所有未读站内信 → status=0
        stmt = (
            update(NotificationLog)
            .where(
                and_(
                    NotificationLog.user_id == user_id,
                    NotificationLog.status == LOG_STATUS_UNREAD,
                    NotificationLog.channel_id.in_(channel_ids_subq),
                )
            )
            .values(status=LOG_STATUS_SUCCESS)
            .execution_options(synchronize_session=False)
        )
        try:
            result = await self.db.execute(stmt)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"全部标记已读失败：{e}") from e
        return int(result.rowcount or 0)
