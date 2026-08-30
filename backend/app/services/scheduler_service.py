"""
定时任务调度服务（定时计划类）
--------------------------------------------------------------------------
集中管理所有后台定时任务循环，main.py 启动时调用 start_all() 拉起全部任务。
其他业务类（User/Email/PlanService 等）如需定时触发能力，由本服务统一调度。

当前包含四类后台任务：
1. 账号清理循环（每 30 秒）：清理 status=0 且超时的删除计划账号
2. 计划自动关闭循环（每 30 分钟）：将 end_date<today 的按日期结束计划置为已结束
3. 定时通知派发循环（每 60 秒）：根据打卡计划提醒时间发送站内信/邮件/微信/App推送通知
4. 生物识别凭证清理循环（每 30 分钟）：删除已过期的 user_biometric_tokens 记录

通知派发逻辑（批量预取 + 分钟水位回放架构）：
- 分钟水位：进程内记录上一次已处理的分钟；稳态每轮只处理新增的 1 分钟，
  进程重启/宕机恢复后回放近 REPLAY_WINDOW_MINUTES 分钟，漏掉的通知自动补发
  （防重键天然挡住已发过的），超过回放窗口的仍丢失，避免恢复后狂发陈旧通知
- 批量预取：计划/打卡记录/防重日志/渠道四类数据各一次查询取回，内存匹配，
  消除逐时间点/逐渠道查询的 N+1（查询次数与窗口内分钟数无关）
- 计划按重复星期位掩码过滤：非重复日（repeat_weekdays 位未命中）的计划整日跳过
- 提醒次数（followup_count）驱动的触发模式：
  - 3（默认三段式，行为与历史版本一致）：
    准时（trigger_type=0）→ 超10分钟催办（trigger_type=1）→
    「1小时 与 下一次提醒中点 择先」催办（trigger_type=2，末次提醒固定 +1 小时）
  - 2（自定义等间隔）：准时（0）→ 提醒时间+间隔分钟（1）
  - 1（仅准时）：仅 trigger_type=0
- 已打卡判停：匹配区间复用 CheckinService.compute_day_windows（末次提醒区间
  跨日延伸至「末次催办+30 分钟」），次日凌晨补打会拦停跨天催办
- 防重：以 (plan_time_id, trigger_type, notify_date, channel_id) 为去重键
- 站内信：直接写 notification_logs（status=2 未读）
- 邮件：读取用户 notification_channels.channel_value 作为 SMTP 发送，收件人取 users.email
- 微信：一次性订阅额度制（granted-sent>0 才发，成功 sent+1）
- App 推送：读取 channel_value 内的设备 token 数组，逐个走友盟+ U-Push 下发，
  失败计数满 3 次剔除该设备，数组清空则删除整行渠道；按渠道只记 1 条日志
"""
import asyncio
import json
from collections import defaultdict
from datetime import datetime, date, time as dt_time, timedelta

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import AsyncSessionLocal
from ..models.plan import CheckinPlan, PlanNotificationTime, PlanNotificationChannel
from ..models.notification_channel import NotificationChannel
from ..models.notification_log import NotificationLog
from ..models.checkin_record import CheckinRecord
from ..models.user import User as UserModel
from ..schemas.notification_channel import (
    CHANNEL_TYPE_ZNX,
    CHANNEL_TYPE_EMAIL,
    CHANNEL_TYPE_WECHAT,
    CHANNEL_TYPE_APP_PUSH,
    APP_PUSH_MAX_FAIL_COUNT,
)
from ..schemas.notification_log import (
    LOG_STATUS_SUCCESS,
    LOG_STATUS_FAILED,
    LOG_STATUS_UNREAD,
    TRIGGER_ON_TIME,
    TRIGGER_OFFSET_10MIN,
    TRIGGER_OFFSET_1HOUR_OR_MIDPOINT,
    FOLLOWUP_OFFSET_10MIN,
    TRIGGER_DESC,
)
from ..core.config import settings
from ..models.user_miniapp_account import UserMiniappAccount
from ..services.wechat_service import WeChatService, ERRCODE_NO_PERMISSION
from ..services.umeng_service import UmengService, UmengPushError
from ..utils.timezone import now_shanghai
from ..utils.crypto import decrypt
from ..utils.logger import logger
from .checkin_service import CheckinService
from .email_service import Email
from .user_service import User
from .plan_service import PlanService
from .notification_channel_service import NotificationChannelService


