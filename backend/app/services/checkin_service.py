from datetime import datetime, date, time as dt_time, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.checkin_record import CheckinRecord
from ..models.plan import CheckinPlan, PlanNotificationTime
from ..utils.logger import logger
from ..utils.timezone import today_shanghai

# 末次催办触发后的跨日补打宽限分钟数：
# 末次提醒的匹配区间跨日延伸至「末次催办触发点 + 该宽限」，期间打卡仍归属该次提醒
CROSS_DAY_GRACE_MINUTES: int = 30


class CheckinService:
    """
    打卡记录业务逻辑服务
    --------------------------------------------------------------------------
    - 打卡：写入 checkin_records 表（允许重复打卡）；校验提醒日（含跨日补打窗口）；
      end_mode=1（按次数结束）计划累计达标后自动置 status=0
    - 查询：用户今日打卡记录、某计划今日已打卡时间点、最近一次打卡记录
    - 匹配区间：按相邻提醒的中点划分；末次提醒区间跨日延伸（末次催办+30 分钟，
      且不超过跨日中点），前一日补打窗口让位后首区间起点后移，全天时间轴连续无歧义
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
        - 校验提醒日：打卡日期须为该计划的有效提醒日（日期范围+星期），
          或处于前一日末次提醒的跨日补打窗口内（仅限该末次时间点）
        - 允许重复打卡（同一时间点可多次打卡）
        - end_mode=1：累计打卡（按 时间点+日期 去重）达标后自动将计划置为已结束
        """
        # 校验计划归属（含提醒时间点，供提醒日校验与达标计数使用）
        plan_result = await self.db.execute(
            select(CheckinPlan)
            .where(CheckinPlan.id == plan_id)
            .options(selectinload(CheckinPlan.notification_times))
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

        # 校验提醒日：当日有效（区间覆盖全天，任意时刻可打卡）；
        # 当日非提醒日时，仅允许处于前一日末次提醒跨日补打窗口内、且打卡对象为该末次时间点
        record_date = actual_time.date()
        if not self._is_plan_on_date(plan, record_date):
            prev_date = record_date - timedelta(days=1)
            allowed = False
            if self._is_plan_on_date(plan, prev_date):
                times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
                if times:
                    last = times[-1]
                    ext_end = self._last_reminder_ext_end_minutes(plan, prev_date, times)
                    ext_end_dt = datetime.combine(prev_date, dt_time(0, 0, 0)) + timedelta(
                        minutes=ext_end
                    )
                    if plan_time_id == last.id and actual_time < ext_end_dt:
                        allowed = True
            if not allowed:
                raise ValueError("今日非该计划提醒日，无法打卡")

        record = CheckinRecord(
            user_id=user_id,
            plan_id=plan_id,
            plan_time_id=plan_time_id,
            actual_time=actual_time,
        )
        self.db.add(record)
        try:
            await self.db.flush()
            # end_mode=1（按打卡总次数结束）：flush 后本条记录已在事务内可见，计数含本次打卡；
            # 累计口径按「不同（提醒时间点+打卡日期）」去重，同一时间点重复打卡只计 1 次
            if plan.end_mode == 1 and plan.total_target_count:
                count_result = await self.db.execute(
                    select(CheckinRecord.plan_time_id, CheckinRecord.actual_time).where(
                        CheckinRecord.user_id == user_id,
                        CheckinRecord.plan_id == plan_id,
                    )
                )
                distinct_doses = {(row[0], row[1].date()) for row in count_result.all()}
                if len(distinct_doses) >= plan.total_target_count:
                    plan.status = 0
                    logger.info(
                        f"计划 {plan_id} 累计打卡 {len(distinct_doses)} 次达到目标 "
                        f"{plan.total_target_count}，已自动置为已结束"
                    )
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

    async def get_latest_checkin(self, user_id: int, plan_id: int) -> CheckinRecord | None:
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
        查询用户某天的打卡详情（含计划提醒时间与跨日补打记录）
        - 当日计划行：仅展示查看日期为有效提醒日（日期范围+星期，不限 status）的计划，
          每个提醒时间按匹配区间判定是否已打卡；末次提醒区间跨日延伸，
          次日凌晨的补打记录会使查看日末次提醒行显示为已打卡
        - 跨天记录行（is_cross_day=true）：查看日凌晨的打卡归属前一日末次提醒，
          即便前一日计划在查看日已非提醒日（如仅工作日计划周六凌晨补打），也展示该记录
        - 同一提醒时间多次打卡：合并为一行展示，返回首次/末次打卡时间及打卡次数
        - 打卡记录必须依附于提醒时间显示，无对应提醒时间的记录不展示
        - 返回格式：[{ plan_name, plan_remark, notification_time, checked,
                      first_actual_time, last_actual_time, checkin_count, is_cross_day }]
        """
        day_start = datetime.combine(day_date, dt_time(0, 0, 0))
        prev_date = day_date - timedelta(days=1)

        # 1. 查询当日与前一日有效提醒日的计划（日期范围过滤后按星期位掩码筛选，不限 status）
        # 当日计划产生主明细行；前一日计划用于跨天补打记录块与当日首区间起点计算
        plans_result = await self.db.execute(
            select(CheckinPlan)
            .where(
                and_(
                    CheckinPlan.user_id == user_id,
                    CheckinPlan.start_date <= day_date,
                    CheckinPlan.end_date >= prev_date,
                )
            )
            .options(selectinload(CheckinPlan.notification_times))
            .order_by(CheckinPlan.priority.asc(), CheckinPlan.created_at.asc())
        )
        all_plans = list(plans_result.scalars().all())
        today_plans = [p for p in all_plans if self._is_plan_on_date(p, day_date)]
        prev_plans = [p for p in all_plans if self._is_plan_on_date(p, prev_date)]

        # 2. 计算打卡记录查询窗口：当日 0 点 ~ 次日最大跨日延伸结束
        # （末次提醒区间可延伸至次日，查看当日明细须能看到次日凌晨的补打记录）
        max_end_min = 1440
        for plan in today_plans:
            times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
            if times:
                max_end_min = max(
                    max_end_min, self._last_reminder_ext_end_minutes(plan, day_date, times)
                )
        records_end = day_start + timedelta(minutes=max_end_min)

        # 3. 查询该窗口内的所有打卡记录（含次日凌晨补打部分）
        records_result = await self.db.execute(
            select(CheckinRecord).where(
                and_(
                    CheckinRecord.user_id == user_id,
                    CheckinRecord.actual_time >= day_start,
                    CheckinRecord.actual_time < records_end,
                )
            ).order_by(CheckinRecord.actual_time.asc())
        )
        records = list(records_result.scalars().all())

        def record_minutes(r: CheckinRecord) -> int:
            """记录时刻相对当日 0 点的分钟数（次日凌晨部分 >1440）"""
            return int((r.actual_time - day_start).total_seconds() // 60)

        cross_rows: list[dict] = []
        normal_rows: list[dict] = []

        # 4. 当日计划行：匹配区间判定已打卡（区间含跨日延伸段）
        for plan in today_plans:
            plan_records = [r for r in records if r.plan_id == plan.id and r.actual_time is not None]
            times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
            if not times:
                continue
            windows = self.compute_day_windows(plan, day_date, times)
            for i, t in enumerate(times):
                start_min, end_min = windows["intervals"][i]
                matched = [
                    r for r in plan_records if start_min <= record_minutes(r) < end_min
                ]
                row = {
                    "plan_name": plan.name,
                    "plan_remark": plan.remark or "",
                    "notification_time": t.notification_time.strftime("%H:%M"),
                    "checked": bool(matched),
                    "first_actual_time": matched[0].actual_time.isoformat() if matched else None,
                    "last_actual_time": matched[-1].actual_time.isoformat() if matched else None,
                    "checkin_count": len(matched),
                    "is_cross_day": False,
                }
                normal_rows.append(row)

        # 5. 跨天记录行：前一日有效计划的末次提醒，匹配查看日凌晨 [0, 前日延伸结束) 的记录
        for plan in prev_plans:
            times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
            if not times:
                continue
            last = times[-1]
            prev_ext_end = self._last_reminder_ext_end_minutes(plan, prev_date, times)
            prev_ext_today = prev_ext_end - 1440  # 前日补打窗口在查看日的结束分钟
            if prev_ext_today <= 0:
                continue
            matched = [
                r for r in records if r.plan_id == plan.id and record_minutes(r) < prev_ext_today
            ]
            if not matched:
                continue
            cross_rows.append({
                "plan_name": plan.name,
                "plan_remark": plan.remark or "",
                "notification_time": last.notification_time.strftime("%H:%M"),
                "checked": True,
                "first_actual_time": matched[0].actual_time.isoformat(),
                "last_actual_time": matched[-1].actual_time.isoformat(),
                "checkin_count": len(matched),
                "is_cross_day": True,
            })

        # 跨天行（按实际打卡时间升序）在前，当日行（按提醒时间升序）在后
        normal_rows.sort(key=lambda x: x["notification_time"])
        return cross_rows + normal_rows

    # ==================== 匹配区间计算（调度器/站内信已读判定复用） ====================

    @staticmethod
    def _is_plan_on_date(plan: CheckinPlan, day_date: date) -> bool:
        """计划在某日是否为有效提醒日（日期范围内 + 重复星期位掩码命中）"""
        if plan.start_date > day_date or plan.end_date < day_date:
            return False
        weekdays = plan.repeat_weekdays if plan.repeat_weekdays is not None else 127
        return bool(weekdays & (1 << day_date.weekday()))

    @staticmethod
    def _last_followup_offset_minutes(plan_time: PlanNotificationTime) -> int:
        """
        某提醒时间点末次催办相对提醒时间的偏移分钟
        - count=3（默认三段式）：档位2对末次提醒固定 +60 分钟
        - count=2（自定义等间隔）：末次（第2次）提醒为 +间隔分钟
        - count=1（仅准时）：无催办，偏移 0
        """
        count = plan_time.followup_count if plan_time.followup_count is not None else 3
        if count == 3:
            return 60
        if count == 2:
            return plan_time.followup_interval_min or 10
        return 0

    @staticmethod
    def _last_reminder_ext_end_minutes(
        plan: CheckinPlan, day_date: date, times: list[PlanNotificationTime]
    ) -> int:
        """
        某日末次提醒匹配区间的结束分钟（相对当日 0 点，恒 >= 1440）
        - 跨日延伸终点 = min(跨日中点, 末次催办触发点 + 30 分钟宽限)
          跨日中点 = 昨日末次提醒与次日首提醒的中点（次日非提醒日时无中点，直接取催办+30）
        - 恒不小于 1440：跨日延伸只延长、不缩短当日区间（当日部分始终覆盖至 24:00，
          与升级前的全天无留白行为一致）
        """
        if not times:
            return 1440
        last = times[-1]
        m = last.notification_time.hour * 60 + last.notification_time.minute
        followup_end = (
            m + CheckinService._last_followup_offset_minutes(last) + CROSS_DAY_GRACE_MINUTES
        )
        next_day = day_date + timedelta(days=1)
        if CheckinService._is_plan_on_date(plan, next_day):
            first = times[0]
            next_first = first.notification_time.hour * 60 + first.notification_time.minute
            cross_mid = (m + next_first + 1440) // 2
            end = min(cross_mid, followup_end)
        else:
            end = followup_end
        return max(1440, end)

    @staticmethod
    def compute_day_windows(
        plan: CheckinPlan, day_date: date, times: list[PlanNotificationTime]
    ) -> dict:
        """
        计算某计划某日的完整匹配窗口
        - intervals：各提醒时间的匹配区间 [(start, end)]（分钟，末次 end 可 >1440 跨日延伸）
          - 首条：[前一日补打窗口在本日的结束点, midpoint(t1, t2)]（无延伸时起点为 0）
          - 中间：[midpoint(t_{i-1}, t_i), midpoint(t_i, t_{i+1})]
          - 末条：[midpoint(t_{n-1}, t_n), 跨日延伸终点]
        - prev_ext_end：前一日末次提醒补打窗口在本日的结束分钟（0=前一日无延伸）
        """
        prev_ext_end = 0
        if CheckinService._is_plan_on_date(plan, day_date - timedelta(days=1)):
            prev_ext = CheckinService._last_reminder_ext_end_minutes(
                plan, day_date - timedelta(days=1), times
            )
            prev_ext_end = max(0, prev_ext - 1440)

        intervals: list[tuple[int, int]] = []
        n = len(times)
        for i, t in enumerate(times):
            m = t.notification_time.hour * 60 + t.notification_time.minute
            if i == 0:
                start = prev_ext_end  # 口径C：首区间起点让位于前一日补打窗口，保证时间轴连续
            else:
                prev_m = times[i - 1].notification_time.hour * 60 + times[i - 1].notification_time.minute
                start = (prev_m + m) // 2
            if i < n - 1:
                next_m = times[i + 1].notification_time.hour * 60 + times[i + 1].notification_time.minute
                end = (m + next_m) // 2
            else:
                end = CheckinService._last_reminder_ext_end_minutes(plan, day_date, times)
            intervals.append((start, end))
        return {"intervals": intervals, "prev_ext_end": prev_ext_end}
