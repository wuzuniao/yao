"""
定时任务调度服务（定时计划类）
--------------------------------------------------------------------------
集中管理所有后台定时任务循环，main.py 启动时调用 start_all() 拉起全部任务。
其他业务类（User/Email/PlanService 等）如需定时触发能力，由本服务统一调度。

当前包含三类后台任务：
1. 账号清理循环（每 30 秒）：清理 status=0 且超时的删除计划账号
2. 计划自动关闭循环（每 30 分钟）：将 end_date<today 的进行中计划置为已结束
3. 定时通知派发循环（每 60 秒）：根据打卡计划提醒时间发送站内信/邮件通知

通知派发逻辑：
- 准时触发（trigger_type=0）：到达提醒时间，且当天打卡记录数 < 提醒时间数时发送
- 超时催办（trigger_type=1/2/3）：超过提醒时间 5 分钟/30 分钟/1 小时，该时间点仍无打卡记录时发送
- 防重：以 (plan_time_id, trigger_type, notify_date, channel_id) 为去重键查询 notification_logs
- 站内信：直接写 notification_logs（status=2 未读）
- 邮件：读取用户 notification_channels.channel_value 作为 SMTP 发送，收件人取 users.email
"""
import asyncio
from datetime import datetime, time as dt_time, timedelta

from sqlalchemy import select, func as sa_func
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
)
from ..schemas.notification_log import (
    LOG_STATUS_SUCCESS,
    LOG_STATUS_FAILED,
    LOG_STATUS_UNREAD,
    TRIGGER_ON_TIME,
    FOLLOWUP_OFFSETS,
    TRIGGER_DESC,
)
from ..utils.timezone import now_shanghai
from ..utils.crypto import decrypt
from ..utils.logger import logger
from .email_service import Email
from .user_service import User
from .plan_service import PlanService
from .notification_channel_service import NotificationChannelService


# 后台循环间隔（秒）
INTERVAL_PURGE: int = 30        # 账号清理：每 30 秒
INTERVAL_PLAN_CLOSE: int = 1800  # 计划关闭：每 30 分钟
INTERVAL_NOTIFICATION: int = 60   # 通知派发：每 60 秒


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
        ]
        logger.info("定时任务调度服务已启动：账号清理/计划关闭/通知派发")

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