# 后台循环间隔（秒）
INTERVAL_PURGE: int = 30        # 账号清理：每 30 秒
INTERVAL_PLAN_CLOSE: int = 1800  # 计划关闭：每 30 分钟
INTERVAL_NOTIFICATION: int = 60   # 通知派发：每 60 秒
INTERVAL_BIOMETRIC_PURGE: int = 1800  # 生物识别凭证清理：每 30 分钟

# 通知派发回放窗口（分钟）：进程重启/宕机恢复后向前回放的分钟数（含当前分钟），
# 窗口内的漏发通知自动补发（防重键挡住已发条目），超出窗口的不再补发
REPLAY_WINDOW_MINUTES: int = 5

# 进程级分钟水位：上一次已处理的分钟（秒/微秒归零）；None 表示进程尚未处理过任何分钟。
# 派发器每分钟被重新实例化，水位须挂在模块级跨实例存活
_last_processed_minute: datetime | None = None


class SchedulerService:
    """定时任务调度服务，统一管理所有后台循环任务"""

    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []

    async def start_all(self) -> None:
        """启动全部后台循环任务（由 main.py lifespan 调用）"""
        self._tasks = [
            asyncio.create_task(self._loop_purge_deletions()),
            asyncio.create_task(self._loop_close_expired_plans()),
            asyncio.create_task(self._loop_dispatch_notifications()),
            asyncio.create_task(self._loop_purge_expired_biometric_tokens()),
        ]
        logger.info("定时任务调度服务已启动：账号清理/计划关闭/通知派发/生物识别凭证清理")

    async def stop_all(self) -> None:
        """停止全部后台循环任务（由 main.py lifespan 调用）"""
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass
        self._tasks = []

    # ==================== 后台循环 ====================

    async def _loop_purge_deletions(self) -> None:
        """循环：定期清理到期删除账号（委托 User 服务）"""
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    count = await User(session).purge_expired_deletions()
                    if count > 0:
                        logger.info(f"已清理 {count} 个到期删除账号")
            except Exception:
                logger.exception("清理到期删除账号任务异常")
            await asyncio.sleep(INTERVAL_PURGE)

    async def _loop_close_expired_plans(self) -> None:
        """循环：定期自动关闭过期计划（委托 PlanService）"""
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    await PlanService(session).auto_close_expired_plans()
            except Exception:
                logger.exception("自动关闭过期计划任务异常")
            await asyncio.sleep(INTERVAL_PLAN_CLOSE)

    async def _loop_dispatch_notifications(self) -> None:
        """循环：每分钟派发定时通知"""
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    dispatcher = NotificationDispatcher(session)
                    await dispatcher.dispatch_for_now()
            except Exception:
                logger.exception("定时通知派发任务异常")
            await asyncio.sleep(INTERVAL_NOTIFICATION)

    async def _loop_purge_expired_biometric_tokens(self) -> None:
        """循环：定期清理已过期的生物识别登录凭证（委托 User 服务）"""
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    count = await User(session).purge_expired_biometric_tokens()
                    if count > 0:
                        logger.info(f"已清理 {count} 条过期生物识别凭证")
            except Exception:
                logger.exception("清理过期生物识别凭证任务异常")
            await asyncio.sleep(INTERVAL_BIOMETRIC_PURGE)


def _trigger_desc(plan_time: PlanNotificationTime, trigger_type: int) -> str:
    """
    触发类型中文描述
    - 默认三段式（followup_count=3）走 TRIGGER_DESC 常量表（准时/超10分钟/1小时或中点）
    - 自定义等间隔（count=1/2）动态生成「第N次提醒（+X分钟）」
    """
    count = plan_time.followup_count if plan_time.followup_count is not None else 3
    if count == 3:
        return TRIGGER_DESC.get(trigger_type, "提醒")
    if trigger_type == 0:
        return "准时提醒"
    interval = plan_time.followup_interval_min or 10
    return f"第{trigger_type + 1}次提醒（+{interval * trigger_type}分钟）"


