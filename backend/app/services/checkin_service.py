from datetime import datetime, date, time as dt_time, timedelta
from typing import Optional

from sqlalchemy import select, and_, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.checkin_record import CheckinRecord
from ..models.plan import CheckinPlan, PlanNotificationTime
from ..utils.timezone import today_shanghai


class CheckinService:
    """
    打卡记录业务逻辑服务
    --------------------------------------------------------------------------
    - 打卡：写入 checkin_records 表（允许重复打卡）
    - 查询：用户今日打卡记录、某计划今日已打卡时间点、最近一次打卡记录
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_checkin(
        self,
        user_id: int,
        plan_id: int,
        plan_time_id: int,
        actual_time: datetime,
    ) -> CheckinRecord:
        """
        创建打卡记录
        - 校验计划存在且属于该用户
        - 校验时间点存在且属于该计划
        - 允许重复打卡（同一时间点可多次打卡）
        """
        # 校验计划归属
        plan_result = await self.db.execute(
            select(CheckinPlan).where(CheckinPlan.id == plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if not plan:
            raise ValueError("计划不存在")
        if plan.user_id != user_id:
            raise ValueError("无权操作该计划")

        # 校验时间点归属
        time_result = await self.db.execute(
            select(PlanNotificationTime).where(PlanNotificationTime.id == plan_time_id)
        )
        plan_time = time_result.scalar_one_or_none()
        if not plan_time:
            raise ValueError("通知时间点不存在")
        if plan_time.plan_id != plan_id:
            raise ValueError("通知时间点不属于该计划")

        record = CheckinRecord(
            user_id=user_id,
            plan_id=plan_id,
            plan_time_id=plan_time_id,
            actual_time=actual_time,
        )
        self.db.add(record)
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"打卡失败：{e}") from e
        await self.db.refresh(record)
        return record

    async def list_today_by_user(self, user_id: int) -> list[CheckinRecord]:
        """查询用户今日所有打卡记录（使用日期范围比较避免 DATE() 函数时区问题）"""
        today = today_shanghai()
        day_start = datetime.combine(today, dt_time(0, 0, 0))
        day_end = datetime.combine(today + timedelta(days=1), dt_time(0, 0, 0))
        result = await self.db.execute(
            select(CheckinRecord).where(
                and_(
                    CheckinRecord.user_id == user_id,
                    CheckinRecord.actual_time >= day_start,
                    CheckinRecord.actual_time < day_end,
                )
            )
        )
        return list(result.scalars().all())

    async def list_today_by_plan(self, user_id: int, plan_id: int) -> list[CheckinRecord]:
        """查询用户今日某计划的打卡记录（用于判断哪些时间点已打卡）"""
        today = today_shanghai()
        day_start = datetime.combine(today, dt_time(0, 0, 0))
        day_end = datetime.combine(today + timedelta(days=1), dt_time(0, 0, 0))
        result = await self.db.execute(
            select(CheckinRecord).where(
                and_(
                    CheckinRecord.user_id == user_id,
                    CheckinRecord.plan_id == plan_id,
                    CheckinRecord.actual_time >= day_start,
                    CheckinRecord.actual_time < day_end,
                )
            ).order_by(CheckinRecord.actual_time.asc())
        )
        return list(result.scalars().all())

    async def get_latest_checkin(self, user_id: int, plan_id: int) -> Optional[CheckinRecord]:
        """查询用户某计划的最近一次打卡记录（用于多提醒时间间隔判断）"""
        result = await self.db.execute(
            select(CheckinRecord).where(
                and_(
                    CheckinRecord.user_id == user_id,
                    CheckinRecord.plan_id == plan_id,
                )
            ).order_by(CheckinRecord.actual_time.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_month(self, user_id: int, year: int, month: int) -> list[int]:
        """
        查询用户某月所有打卡记录的日期列表
        - 使用日期范围比较（避免 extract 函数的时区/兼容问题）
        - 返回当月有打卡记录的日期（day of month）列表
        - 用于日历小绿点标识
        """
        # 构建当月起止时间（用于范围查询）
        first_day = datetime(year, month, 1)
        if month == 12:
            next_month_first = datetime(year + 1, 1, 1)
        else:
            next_month_first = datetime(year, month + 1, 1)

        result = await self.db.execute(
            select(CheckinRecord.actual_time).where(
                and_(
                    CheckinRecord.user_id == user_id,
                    CheckinRecord.actual_time >= first_day,
                    CheckinRecord.actual_time < next_month_first,
                )
            )
        )
        # 在 Python 中提取 day（避免 SQL DAY() 函数的时区问题）
        days = set()
        for row in result.all():
            dt = row[0]
            if dt:
                days.add(dt.day)
        return sorted(days)

    async def list_day_detail(self, user_id: int, day_date: date) -> list[dict]:
        """
        查询用户某天的打卡详情（含计划提醒时间）
        - 查询当天有效的所有计划（start_date <= day_date <= end_date，不限制 status）
          确保已结束但当天有效的计划也会显示
        - 查询用户当天的打卡记录
        - 打卡记录与提醒时间的匹配规则（与首页 index.vue 的 isTimeChecked 一致）：
          - 单条提醒时间：当日有任意一条该计划的打卡记录即视为已打卡
          - 多条提醒时间：在提醒时间的前后各1小时 [t-60, t+60] 内存在打卡记录即视为已打卡
        - 同一提醒时间多次打卡：每条记录单独占一行，确保所有记录完整展示
        - 返回格式：[{ plan_id, plan_name, plan_remark, notification_time, checked, actual_time }]
        """
        day_start = datetime.combine(day_date, dt_time(0, 0, 0))
        day_end = datetime.combine(day_date + timedelta(days=1), dt_time(0, 0, 0))

        # 1. 查询用户当天所有打卡记录（outerjoin 计划与提醒时间，保留已删除的孤儿记录）
        records_result = await self.db.execute(
            select(CheckinRecord, CheckinPlan, PlanNotificationTime)
            .outerjoin(CheckinPlan, CheckinRecord.plan_id == CheckinPlan.id)
            .outerjoin(PlanNotificationTime, CheckinRecord.plan_time_id == PlanNotificationTime.id)
            .where(
                and_(
                    CheckinRecord.user_id == user_id,
                    CheckinRecord.actual_time >= day_start,
                    CheckinRecord.actual_time < day_end,
                )
            )
            .order_by(CheckinRecord.actual_time.asc())
        )
        records = records_result.all()

        # 2. 查询当天有效的所有计划（按日期范围过滤，不限制 status）
        # 这样即使计划后来被定时任务标记为已结束，只要当天在计划范围内，就会显示
        plans_result = await self.db.execute(
            select(CheckinPlan)
            .where(
                and_(
                    CheckinPlan.user_id == user_id,
                    CheckinPlan.start_date <= day_date,
                    CheckinPlan.end_date >= day_date,
                )
            )
            .options(selectinload(CheckinPlan.notification_times))
            .order_by(CheckinPlan.priority.asc(), CheckinPlan.created_at.desc())
        )
        plans = plans_result.scalars().all()
        valid_plan_ids = {p.id for p in plans}

        detail: list[dict] = []
        # 已被时间区间匹配的打卡记录 id（用于后续识别未匹配的偏离记录）
        matched_record_ids: set[int] = set()

        # 3a. 当天有效计划：每个提醒时间按"时间区间匹配"判定是否已打卡
        for plan in plans:
            # 该计划当天所有打卡记录（含 actual_time 转分钟数）
            plan_records = []
            for record, p, _pt in records:
                if p is not None and p.id == plan.id and record.actual_time is not None:
                    r_minutes = record.actual_time.hour * 60 + record.actual_time.minute
                    plan_records.append((record, r_minutes))

            times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
            for t in times:
                t_minutes = t.notification_time.hour * 60 + t.notification_time.minute
                # 时间区间匹配（与 index.vue isTimeChecked 规则一致）
                if len(times) == 1:
                    # 单条提醒时间：当日有任意记录即视为已打卡
                    matched = plan_records
                else:
                    # 多条提醒时间：[t-60, t+60] 区间内存在记录
                    lo = t_minutes - 60
                    hi = t_minutes + 60
                    matched = [(r, m) for (r, m) in plan_records if m >= lo and m <= hi]

                if matched:
                    # 每条匹配记录单独占一行，确保多次打卡完整展示
                    for r, _m in matched:
                        matched_record_ids.add(r.id)
                        detail.append({
                            "plan_id": plan.id,
                            "plan_name": plan.name,
                            "plan_remark": plan.remark or "",
                            "notification_time": t.notification_time.strftime("%H:%M"),
                            "checked": True,
                            "actual_time": r.actual_time.isoformat() if r.actual_time else None,
                        })
                else:
                    detail.append({
                        "plan_id": plan.id,
                        "plan_name": plan.name,
                        "plan_remark": plan.remark or "",
                        "notification_time": t.notification_time.strftime("%H:%M"),
                        "checked": False,
                        "actual_time": None,
                    })

        # 3b. 孤儿记录：计划已删除 / 不在当天有效计划中 / 偏离所有提醒区间，单独展示
        for record, plan, plan_time in records:
            # 跳过已被时间区间匹配的记录
            if record.id in matched_record_ids:
                continue
            detail.append({
                "plan_id": plan.id if plan else record.plan_id,
                "plan_name": plan.name if plan else "(已删除计划)",
                "plan_remark": (plan.remark or "") if plan else "",
                "notification_time": plan_time.notification_time.strftime("%H:%M") if plan_time else "",
                "checked": True,
                "actual_time": record.actual_time.isoformat() if record.actual_time else None,
            })

        # 按提醒时间排序，同一提醒时间已打卡在前
        detail.sort(key=lambda x: (x["notification_time"], 0 if x["checked"] else 1))
        return detail
