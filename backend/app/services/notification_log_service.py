from collections import defaultdict
from datetime import date, datetime, time as dt_time, timedelta
from typing import Any

from sqlalchemy import delete, select, text, and_, case, func as sa_func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.checkin_record import CheckinRecord
from ..models.notification_log import NotificationLog
from ..models.notification_channel import NotificationChannel
from ..models.plan import CheckinPlan
from ..schemas.notification_channel import CHANNEL_TYPE_ZNX
from ..schemas.notification_log import LOG_STATUS_SUCCESS, LOG_STATUS_UNREAD
from ..utils.logger import logger
from ..utils.timezone import now_shanghai
from .checkin_service import CheckinService

# 自动已读判定回看天数（2026-10-25 性能优化）：仅扫描归属日不早于「今天-N天」的
# 未读——更早的未读其匹配窗口已完全结束（前端打卡均为当前时刻，跨日补打窗口
# 最迟到次日 ~01:30），不可能再被新打卡命中；长期囤积未读的用户每次 unread-count
# 轮询不再重算已关闭的窗口。需清理这类历史未读时用「全部已读」
AUTO_MARK_LOOKBACK_DAYS: int = 3

# 过期日志清理的每批删除行数上限：分批删除避免大事务长锁
# （表增长后单条 DELETE 全量清理可能长时间持有行锁与 undo 压力）
_CLEANUP_BATCH_SIZE: int = 5000


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
        - 匹配区间复用 CheckinService.compute_day_windows（按相邻中点划分，末次区间跨日延伸），
          次日凌晨的补打记录同样会将前一日末次提醒的催办站内信标记为已读
        - plan_time_id 为 NULL / 计划已删除 / notify_date 为 NULL / 无打卡记录 → 保持未读
        - 已读（status=0）记录不参与判定
        - 打卡记录一次范围查询预取（覆盖全部涉及计划与归属日窗口）后内存分组匹配，
          无论未读日志条数/组数多少，打卡记录查询恒为 1 次（2026-10-25 性能优化：
          由逐组查询收敛为单次预取）
        """
        # 1. 查询该用户所有未读站内信记录（仅回看窗口内：更早的未读其匹配窗口
        #    已完全结束，不可能再被新打卡命中，不再参与判定与加载）
        #    notify_date 为 NULL 的记录本就不参与自动已读（下方内存跳过），一并排除
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
                    NotificationLog.notify_date
                    >= now_shanghai().date() - timedelta(days=AUTO_MARK_LOOKBACK_DAYS),
                )
            )
        )
        unread_logs = list(unread_result.scalars().all())
        if not unread_logs:
            return

        # 2. 批量加载相关计划（含提醒时间，selectinload 避免 N+1）
        plan_ids = {log.plan_id for log in unread_logs if log.plan_time_id is not None}
        plans_map: dict[int, CheckinPlan] = {}
        if plan_ids:
            plans_result = await self.db.execute(
                select(CheckinPlan)
                .where(CheckinPlan.id.in_(plan_ids))
                .options(selectinload(CheckinPlan.notification_times))
            )
            for plan in plans_result.scalars().all():
                plans_map[plan.id] = plan

        # 3. 按 (plan_id, notify_date) 分组：同组日志共用一次窗口计算与一次打卡记录查询
        groups: dict[tuple[int, date], list[NotificationLog]] = {}
        for log in unread_logs:
            if log.plan_time_id is None or log.notify_date is None:
                continue
            if log.plan_id not in plans_map:
                # 计划已删除 → 无法获取提醒时间，保持未读
                continue
            groups.setdefault((log.plan_id, log.notify_date), []).append(log)

        # 4. 一次范围查询预取全部涉及计划的打卡记录（窗口覆盖最早归属日 ~ 最晚归属日+2天，
        #    各组窗口 [归属日 0 点, +2天) 均落在其中），内存按计划分组后逐组匹配区间，
        #    消除逐组查询的 N+1（此前查询次数 = 组数，未读跨多日/多计划时线性放大）
        records_by_plan: dict[int, list[datetime]] = defaultdict(list)
        if groups:
            group_plan_ids = {pid for pid, _ in groups}
            min_date = min(d for _, d in groups)
            max_date = max(d for _, d in groups)
            span_start = datetime.combine(min_date, dt_time(0, 0, 0))
            span_end = datetime.combine(max_date + timedelta(days=2), dt_time(0, 0, 0))
            records_result = await self.db.execute(
                select(CheckinRecord.plan_id, CheckinRecord.actual_time).where(
                    and_(
                        CheckinRecord.user_id == user_id,
                        CheckinRecord.plan_id.in_(group_plan_ids),
                        CheckinRecord.actual_time >= span_start,
                        CheckinRecord.actual_time < span_end,
                    )
                )
            )
            for pid, at in records_result.all():
                records_by_plan[pid].append(at)

        marked = False
        for (plan_id, notify_date), logs in groups.items():
            plan = plans_map[plan_id]
            times = sorted(plan.notification_times, key=lambda nt: nt.notification_time)
            # 该计划该日的完整匹配窗口（含跨日延伸，各日志按 plan_time_id 定位各自区间）
            windows = CheckinService.compute_day_windows(plan, notify_date, times)
            pending: list[tuple[NotificationLog, int, int]] = []
            for log in logs:
                idx = next(
                    (i for i, nt in enumerate(times) if nt.id == log.plan_time_id), None
                )
                if idx is None:
                    continue
                start_min, end_min = windows["intervals"][idx]
                pending.append((log, start_min, end_min))
            if not pending:
                continue
            # 组内匹配窗口 [归属日 0 点, +2天)（区间终点最大约次日 25.5 小时，取 2 天覆盖）
            day_start = datetime.combine(notify_date, dt_time(0, 0, 0))
            day_end = day_start + timedelta(days=2)
            actual_minutes = [
                int((at - day_start).total_seconds()) // 60
                for at in records_by_plan.get(plan_id, [])
                if day_start <= at < day_end
            ]
            if not actual_minutes:
                continue
            for log, start_min, end_min in pending:
                if any(start_min <= m < end_min for m in actual_minutes):
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
        - JOIN notification_channels 过滤 channel_type='站内信'：
          仅查 channel_type=ZNX，App 推送（app_push）/ 邮件日志不在此列，
          它们同样落在 notification_logs 中（仅作发送回执），但不在站内信页展示
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

        # 总数与未读数合并为一次聚合查询（过滤条件完全相同，仅 status 口径不同，
        # 省去此前 total、unread_count 各查一次的两次往返）
        counts_result = await self.db.execute(
            select(
                sa_func.count(NotificationLog.id),
                sa_func.coalesce(
                    sa_func.sum(
                        case(
                            (NotificationLog.status == LOG_STATUS_UNREAD, 1),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
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
        total, unread_count = counts_result.one()
        total = int(total)
        unread_count = int(unread_count)

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

    async def count_unread_with_auto_mark(self, user_id: int) -> int:
        """
        统计用户未读站内信数量（先自动标记已读，再返回清理后的真实数量）
        - 供通知图标实时切换接口（unread-count）使用：先扫描未读站内信，匹配区间内
          已有打卡记录的更新为已读，再返回剩余未读数
        - 与 list_znx_by_user 共用 _auto_mark_read_if_checked 自动标记逻辑
        """
        await self._auto_mark_read_if_checked(user_id)
        return await self.count_unread(user_id)

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
            # 对外仅返回固定文案，异常详情只写日志
            logger.exception("标记站内信已读失败 log_id=%s user_id=%s", log_id, user_id)
            raise ValueError("标记已读失败，请稍后重试") from e
        # 模型无服务器端默认列，expire_on_commit=False 下无需 refresh 回读
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
            # 对外仅返回固定文案，异常详情只写日志
            logger.exception("全部标记已读失败 user_id=%s", user_id)
            raise ValueError("全部标记已读失败，请稍后重试") from e
        return int(result.rowcount or 0)

    async def cleanup_expired_logs(self, retention_days: int) -> int:
        """
        清理过期的通知日志（数据保留策略，供调度器每日调用）
        - 删除「非未读（已读/失败）且 send_time 早于保留期」的 notification_logs；
          未读（status=2）不清理，保留未读角标语义
        - 分批删除（每批 _CLEANUP_BATCH_SIZE 行），返回累计删除行数
        - retention_days <= 0 视为关闭清理，直接返回 0
        """
        if retention_days <= 0:
            return 0
        cutoff = now_shanghai() - timedelta(days=retention_days)
        total = 0
        while True:
            # MariaDB 原生 DELETE ... LIMIT 分批删除（表名取自 ORM 模型；
            # Delete 构造无 limit()，且 MariaDB 不支持 IN 子查询内带 LIMIT）：
            # 每批最多 _CLEANUP_BATCH_SIZE 行，避免大事务长锁与 undo 压力
            result = await self.db.execute(
                text(
                    "DELETE FROM `notification_logs` "
                    "WHERE `status` != :unread AND `send_time` < :cutoff "
                    "LIMIT :batch"
                ),
                {"unread": LOG_STATUS_UNREAD, "cutoff": cutoff, "batch": _CLEANUP_BATCH_SIZE},
            )
            await self.db.commit()
            deleted = int(result.rowcount or 0)
            total += deleted
            if deleted < _CLEANUP_BATCH_SIZE:
                break
        if total:
            logger.info(f"已清理过期通知日志 {total} 条（保留 {retention_days} 天，未读不清理）")
        return total