class NotificationDispatcher:
    """
    通知派发器（单次执行，由 SchedulerService 每分钟实例化调用）
    --------------------------------------------------------------------------
    将派发逻辑独立成类，避免 SchedulerService 承载过多职责。
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch_for_now(self) -> int:
        """
        派发当前时刻应触发的所有通知（准时 + 三档催办）
        - 准时：当前 HH:MM 命中提醒时间
        - 催办：当前 HH:MM == 提醒时间 + 5/30/60 分钟
        返回成功派发的通知数（不含被去重跳过的）
        """
        now = now_shanghai()
        sent = 0
        # 准时触发
        sent += await self._dispatch_trigger(now, TRIGGER_ON_TIME)
        # 三档催办：now 反推提醒时间 = now - offset
        for trigger_type, offset_min in FOLLOWUP_OFFSETS:
            target = now - timedelta(minutes=offset_min)
            sent += await self._dispatch_trigger(target, trigger_type)
        return sent

    async def _dispatch_trigger(self, target_dt: datetime, trigger_type: int) -> int:
        """
        派发某一触发类型的通知
        :param target_dt: 提醒时间所在的 datetime（准时=now，催办=now-offset）
        :param trigger_type: TRIGGER_ON_TIME / TRIGGER_OFFSET_5MIN / ...
        """
        # 截断到分钟（秒数置零），与 DB 中 TIME 列 HH:MM:SS 对齐
        target_time = dt_time(target_dt.hour, target_dt.minute)
        notify_date = target_dt.date()

        # 查询当日有效且提醒时间 == target_time 的计划时间点
        result = await self.db.execute(
            select(PlanNotificationTime)
            .join(CheckinPlan, PlanNotificationTime.plan_id == CheckinPlan.id)
            .where(
                PlanNotificationTime.notification_time == target_time,
                CheckinPlan.status == 1,
                CheckinPlan.start_date <= notify_date,
                CheckinPlan.end_date >= notify_date,
            )
            .options(
                selectinload(PlanNotificationTime.plan).selectinload(CheckinPlan.notification_times)
            )
        )
        plan_times = result.scalars().all()

        sent = 0
        for pt in plan_times:
            plan = pt.plan
            # 准时触发：当天打卡记录数 < 提醒时间数 才发送
            # 催办触发：该提醒时间点当天无打卡记录 才发送
            if trigger_type == TRIGGER_ON_TIME:
                times_count = len(plan.notification_times)
                checkin_count = await self._count_checkins(plan.id, plan.user_id, notify_date)
                if checkin_count >= times_count:
                    continue
            else:
                if await self._has_checkin_for_slot(plan.id, pt.id, plan.user_id, notify_date):
                    continue

            # 遍历该计划绑定的通知渠道
            channels = await self._get_channels_for_plan(plan.id)
            for channel in channels:
                if not channel.enabled:
                    continue
                # 防重：同一天同一时间点同一触发类型同一渠道只发一次
                if await self._already_sent(pt.id, trigger_type, notify_date, channel.id):
                    continue
                await self._send_via_channel(plan, pt, channel, trigger_type, notify_date)
                sent += 1
        return sent

    # ==================== 查询辅助 ====================

    async def _get_channels_for_plan(self, plan_id: int) -> list[NotificationChannel]:
        """查询计划绑定的所有通知渠道（含配置）"""
        result = await self.db.execute(
            select(NotificationChannel)
            .join(PlanNotificationChannel, PlanNotificationChannel.channel_id == NotificationChannel.id)
            .where(PlanNotificationChannel.plan_id == plan_id)
        )
        return list(result.scalars().all())

    async def _count_checkins(self, plan_id: int, user_id: int, notify_date) -> int:
        """统计某计划某日的打卡记录总数（日期范围比较避免时区问题）"""
        day_start = datetime.combine(notify_date, dt_time(0, 0, 0))
        day_end = datetime.combine(notify_date + timedelta(days=1), dt_time(0, 0, 0))
        result = await self.db.execute(
            select(sa_func.count(CheckinRecord.id)).where(
                CheckinRecord.user_id == user_id,
                CheckinRecord.plan_id == plan_id,
                CheckinRecord.actual_time >= day_start,
                CheckinRecord.actual_time < day_end,
            )
        )
        return int(result.scalar() or 0)

    async def _has_checkin_for_slot(self, plan_id: int, plan_time_id: int, user_id: int, notify_date) -> bool:
        """判断某计划某提醒时间点在指定日期是否已有打卡记录"""
        day_start = datetime.combine(notify_date, dt_time(0, 0, 0))
        day_end = datetime.combine(notify_date + timedelta(days=1), dt_time(0, 0, 0))
        result = await self.db.execute(
            select(sa_func.count(CheckinRecord.id)).where(
                CheckinRecord.user_id == user_id,
                CheckinRecord.plan_id == plan_id,
                CheckinRecord.plan_time_id == plan_time_id,
                CheckinRecord.actual_time >= day_start,
                CheckinRecord.actual_time < day_end,
            )
        )
        return int(result.scalar() or 0) > 0

    async def _already_sent(self, plan_time_id: int, trigger_type: int, notify_date, channel_id: int) -> bool:
        """防重查询：当日该时间点+触发类型+渠道是否已发过通知（含失败记录）"""
        result = await self.db.execute(
            select(NotificationLog.id).where(
                NotificationLog.plan_time_id == plan_time_id,
                NotificationLog.trigger_type == trigger_type,
                NotificationLog.notify_date == notify_date,
                NotificationLog.channel_id == channel_id,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

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

        # 4. 组装邮件内容
        trigger_desc = TRIGGER_DESC.get(trigger_type, "提醒")
        reminder_str = plan_time.notification_time.strftime("%H:%M")
        subject = f"【按时打卡】{plan.name} - {trigger_desc}"
        content = (
            f"您的打卡计划「{plan.name}」{trigger_desc}（提醒时间：{reminder_str}）。\n"
            + (f"备注：{plan.remark}\n" if plan.remark else "")
            + "\n请尽快打开小程序完成打卡。"
        )

        # 5. SMTP 发送（在线程池中执行同步调用，避免阻塞事件循环）
        status = LOG_STATUS_SUCCESS
        error_msg = None
        try:
            await asyncio.to_thread(
                Email().send_notification,
                user.email,
                subject,
                content,
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
