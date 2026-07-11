from datetime import time

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.plan import (
    CheckinPlan,
    PlanNotificationChannel,
    PlanNotificationTime,
)
from ..models.notification_channel import NotificationChannel
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
        from sqlalchemy import case
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
        notification_times: list[str],
        channel_ids: list[int],
        status: int = 1,
        priority: int = 3,
    ) -> CheckinPlan:
        """
        创建计划
        - 同时写入主表、时间点表、渠道关联表
        - 校验 channel_ids 均属于该用户
        - status：1-进行中，2-暂停，0-已结束
        - priority：0-7，数字越小优先级越高
        """
        # 1. 校验通知渠道归属
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

        # 2. 创建计划主记录
        plan = CheckinPlan(
            user_id=user_id,
            name=name,
            remark=remark or None,
            start_date=start_date,
            end_date=end_date,
            status=status,
            priority=priority,
        )
        self.db.add(plan)
        await self.db.flush()

        # 3. 写入通知时间点
        for t in notification_times:
            # 兼容 HH:MM 和 HH:MM:SS 格式
            parts = t.split(":")
            if len(parts) == 2:
                h, m = int(parts[0]), int(parts[1])
                t_obj = time(hour=h, minute=m, second=0)
            else:
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                t_obj = time(hour=h, minute=m, second=s)
            self.db.add(PlanNotificationTime(
                plan_id=plan.id,
                notification_time=t_obj,
            ))

        # 4. 写入计划-渠道关联
        for cid in channel_ids:
            self.db.add(PlanNotificationChannel(
                plan_id=plan.id,
                channel_id=cid,
            ))

        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def delete_plan(self, plan_id: int, user_id: int) -> None:
        """删除计划（同时删除关联的时间点和渠道关联）"""
        plan = await self.get_by_id(plan_id)
        if not plan:
            raise ValueError("计划不存在")
        if plan.user_id != user_id:
            raise ValueError("无权操作该计划")

        # 删除关联的时间点
        await self.db.execute(
            delete(PlanNotificationTime).where(PlanNotificationTime.plan_id == plan_id)
        )
        # 删除关联的渠道
        await self.db.execute(
            delete(PlanNotificationChannel).where(PlanNotificationChannel.plan_id == plan_id)
        )
        # 删除主记录
        await self.db.delete(plan)
        await self.db.commit()

    async def update_plan(
        self,
        plan_id: int,
        user_id: int,
        name: str,
        remark: str,
        start_date,
        end_date,
        notification_times: list[str],
        channel_ids: list[int],
        status: int = 1,
        priority: int = 3,
    ) -> CheckinPlan:
        """
        更新计划
        - 更新主表字段（name/remark/start_date/end_date/status/priority）
        - 删除旧的时间点和渠道关联，写入新的
        - 校验 channel_ids 均属于该用户
        """
        plan = await self.get_by_id(plan_id)
        if not plan:
            raise ValueError("计划不存在")
        if plan.user_id != user_id:
            raise ValueError("无权操作该计划")

        # 校验通知渠道归属
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

        # 更新主记录
        plan.name = name
        plan.remark = remark or None
        plan.start_date = start_date
        plan.end_date = end_date
        plan.status = status
        plan.priority = priority

        # 删除旧的时间点，写入新的
        await self.db.execute(
            delete(PlanNotificationTime).where(PlanNotificationTime.plan_id == plan_id)
        )
        for t in notification_times:
            parts = t.split(":")
            if len(parts) == 2:
                h, m = int(parts[0]), int(parts[1])
                t_obj = time(hour=h, minute=m, second=0)
            else:
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                t_obj = time(hour=h, minute=m, second=s)
            self.db.add(PlanNotificationTime(
                plan_id=plan.id,
                notification_time=t_obj,
            ))

        # 删除旧的渠道关联，写入新的
        await self.db.execute(
            delete(PlanNotificationChannel).where(PlanNotificationChannel.plan_id == plan_id)
        )
        for cid in channel_ids:
            self.db.add(PlanNotificationChannel(
                plan_id=plan.id,
                channel_id=cid,
            ))

        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def auto_close_expired_plans(self) -> int:
        """
        自动关闭已过期的计划
        - 查询所有 status=1（进行中）且 end_date < today 的计划
        - 将其 status 更新为 0（已结束）
        - 返回受影响的行数
        """
        today = today_shanghai()
        result = await self.db.execute(
            update(CheckinPlan)
            .where(
                CheckinPlan.status == 1,
                CheckinPlan.end_date < today,
            )
            .values(status=0)
        )
        await self.db.commit()
        affected = result.rowcount or 0
        if affected > 0:
            logger.info(f"自动关闭 {affected} 个已过期计划（end_date < {today}）")
        return affected
