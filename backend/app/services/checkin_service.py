from datetime import datetime, date, time as dt_time, timedelta
from typing import Optional

from sqlalchemy import select, and_
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
        - 查询用户当天的打卡记录（仅查 CheckinRecord）
        - 打卡记录与提醒时间的匹配规则（与首页 index.vue 一致）：
          - 按相邻提醒的中点划分匹配区间，覆盖全天 0:00-24:00 无间隙、无留白
          - 单条提醒时间：匹配区间为 [0:00, 24:00]（全天）
          - 多条提醒时间：第一个 [0:00, midpoint]；中间 [midpoint, midpoint]；最后一个 [midpoint, 24:00]
          - 在匹配区间内有打卡记录即视为已打卡
        - 同一提醒时间多次打卡：合并为一行展示，返回首次/末次打卡时间及打卡次数
        - 打卡记录必须依附于提醒时间显示，无对应提醒时间的记录不展示
        - 返回格式：[{ plan_name, plan_remark, notification_time, checked,
                      first_actual_time, last_actual_time, checkin_count }]
        """
        day_start = datetime.combine(day_date, dt_time(0, 0, 0))
        day_end = datetime.combine(day_date + timedelta(days=1), dt_time(0, 0, 0))

        # 1. 查询用户当天所有打卡记录
        records_result = await self.db.execute(
            select(CheckinRecord).where(
                and_(
                    CheckinRecord.user_id == user_id,
                    CheckinRecord.actual_time >= day_start,
                    CheckinRecord.actual_time < day_end,
                )
            ).order_by(CheckinRecord.actual_time.asc())
        )
        records = list(records_result.scalars().all())

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
            .order_by(CheckinPlan.priority.asc(), CheckinPlan.created_at.asc())
        )
        plans = plans_result.scalars().all()

        detail: list[dict] = []

        # 3. 当天有效计划：每个提醒时间按"匹配区间"判定是否已打卡
        for plan in plans:
            # 该计划当天所有打卡记录
            plan_records = [r for r in records if r.plan_id == plan.id and r.actual_time is not None]

            times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
            # 计算匹配区间（按相邻中点划分，覆盖全天 0:00-24:00）
            intervals = self._get_match_intervals(times)
            for i, t in enumerate(times):
                interval_start, interval_end = intervals[i]
                # 匹配区间内的打卡记录
                matched = []
                for r in plan_records:
                    r_minutes = r.actual_time.hour * 60 + r.actual_time.minute
                    if r_minutes >= interval_start and r_minutes < interval_end:
                        matched.append(r)

                if matched:
                    # 已按 actual_time 升序查询，首条为首次，末条为末次
                    first = matched[0]
                    last = matched[-1]
                    detail.append({
                        "plan_name": plan.name,
                        "plan_remark": plan.remark or "",
                        "notification_time": t.notification_time.strftime("%H:%M"),
                        "checked": True,
                        "first_actual_time": first.actual_time.isoformat() if first.actual_time else None,
                        "last_actual_time": last.actual_time.isoformat() if last.actual_time else None,
                        "checkin_count": len(matched),
                    })
                else:
                    detail.append({
                        "plan_name": plan.name,
                        "plan_remark": plan.remark or "",
                        "notification_time": t.notification_time.strftime("%H:%M"),
                        "checked": False,
                        "first_actual_time": None,
                        "last_actual_time": None,
                        "checkin_count": 0,
                    })

        # 按提醒时间升序排序
        detail.sort(key=lambda x: x["notification_time"])
        return detail

    @staticmethod
    def _get_match_intervals(times: list) -> list[tuple[int, int]]:
        """
        计算匹配区间（按相邻中点划分，覆盖全天 0:00-24:00，无间隙、无留白）
        - 第一次提醒：[0:00, midpoint(t1, t2)]
        - 中间提醒：[midpoint(t_{i-1}, t_i), midpoint(t_i, t_{i+1})]
        - 最后一次提醒：[midpoint(t_{n-1}, t_n), 24:00]
        """
        intervals: list[tuple[int, int]] = []
        for i in range(len(times)):
            t_min = times[i].notification_time.hour * 60 + times[i].notification_time.minute
            if i == 0:
                start = 0  # 0:00
            else:
                prev_min = times[i - 1].notification_time.hour * 60 + times[i - 1].notification_time.minute
                start = (prev_min + t_min) // 2
            if i == len(times) - 1:
                end = 1440  # 24:00
            else:
                next_min = times[i + 1].notification_time.hour * 60 + times[i + 1].notification_time.minute
                end = (t_min + next_min) // 2
            intervals.append((start, end))
        return intervals
