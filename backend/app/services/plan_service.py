from datetime import time

from sqlalchemy import select, delete, update, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.plan import (
    CheckinPlan,
    PlanNotificationChannel,
    PlanNotificationTime,
)
from ..models.checkin_record import CheckinRecord
from ..models.notification_log import NotificationLog
from ..models.notification_channel import NotificationChannel
from ..schemas.plan import NotificationTimeItem
from ..utils.logger import logger
from ..utils.timezone import today_shanghai


class PlanService:
    """
    计划业务逻辑服务
    --------------------------------------------------------------------------
    - 创建计划：写入 checkin_plans 主表 + plan_notification_times 多个时间点 + plan_notification_channels 多个渠道关联
    - 查询计划：按用户ID查询，包含时间点和关联渠道
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_user(self, user_id: int) -> list[CheckinPlan]:
        """
        查询用户的所有计划（含时间点和关联渠道）
        - 排序规则：status（1-进行中 → 2-暂停 → 0-已结束）→ priority 升序 → created_at 降序
          进行中最前，暂停其次，已结束最后；同状态按 priority 数字越小越靠前；同状态同优先级新创建在前
        """
        # status 排序：用 CASE 把 1 → 0、2 → 1、0 → 2，使进行中<暂停<已结束
        status_order = case(
            (CheckinPlan.status == 1, 0),
            (CheckinPlan.status == 2, 1),
            (CheckinPlan.status == 0, 2),
            else_=3,
        )
        result = await self.db.execute(
            select(CheckinPlan)
            .where(CheckinPlan.user_id == user_id)
            .options(selectinload(CheckinPlan.notification_times), selectinload(CheckinPlan.channels))
            .order_by(status_order.asc(), CheckinPlan.priority.asc(), CheckinPlan.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, plan_id: int) -> CheckinPlan | None:
        """根据ID查询计划（含时间点和关联渠道）"""
        result = await self.db.execute(
            select(CheckinPlan)
            .where(CheckinPlan.id == plan_id)
            .options(selectinload(CheckinPlan.notification_times), selectinload(CheckinPlan.channels))
        )
        return result.scalar_one_or_none()

    async def create_plan(
        self,
        user_id: int,
        name: str,
        remark: str,
        start_date,
        end_date,
        notification_times: list[NotificationTimeItem],
        channel_ids: list[int],
        status: int = 1,
        priority: int = 3,
        repeat_weekdays: int = 127,
        end_mode: int = 0,
        total_target_count: int | None = None,
    ) -> CheckinPlan:
        """
        创建计划
        - 同时写入主表、时间点表、渠道关联表
        - 校验 channel_ids 均属于该用户
        - status：1-进行中，2-暂停，0-已结束
        - priority：0-3，数字越小优先级越高
        - repeat_weekdays/end_mode/total_target_count：重复星期位掩码与结束方式
          （end_mode=1/2 时 end_date 由调用方传哨兵值，见 Schema.effective_end_date）
        """
        # 1. 校验通知渠道归属
        await self._validate_channel_ownership(user_id, channel_ids)

        # 2. 创建计划主记录
        plan = CheckinPlan(
            user_id=user_id,
            name=name,
            remark=remark or None,
            start_date=start_date,
            end_date=end_date,
            repeat_weekdays=repeat_weekdays,
            end_mode=end_mode,
            total_target_count=total_target_count if end_mode == 1 else None,
            status=status,
            priority=priority,
        )
        self.db.add(plan)
        await self.db.flush()

        # 3. 写入通知时间点
        self._write_notification_times(plan.id, notification_times)

        # 4. 写入计划-渠道关联
        self._write_plan_channels(plan.id, channel_ids)

        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def delete_plan(self, plan_id: int, user_id: int) -> None:
        """
        删除计划
        - 以 plan_id 为过滤条件，级联删除关联的打卡记录、通知记录、通知时间点、计划-渠道关联
        - 通知渠道本身保留，仅删除与该计划的关联记录
        """
        plan = await self.get_by_id(plan_id)
        if not plan:
            raise ValueError("计划不存在")
        if plan.user_id != user_id:
            raise ValueError("无权操作该计划")

        # 按 plan_id 批量删除关联数据（先删引用 plan_time_id 的日志/记录，再删时间点）
        await self.db.execute(
            delete(CheckinRecord).where(CheckinRecord.plan_id == plan_id)
        )
        await self.db.execute(
            delete(NotificationLog).where(NotificationLog.plan_id == plan_id)
        )
        await self.db.execute(
            delete(PlanNotificationTime).where(PlanNotificationTime.plan_id == plan_id)
        )
        await self.db.execute(
            delete(PlanNotificationChannel).where(PlanNotificationChannel.plan_id == plan_id)
        )
        # 删除计划主记录（使用语句删除，避免 ORM 级联对已手动删除的关联表发出二次删除警告）
        await self.db.execute(
            delete(CheckinPlan).where(CheckinPlan.id == plan_id)
        )
        await self.db.commit()

    async def update_plan(
        self,
        plan_id: int,
        user_id: int,
        name: str,
        remark: str,
        start_date,
        end_date,
        notification_times: list[NotificationTimeItem],
        channel_ids: list[int],
        status: int = 1,
        priority: int = 3,
        repeat_weekdays: int = 127,
        end_mode: int = 0,
        total_target_count: int | None = None,
    ) -> CheckinPlan:
        """
        更新计划
        - 更新主表字段（name/remark/start_date/end_date/repeat_weekdays/end_mode/
          total_target_count/status/priority）
        - 删除旧的时间点和渠道关联，写入新的
        - 校验 channel_ids 均属于该用户
        """
        plan = await self.get_by_id(plan_id)
        if not plan:
            raise ValueError("计划不存在")
        if plan.user_id != user_id:
            raise ValueError("无权操作该计划")

        # 校验通知渠道归属
        await self._validate_channel_ownership(user_id, channel_ids)

        # 更新主记录
        plan.name = name
        plan.remark = remark or None
        plan.start_date = start_date
        plan.end_date = end_date
        plan.repeat_weekdays = repeat_weekdays
        plan.end_mode = end_mode
        plan.total_target_count = total_target_count if end_mode == 1 else None
        plan.status = status
        plan.priority = priority

        # 删除旧的时间点，写入新的
        await self.db.execute(
            delete(PlanNotificationTime).where(PlanNotificationTime.plan_id == plan_id)
        )
        self._write_notification_times(plan.id, notification_times)

        # 删除旧的渠道关联，写入新的
        await self.db.execute(
            delete(PlanNotificationChannel).where(PlanNotificationChannel.plan_id == plan_id)
        )
        self._write_plan_channels(plan.id, channel_ids)

        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    # ==================== 内部辅助方法（供 create_plan/update_plan 复用） ====================

    async def _validate_channel_ownership(self, user_id: int, channel_ids: list[int]) -> None:
        """
        校验通知渠道归属：channel_ids 非空且均属于该用户
        - 空列表 → 至少选择一个通知方式
        - 数量不一致 → 包含无效或非本用户的通知渠道
        """
        if not channel_ids:
            raise ValueError("至少选择一个通知方式")
        result = await self.db.execute(
            select(NotificationChannel).where(
                NotificationChannel.user_id == user_id,
                NotificationChannel.id.in_(channel_ids),
            )
        )
        owned_channels = list(result.scalars().all())
        if len(owned_channels) != len(set(channel_ids)):
            raise ValueError("包含无效或非本用户的通知渠道")

    @staticmethod
    def _parse_time_str(t: str) -> time:
        """将 HH:MM 或 HH:MM:SS 字符串解析为 datetime.time 对象"""
        parts = t.split(":")
        if len(parts) == 2:
            h, m = int(parts[0]), int(parts[1])
            return time(hour=h, minute=m, second=0)
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        return time(hour=h, minute=m, second=s)

    def _write_notification_times(self, plan_id: int, notification_times: list[NotificationTimeItem]) -> None:
        """为指定计划批量写入通知时间点（时间 + 提醒次数/间隔）"""
        for item in notification_times:
            self.db.add(PlanNotificationTime(
                plan_id=plan_id,
                notification_time=self._parse_time_str(item.time),
                followup_count=item.followup_count,
                followup_interval_min=item.followup_interval_min,
            ))

    def _write_plan_channels(self, plan_id: int, channel_ids: list[int]) -> None:
        """为指定计划批量写入计划-渠道关联记录"""
        for cid in channel_ids:
            self.db.add(PlanNotificationChannel(
                plan_id=plan_id,
                channel_id=cid,
            ))

    async def auto_close_expired_plans(self) -> int:
        """
        自动关闭已过期的计划
        - 查询所有 status=1（进行中）且 end_mode=0（按日期结束）且 end_date < today 的计划
        - 将其 status 更新为 0（已结束）
        - 按次数结束（end_mode=1）由打卡累计达标触发；长期（end_mode=2）不自动关闭
        - 返回受影响的行数
        """
        today = today_shanghai()
        result = await self.db.execute(
            update(CheckinPlan)
            .where(
                CheckinPlan.status == 1,
                CheckinPlan.end_mode == 0,
                CheckinPlan.end_date < today,
            )
            .values(status=0)
        )
        await self.db.commit()
        affected = result.rowcount or 0
        if affected > 0:
            logger.info(f"自动关闭 {affected} 个已过期计划（end_date < {today}）")
        return affected
