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
- 准时触发（trigger_type=0）：到达提醒时间，且该提醒时间对应匹配区间内无打卡记录时发送
- 催办两档：
  - 档位1（trigger_type=1）：超过提醒时间 10 分钟，匹配区间内无打卡记录时发送
  - 档位2（trigger_type=2）：1 小时 与 下一次提醒中点 择先到达者触发（末次提醒固定 +1 小时），匹配区间内无打卡记录时发送
- 防重：以 (plan_time_id, trigger_type, notify_date, channel_id) 为去重键查询 notification_logs
- 站内信：直接写 notification_logs（status=2 未读）
- 邮件：读取用户 notification_channels.channel_value 作为 SMTP 发送，收件人取 users.email
"""
import asyncio
import json
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
    CHANNEL_TYPE_WECHAT,
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

    派发规则（详见 clarify-notification-logic spec）：
    - 准时触发（trigger_type=0）：当前 HH:MM 命中提醒时间，且该提醒时间对应匹配区间内无打卡记录
    - 档位1催办（trigger_type=1）：当前 HH:MM == 提醒时间+10分钟，且匹配区间内无打卡记录
    - 档位2催办（trigger_type=2）：当前 HH:MM == 档位2触发时间（1小时与中点择先到达者），
      且匹配区间内无打卡记录；末次提醒固定 +1 小时
    - 匹配区间定义同 clarify-checkin-logic spec（按相邻提醒中点划分，覆盖全天 0:00-24:00）
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch_for_now(self) -> int:
        """
        派发当前时刻应触发的所有通知（准时 + 两档催办）
        返回成功派发的通知数（不含被去重跳过的）
        """
        now = now_shanghai()
        sent = 0
        # 准时触发：reminder = now（offset=0）
        sent += await self._dispatch_fixed_offset(now, 0, TRIGGER_ON_TIME)
        # 档位1：reminder = now - 10分钟
        sent += await self._dispatch_fixed_offset(now, FOLLOWUP_OFFSET_10MIN, TRIGGER_OFFSET_10MIN)
        # 档位2：动态触发时间，正向查询今日+昨日有效计划
        sent += await self._dispatch_followup_2(now)
        return sent

    async def _dispatch_fixed_offset(self, now: datetime, offset_min: int, trigger_type: int) -> int:
        """
        处理准时触发和档位1催办（反推提醒时间）
        :param now: 当前时间
        :param offset_min: 偏移分钟数（准时=0，档位1=10）
        :param trigger_type: TRIGGER_ON_TIME / TRIGGER_OFFSET_10MIN
        """
        target_dt = now - timedelta(minutes=offset_min)
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
            # 在计划提醒时间列表中定位 pt 的索引，用于取匹配区间
            times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
            idx = next((i for i, nt in enumerate(times) if nt.id == pt.id), None)
            if idx is None:
                continue
            intervals = self._get_match_intervals_minutes(times)
            start_min, end_min = intervals[idx]
            # 匹配区间内已有打卡记录则跳过
            checkin_count = await self._count_checkins_in_interval(
                plan.user_id, plan.id, notify_date, start_min, end_min
            )
            if checkin_count >= 1:
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

    async def _dispatch_followup_2(self, now: datetime) -> int:
        """档位2催办：动态触发时间，正向查询今日+昨日有效计划"""
        now_min = now.hour * 60 + now.minute
        sent = 0
        # 今日有效计划
        sent += await self._dispatch_followup_2_for_date(now, now.date(), now_min, is_today=True)
        # 昨日有效计划（处理末次提醒+1小时跨天的情况）
        sent += await self._dispatch_followup_2_for_date(
            now, now.date() - timedelta(days=1), now_min, is_today=False
        )
        return sent

    async def _dispatch_followup_2_for_date(
        self, now: datetime, plan_date, now_min: int, is_today: bool
    ) -> int:
        """
        查询某日有效计划的档位2触发
        :param plan_date: 计划有效期判定日期
        :param now_min: 当前时间的分钟数
        :param is_today: plan_date 是否为今日（用于区分当日触发与跨天触发）
        """
        result = await self.db.execute(
            select(CheckinPlan)
            .where(
                CheckinPlan.status == 1,
                CheckinPlan.start_date <= plan_date,
                CheckinPlan.end_date >= plan_date,
            )
            .options(selectinload(CheckinPlan.notification_times))
        )
        plans = result.scalars().all()

        sent = 0
        for plan in plans:
            times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
            if not times:
                continue
            intervals = self._get_match_intervals_minutes(times)
            for idx, pt in enumerate(times):
                reminder_min = pt.notification_time.hour * 60 + pt.notification_time.minute
                # 计算档位2触发分钟数
                if idx < len(times) - 1:
                    next_min = (
                        times[idx + 1].notification_time.hour * 60
                        + times[idx + 1].notification_time.minute
                    )
                    midpoint = (reminder_min + next_min) // 2
                    trigger_min = min(reminder_min + 60, midpoint)
                else:
                    # 末次提醒：固定 +1 小时
                    trigger_min = reminder_min + 60

                # 判断命中
                hit = False
                notify_date = plan_date
                if trigger_min < 1440:
                    # 当日触发：仅今日计划可命中
                    if is_today and now_min == trigger_min:
                        hit = True
                else:
                    # 跨天触发（仅末次提醒+1小时可能发生）：仅昨日计划可命中
                    mapped_min = trigger_min - 1440
                    if not is_today and now_min == mapped_min:
                        hit = True

                if not hit:
                    continue

                # 匹配区间内已有打卡记录则跳过
                start_min, end_min = intervals[idx]
                checkin_count = await self._count_checkins_in_interval(
                    plan.user_id, plan.id, notify_date, start_min, end_min
                )
                if checkin_count >= 1:
                    continue

                # 遍历渠道发送（档位2对同一提醒时间点同一渠道当天只发一次，靠防重键去重）
                channels = await self._get_channels_for_plan(plan.id)
                for channel in channels:
                    if not channel.enabled:
                        continue
                    if await self._already_sent(
                        pt.id, TRIGGER_OFFSET_1HOUR_OR_MIDPOINT, notify_date, channel.id
                    ):
                        continue
                    await self._send_via_channel(
                        plan, pt, channel, TRIGGER_OFFSET_1HOUR_OR_MIDPOINT, notify_date
                    )
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

    @staticmethod
    def _get_match_intervals_minutes(times: list) -> list[tuple[int, int]]:
        """
        计算匹配区间（分钟数），算法同 checkin_service._get_match_intervals
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
                prev_min = (
                    times[i - 1].notification_time.hour * 60
                    + times[i - 1].notification_time.minute
                )
                start = (prev_min + t_min) // 2
            if i == len(times) - 1:
                end = 1440  # 24:00
            else:
                next_min = (
                    times[i + 1].notification_time.hour * 60
                    + times[i + 1].notification_time.minute
                )
                end = (t_min + next_min) // 2
            intervals.append((start, end))
        return intervals

    async def _count_checkins_in_interval(
        self, user_id: int, plan_id: int, notify_date, start_min: int, end_min: int
    ) -> int:
        """查询某计划某日匹配区间内的打卡记录数"""
        day_start = datetime.combine(notify_date, dt_time(0, 0, 0))
        interval_start = day_start + timedelta(minutes=start_min)
        interval_end = day_start + timedelta(minutes=end_min)
        result = await self.db.execute(
            select(sa_func.count(CheckinRecord.id)).where(
                CheckinRecord.user_id == user_id,
                CheckinRecord.plan_id == plan_id,
                CheckinRecord.actual_time >= interval_start,
                CheckinRecord.actual_time < interval_end,
            )
        )
        return int(result.scalar() or 0)

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

        if channel.channel_type == CHANNEL_TYPE_WECHAT:
            await self._send_wechat(plan, plan_time, channel, trigger_type, notify_date, now)
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