class NotificationDispatcher:
    """
    通知派发器（由 SchedulerService 每分钟实例化调用）
    --------------------------------------------------------------------------
    将派发逻辑独立成类，避免 SchedulerService 承载过多职责。

    架构：分钟水位 + 批量预取 + 内存匹配
    - dispatch_for_now 计算本轮需处理的分钟序列（稳态 1 分钟；重启回放近 5 分钟），
      一次批量预取计划/打卡记录/防重日志/渠道后，逐分钟在内存中匹配触发点
    - 每个提醒时间点的触发点由 followup_count 驱动（详见模块 docstring）
    - 已打卡判停使用 CheckinService.compute_day_windows 的匹配区间（含跨日延伸），
      区间内已有打卡记录则该时间点当日全部触发跳过
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch_for_now(self) -> int:
        """
        派发当前时刻应触发的所有通知（准时 + 催办，支持回放补发）
        返回成功派发的通知数（不含被去重/已打卡跳过的）
        """
        global _last_processed_minute
        now = now_shanghai()
        current_minute = now.replace(second=0, microsecond=0)
        if _last_processed_minute is None:
            # 进程启动：回放近 REPLAY_WINDOW_MINUTES 分钟（含当前分钟）
            start = current_minute - timedelta(minutes=REPLAY_WINDOW_MINUTES - 1)
        else:
            start = _last_processed_minute + timedelta(minutes=1)
            if start > current_minute:
                # 上一轮已处理到当前分钟（循环间隔漂移导致同分钟内二次进入）：无新增分钟
                return 0
            if (current_minute - start).total_seconds() / 60 > REPLAY_WINDOW_MINUTES:
                # 水位距今跨度异常（如进程被冻结）：重置为回放窗口，避免狂发陈旧通知
                start = current_minute - timedelta(minutes=REPLAY_WINDOW_MINUTES - 1)
        _last_processed_minute = current_minute

        minutes: list[datetime] = []
        cursor = start
        while cursor <= current_minute:
            minutes.append(cursor)
            cursor += timedelta(minutes=1)
        return await self._dispatch_batch(minutes)

    # ==================== 批量派发核心 ====================

    async def _dispatch_batch(self, minutes: list[datetime]) -> int:
        """批量派发多个分钟应触发的通知：一次预取全部数据，逐分钟内存匹配"""
        # 涉及的提醒归属日期：各分钟日期 + 各分钟日期的前一日（跨天催办归属提醒所在日）
        dates: set[date] = set()
        for m in minutes:
            dates.add(m.date())
            dates.add(m.date() - timedelta(days=1))

        # 1. 预取有效计划（status=1 且日期范围覆盖任一涉及日期；星期过滤在内存进行）
        date_filters = [
            and_(CheckinPlan.start_date <= d, CheckinPlan.end_date >= d) for d in dates
        ]
        plan_result = await self.db.execute(
            select(CheckinPlan)
            .where(CheckinPlan.status == 1, or_(*date_filters))
            .options(selectinload(CheckinPlan.notification_times))
        )
        plans = [p for p in plan_result.scalars().all() if p.notification_times]
        if not plans:
            return 0

        # 各归属日期下的有效计划（日期范围 + 重复星期位掩码均命中）
        plans_by_date: dict[date, list[CheckinPlan]] = defaultdict(list)
        for plan in plans:
            for d in dates:
                if CheckinService._is_plan_on_date(plan, d):
                    plans_by_date[d].append(plan)

        # 2. 预取各（计划, 归属日）的匹配窗口与打卡记录查询范围
        #    （末次区间跨日延伸，记录窗口须覆盖到最晚归属日的次日延伸结束）
        windows_map: dict[tuple[int, date], dict] = {}
        records_end = datetime.combine(min(dates), dt_time(0, 0, 0))
        for d, d_plans in plans_by_date.items():
            day_start = datetime.combine(d, dt_time(0, 0, 0))
            day_records_end = day_start
            for plan in d_plans:
                times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
                win = CheckinService.compute_day_windows(plan, d, times)
                windows_map[(plan.id, d)] = win
                day_records_end = max(day_records_end, day_start + timedelta(minutes=win["intervals"][-1][1]))
            records_end = max(records_end, day_records_end)
        records_start = datetime.combine(min(dates), dt_time(0, 0, 0))

        plan_ids = [p.id for p in plans]
        # 3. 预取打卡记录（一次查询，内存按区间判定，避免逐时间点查询的 N+1）
        record_result = await self.db.execute(
            select(CheckinRecord).where(
                CheckinRecord.plan_id.in_(plan_ids),
                CheckinRecord.actual_time >= records_start,
                CheckinRecord.actual_time < records_end,
            )
        )
        records_by_plan: dict[int, list[CheckinRecord]] = defaultdict(list)
        for r in record_result.scalars().all():
            records_by_plan[r.plan_id].append(r)

        # 4. 预取防重日志（一次查询取回已发键集合，避免逐渠道查询的 N+1）
        all_pt_ids = [nt.id for p in plans for nt in p.notification_times]
        log_result = await self.db.execute(
            select(
                NotificationLog.plan_time_id,
                NotificationLog.trigger_type,
                NotificationLog.notify_date,
                NotificationLog.channel_id,
            ).where(
                NotificationLog.plan_time_id.in_(all_pt_ids),
                NotificationLog.notify_date.in_(dates),
            )
        )
        sent_keys = {(r[0], r[1], r[2], r[3]) for r in log_result.all()}

        # 5. 预取计划绑定的已启用通知渠道（一次查询，按计划分组）
        channel_result = await self.db.execute(
            select(PlanNotificationChannel.plan_id, NotificationChannel)
            .join(NotificationChannel, PlanNotificationChannel.channel_id == NotificationChannel.id)
            .where(
                PlanNotificationChannel.plan_id.in_(plan_ids),
                NotificationChannel.enabled == True,  # noqa: E712（SQLAlchemy 表达式需用 ==）
            )
        )
        channels_by_plan: dict[int, list[NotificationChannel]] = defaultdict(list)
        for pid, channel in channel_result.all():
            channels_by_plan[pid].append(channel)

        # 6. 逐分钟匹配触发点并派发（分钟升序，保证回放时按时间顺序补发）
        sent = 0
        for m in minutes:
            # 分钟 m 可能命中两类归属日：当日（当日触发）与前一日（跨天触发）
            for d in (m.date() - timedelta(days=1), m.date()):
                minute_off = int((m - datetime.combine(d, dt_time(0, 0, 0))).total_seconds() // 60)
                for plan in plans_by_date.get(d, []):
                    times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
                    win = windows_map[(plan.id, d)]
                    day_start = datetime.combine(d, dt_time(0, 0, 0))
                    plan_records = records_by_plan.get(plan.id, [])
                    channels = channels_by_plan.get(plan.id, [])
                    if not channels:
                        continue
                    for idx, pt in enumerate(times):
                        for trigger_type, trigger_off in self._trigger_points(times, idx):
                            if trigger_off != minute_off:
                                continue
                            # 已打卡判停：匹配区间（含跨日延伸）内已有打卡记录则跳过
                            start_min, end_min = win["intervals"][idx]
                            interval_start = day_start + timedelta(minutes=start_min)
                            interval_end = day_start + timedelta(minutes=end_min)
                            if any(
                                interval_start <= r.actual_time < interval_end
                                for r in plan_records
                            ):
                                continue
                            for channel in channels:
                                if (pt.id, trigger_type, d, channel.id) in sent_keys:
                                    continue
                                await self._send_via_channel(plan, pt, channel, trigger_type, d)
                                sent_keys.add((pt.id, trigger_type, d, channel.id))
                                sent += 1
        return sent

    @staticmethod
    def _trigger_points(times: list[PlanNotificationTime], idx: int) -> list[tuple[int, int]]:
        """
        计算某提醒时间点在归属日的全部触发点 (trigger_type, 相对归属日 0 点的分钟偏移)
        - followup_count=3（默认三段式）：准时 0；+10分钟 1；
          「min(+60, 与下一次提醒中点)」2（末次固定 +60）——与历史版本行为一致
        - followup_count=2（自定义等间隔）：准时 0；提醒时间+间隔分钟 1
        - followup_count=1（仅准时）：仅 0
        """
        pt = times[idx]
        count = pt.followup_count if pt.followup_count is not None else 3
        m = pt.notification_time.hour * 60 + pt.notification_time.minute
        points = [(TRIGGER_ON_TIME, m)]
        if count == 3:
            points.append((TRIGGER_OFFSET_10MIN, m + FOLLOWUP_OFFSET_10MIN))
            if idx < len(times) - 1:
                next_m = (
                    times[idx + 1].notification_time.hour * 60
                    + times[idx + 1].notification_time.minute
                )
                midpoint = (m + next_m) // 2
                points.append((TRIGGER_OFFSET_1HOUR_OR_MIDPOINT, min(m + 60, midpoint)))
            else:
                # 末次提醒：固定 +1 小时
                points.append((TRIGGER_OFFSET_1HOUR_OR_MIDPOINT, m + 60))
        elif count == 2:
            interval = pt.followup_interval_min or 10
            points.append((TRIGGER_OFFSET_10MIN, m + interval))
        return points

    # ==================== 发送与记录 ====================

    async def _send_via_channel(self, plan: CheckinPlan, plan_time: PlanNotificationTime,
                                channel: NotificationChannel, trigger_type: int, notify_date) -> None:
        """按渠道类型发送通知并写入 notification_logs"""
        now = now_shanghai()

        if channel.channel_type == CHANNEL_TYPE_ZNX:
            # 站内信：直接写 notification_logs（status=未读），即完成"发送"
            log = NotificationLog(
                plan_id=plan.id,
                channel_id=channel.id,
                plan_time_id=plan_time.id,
                user_id=plan.user_id,
                send_time=now,
                notify_date=notify_date,
                status=LOG_STATUS_UNREAD,
                trigger_type=trigger_type,
            )
            self.db.add(log)
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()
                logger.exception(f"站内信通知写入失败 plan={plan.id} channel={channel.id}")
            return

        if channel.channel_type == CHANNEL_TYPE_EMAIL:
            await self._send_email(plan, plan_time, channel, trigger_type, notify_date, now)
            return

        if channel.channel_type == CHANNEL_TYPE_WECHAT:
            await self._send_wechat(plan, plan_time, channel, trigger_type, notify_date, now)
            return

        if channel.channel_type == CHANNEL_TYPE_APP_PUSH:
            await self._send_app_push(plan, plan_time, channel, trigger_type, notify_date, now)
            return

        logger.warning(f"未知渠道类型 channel={channel.id} type={channel.channel_type}，跳过")

    async def _send_email(self, plan: CheckinPlan, plan_time: PlanNotificationTime,
                          channel: NotificationChannel, trigger_type: int, notify_date, now: datetime) -> None:
        """邮件渠道发送：解析配置→查收件人→解密密码→SMTP 发送→记录日志"""
        # 1. 解析 channel_value JSON
        cfg = NotificationChannelService.parse_email_channel_value(channel.channel_value)
        if not cfg:
            logger.warning(f"邮件渠道 {channel.id} JSON 解析失败，跳过")
            await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now,
                                  LOG_STATUS_FAILED, "邮件渠道配置解析失败")
            return

        # 2. 查收件人邮箱（users.email）
        user_result = await self.db.execute(
            select(UserModel).where(UserModel.id == plan.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.email:
            logger.warning(f"用户 {plan.user_id} 未绑定邮箱，跳过邮件通知")
            await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now,
                                  LOG_STATUS_FAILED, "用户未绑定邮箱")
            return

        # 3. 解密 SMTP 密码
        try:
            smtp_password = decrypt(cfg.get("password", ""))
        except Exception as e:
            logger.error(f"邮件渠道 {channel.id} 密码解密失败: {e}")
            await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now,
                                  LOG_STATUS_FAILED, f"密码解密失败: {e}")
            return

        # 4. 组装邮件内容（结构化字段 (字段名, 值, 是否加粗)，由 Email.send_notification 逐字段渲染；
        #    备注可能多行，整体作为一个字段值且不加粗——多行内容中含冒号不会被误拆为新字段）
        trigger_desc = _trigger_desc(plan_time, trigger_type)
        reminder_str = plan_time.notification_time.strftime("%H:%M")
        subject = f"【按时吃药】{plan.name} - {trigger_desc}"
        # 计划周期：end_mode=0 显示起止日期；1/2 的 end_date 为 9999-12-31 哨兵，仅显示开始日期起
        if plan.end_mode == 0:
            period_value = f"{plan.start_date} ~ {plan.end_date}"
        else:
            period_value = f"{plan.start_date} 起"
        fields = [
            ("计划名称", plan.name, True),
            ("备注", plan.remark or "无", False),
            ("计划周期", period_value, True),
            ("提醒时间", reminder_str, True),
            ("触发类型", trigger_desc, True),
        ]

        # 5. SMTP 发送（在线程池中执行同步调用，避免阻塞事件循环）
        status = LOG_STATUS_SUCCESS
        error_msg = None
        try:
            await asyncio.to_thread(
                Email().send_notification,
                user.email,
                subject,
                fields,
                cfg.get("smtp_host", ""),
                int(cfg.get("smtp_port", 465)),
                cfg.get("email", ""),
                smtp_password,
            )
        except Exception as e:
            status = LOG_STATUS_FAILED
            error_msg = str(e)[:255]

        # 6. 记录发送结果
        await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now, status, error_msg)

    async def _send_wechat(self, plan: CheckinPlan, plan_time: PlanNotificationTime,
                           channel: NotificationChannel, trigger_type: int, notify_date, now: datetime) -> None:
        """微信订阅消息渠道发送（一次性订阅：授权额度制）"""
        # 1. 检查授权额度（granted - sent）
        quota = NotificationChannelService.parse_wechat_channel_value(channel.channel_value)
        if quota["granted"] - quota["sent"] <= 0:
            logger.debug(f"微信渠道 {channel.id} 授权额度已用完，跳过本次发送")
            return

        # 2. 获取用户 openid
        openid = await self._get_openid(plan.user_id)
        if not openid:
            await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now,
                                  LOG_STATUS_FAILED, "未找到用户微信 openid")
            return

        # 3. 组装模板字段（一次性订阅模板字段固定，须严格匹配）
        reminder_str = plan_time.notification_time.strftime("%H:%M")
        data = {
            "thing4": {"value": (plan.name or "打卡提醒")[:20]},          # 打卡名称
            "thing3": {"value": (plan.remark or "请按时完成打卡")[:20]},  # 备注
            "time13": {"value": reminder_str},                            # 提醒时间
            "thing12": {"value": settings.WX_SUBSCRIBE_ORG_NAME[:20]},    # 机构名称
        }

        # 4. 调用微信接口下发
        try:
            result = await WeChatService.send_subscribe_message(
                openid,
                settings.WX_SUBSCRIBE_TEMPLATE_ID,
                data,
                settings.WX_SUBSCRIBE_PAGE,
            )
        except Exception as e:
            await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now,
                                  LOG_STATUS_FAILED, f"微信接口调用异常: {e}"[:255])
            return

        errcode = result.get("errcode", 0)
        if errcode == 0:
            # 发送成功：消费一次额度
            quota["sent"] += 1
            channel.channel_value = json.dumps(quota, ensure_ascii=False)
            channel.updated_at = now_shanghai()
            await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now,
                                  LOG_STATUS_SUCCESS, None)
        elif errcode == ERRCODE_NO_PERMISSION:
            # 用户拒绝/未授权（额度已失效）：将 granted 对齐 sent，停止后续发送
            quota["granted"] = quota["sent"]
            channel.channel_value = json.dumps(quota, ensure_ascii=False)
            channel.updated_at = now_shanghai()
            await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now,
                                  LOG_STATUS_FAILED, "微信订阅授权已失效（额度用尽或已取消）")
        else:
            await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now,
                                  LOG_STATUS_FAILED, f"微信发送失败 errcode={errcode} {result.get('errmsg')}"[:255])

    async def _send_app_push(self, plan: CheckinPlan, plan_time: PlanNotificationTime,
                             channel: NotificationChannel, trigger_type: int, notify_date,
                             now: datetime) -> None:
        """
        App 推送渠道发送（友盟+ U-Push，多设备遍历下发）

        - 每用户仅一行渠道，channel_value 内为设备 token 数组，逐个 token 下发
        - 成功：该 token 的 fail_count 归零
        - 失败：该 token 的 fail_count +1，累计满 APP_PUSH_MAX_FAIL_COUNT 次即剔除
        - 数组被清空时删除整行渠道（用户需重新在通知方式页添加）
        - 日志：无论多少设备，按渠道只写 1 条 notification_logs
          全部成功 / 部分成功 → status=成功；全部失败 → status=失败
        """
        cfg = NotificationChannelService.parse_app_push_channel_value(channel.channel_value)
        if not cfg.device_tokens:
            # 无设备可推送：清理空渠道行，避免残留
            await self.db.delete(channel)
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()
            logger.info(f"App推送渠道 {channel.id} 无可用设备，已删除该通知方式")
            return

        trigger_desc = _trigger_desc(plan_time, trigger_type)
        reminder_str = plan_time.notification_time.strftime("%H:%M")
        title = f"{plan.name} - {trigger_desc}"
        content = f"{reminder_str} {plan.remark or '请按时完成打卡'}"
        # 附加跳转路径，前端 plus.push click 事件据此 reLaunch 到首页打卡
        extra = {"page": settings.UMENG_PUSH_PAGE, "plan_id": str(plan.id)}

        success_count = 0
        errors: list[str] = []
        kept_tokens = []
        for device in cfg.device_tokens:
            try:
                await UmengService.send(
                    device_token=device.token,
                    title=title,
                    content=content,
                    platform=device.platform,
                    extra=extra,
                )
            except UmengPushError as e:
                device.fail_count += 1
                errors.append(str(e))
                if device.fail_count >= APP_PUSH_MAX_FAIL_COUNT:
                    # 连续失败达上限：判定设备失效，从数组中剔除
                    logger.info(
                        f"App推送设备连续失败{device.fail_count}次已剔除 "
                        f"channel={channel.id} platform={device.platform}"
                    )
                    continue
                kept_tokens.append(device)
            else:
                device.fail_count = 0  # 成功即归零，避免历史失败累积误删
                success_count += 1
                kept_tokens.append(device)

        if success_count > 0:
            status, error_msg = LOG_STATUS_SUCCESS, None
        else:
            status = LOG_STATUS_FAILED
            error_msg = ("；".join(errors) or "App推送全部失败")[:255]

        # 先落日志（内部会 commit），再处理渠道行本身，避免删除后 channel.id 失效
        cfg.device_tokens = kept_tokens
        if cfg.device_tokens:
            channel.channel_value = cfg.model_dump_json()
            channel.updated_at = now_shanghai()
            await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now,
                                  status, error_msg)
            return

        # 全部设备失效：写完日志后删除该通知方式（外键无物理约束，日志 channel_id 保留可溯源）
        await self._write_log(plan, plan_time, channel, trigger_type, notify_date, now,
                              status, error_msg)
        await self.db.delete(channel)
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            logger.exception(f"App推送渠道删除失败 channel={channel.id}")
        else:
            logger.info("App推送渠道全部设备失效，已删除该通知方式")

    async def _get_openid(self, user_id: int) -> str | None:
        """按 user_id + appid 在用户库 user_miniapp_accounts 中查询 openid"""
        result = await self.db.execute(
            select(UserMiniappAccount.openid).where(
                UserMiniappAccount.app_id == settings.WX_APPID,
                UserMiniappAccount.user_id == user_id,
            )
        )
        row = result.first()
        return row[0] if row else None

    async def _write_log(self, plan: CheckinPlan, plan_time: PlanNotificationTime,
                         channel: NotificationChannel, trigger_type: int, notify_date,
                         now: datetime, status: int, error_msg: str | None) -> None:
        """写入一条 notification_logs 记录"""
        log = NotificationLog(
            plan_id=plan.id,
            channel_id=channel.id,
            plan_time_id=plan_time.id,
            user_id=plan.user_id,
            send_time=now,
            notify_date=notify_date,
            status=status,
            trigger_type=trigger_type,
            error_msg=error_msg,
        )
        self.db.add(log)
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            logger.exception(f"通知日志写入失败 plan={plan.id} channel={channel.id}")
