"""
服务层测试补充：覆盖 service 层异常分支与边界条件
--------------------------------------------------------------------------
覆盖目标（用户模块用例已迁 auth 服务仓库）：
- plan_service.py: create/update_plan 无渠道/无效渠道/HH:MM:SS 格式、auto_close_expired_plans
- checkin_service.py: create_checkin commit 失败、get_latest_checkin、list_by_month 12月分支
- notification_log_service.py: _auto_mark_read 计划已删除/idx None、commit 失败分支
- notification_channel_service.py: delete_channel 无权操作
"""
from datetime import date, datetime, time as dt_time, timedelta
from unittest.mock import patch, AsyncMock

import pytest

from app.models.checkin_record import CheckinRecord
from app.models.notification_channel import NotificationChannel
from app.models.notification_log import NotificationLog
from app.services.plan_service import PlanService
from app.services.checkin_service import CheckinService
from app.services.notification_log_service import NotificationLogService
from app.services.notification_channel_service import NotificationChannelService
from app.schemas.notification_channel import CHANNEL_TYPE_ZNX, CHANNEL_TYPE_EMAIL
from app.schemas.plan import NotificationTimeItem
from sqlalchemy import select


# ===== plan_service.py 覆盖 =====


class TestPlanServiceCoverage:
    """PlanService 异常分支与未测试方法覆盖"""

    @pytest.mark.asyncio
    async def test_create_plan_no_channels(self, db_session, test_user):
        """create_plan: 未选择通知渠道应抛出 ValueError"""
        service = PlanService(db_session)
        with pytest.raises(ValueError, match="至少选择一个通知方式"):
            await service.create_plan(
                test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
                [NotificationTimeItem(time="08:00")], [],
            )

    @pytest.mark.asyncio
    async def test_create_plan_hh_mm_ss_format(self, db_session, test_user):
        """create_plan: HH:MM:SS 格式时间应正确解析"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        service = PlanService(db_session)
        plan = await service.create_plan(
            test_user.id, "测试计划", "", date(2026, 1, 1), date(2026, 12, 31),
            [NotificationTimeItem(time="08:00:30")], [znx_channel.id],
        )
        # 重新查询以加载关联关系（异步 SQLAlchemy 不支持懒加载）
        plan = await service.get_by_id(plan.id)
        assert len(plan.notification_times) == 1
        assert plan.notification_times[0].notification_time == dt_time(8, 0, 30)

    @pytest.mark.asyncio
    async def test_update_plan_no_channels(self, db_session, test_user):
        """update_plan: 未选择通知渠道应抛出 ValueError"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        service = PlanService(db_session)
        plan = await service.create_plan(
            test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
            [NotificationTimeItem(time="08:00")], [znx_channel.id],
        )
        with pytest.raises(ValueError, match="至少选择一个通知方式"):
            await service.update_plan(
                plan.id, test_user.id, "更新", "", date(2026, 1, 1), date(2026, 12, 31),
                [NotificationTimeItem(time="08:00")], [],
            )

    @pytest.mark.asyncio
    async def test_update_plan_invalid_channels(self, db_session, test_user):
        """update_plan: 包含无效渠道应抛出 ValueError"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        service = PlanService(db_session)
        plan = await service.create_plan(
            test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
            [NotificationTimeItem(time="08:00")], [znx_channel.id],
        )
        with pytest.raises(ValueError, match="包含无效或非本用户的通知渠道"):
            await service.update_plan(
                plan.id, test_user.id, "更新", "", date(2026, 1, 1), date(2026, 12, 31),
                [NotificationTimeItem(time="08:00")], [999999],
            )

    @pytest.mark.asyncio
    async def test_update_plan_hh_mm_ss_format(self, db_session, test_user):
        """update_plan: HH:MM:SS 格式时间应正确解析"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        service = PlanService(db_session)
        plan = await service.create_plan(
            test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
            [NotificationTimeItem(time="08:00")], [znx_channel.id],
        )
        updated = await service.update_plan(
            plan.id, test_user.id, "更新", "", date(2026, 1, 1), date(2026, 12, 31),
            [NotificationTimeItem(time="20:00:45")], [znx_channel.id],
        )
        # 重新查询以加载关联关系（异步 SQLAlchemy 不支持懒加载）
        updated = await service.get_by_id(updated.id)
        assert updated.notification_times[0].notification_time == dt_time(20, 0, 45)

    @pytest.mark.asyncio
    async def test_auto_close_expired_plans(self, db_session, test_user):
        """auto_close_expired_plans: 过期计划应自动关闭（status 1→0）"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        service = PlanService(db_session)
        # 创建已过期计划（end_date 为昨天，status=1）
        yesterday = date.today() - timedelta(days=1)
        plan = await service.create_plan(
            test_user.id, "过期计划", "", date(2026, 1, 1), yesterday,
            [NotificationTimeItem(time="08:00")], [znx_channel.id], status=1,
        )
        affected = await service.auto_close_expired_plans()
        assert affected >= 1
        await db_session.refresh(plan)
        assert plan.status == 0


# ===== checkin_service.py 覆盖 =====


class TestCheckinServiceCoverage:
    """CheckinService 异常分支与未测试方法覆盖"""

    @pytest.mark.asyncio
    async def test_create_checkin_commit_failure(self, db_session, test_user):
        """create_checkin: commit 失败应抛出 ValueError"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        plan_service = PlanService(db_session)
        plan = await plan_service.create_plan(
            test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
            [NotificationTimeItem(time="08:00")], [znx_channel.id],
        )
        # 重新查询以加载关联关系（异步 SQLAlchemy 不支持懒加载）
        plan = await plan_service.get_by_id(plan.id)
        nt = plan.notification_times[0]
        service = CheckinService(db_session)
        with patch.object(db_session, "commit", new=AsyncMock(side_effect=Exception("commit失败"))):
            with pytest.raises(ValueError, match="打卡失败"):
                await service.create_checkin(
                    test_user.id, plan.id, nt.id, datetime(2026, 7, 2, 8, 0),
                )

    @pytest.mark.asyncio
    async def test_get_latest_checkin(self, db_session, test_user):
        """get_latest_checkin: 应返回最近一次打卡记录"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        plan_service = PlanService(db_session)
        plan = await plan_service.create_plan(
            test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
            [NotificationTimeItem(time="08:00")], [znx_channel.id],
        )
        # 重新查询以加载关联关系（异步 SQLAlchemy 不支持懒加载）
        plan = await plan_service.get_by_id(plan.id)
        nt = plan.notification_times[0]
        service = CheckinService(db_session)
        # 创建两条打卡记录
        await service.create_checkin(test_user.id, plan.id, nt.id, datetime(2026, 7, 2, 8, 0))
        await service.create_checkin(test_user.id, plan.id, nt.id, datetime(2026, 7, 2, 9, 0))
        latest = await service.get_latest_checkin(test_user.id, plan.id)
        assert latest is not None
        assert latest.actual_time == datetime(2026, 7, 2, 9, 0)

    @pytest.mark.asyncio
    async def test_list_by_month_december(self, db_session, test_user):
        """list_by_month: 12月查询应正确处理跨年（year+1, 1月）"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        plan_service = PlanService(db_session)
        plan = await plan_service.create_plan(
            test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
            [NotificationTimeItem(time="08:00")], [znx_channel.id],
        )
        # 重新查询以加载关联关系（异步 SQLAlchemy 不支持懒加载）
        plan = await plan_service.get_by_id(plan.id)
        nt = plan.notification_times[0]
        service = CheckinService(db_session)
        await service.create_checkin(test_user.id, plan.id, nt.id, datetime(2026, 12, 31, 8, 0))
        days = await service.list_by_month(test_user.id, 2026, 12)
        assert 31 in days


# ===== notification_log_service.py 覆盖 =====


class TestNotificationLogServiceCoverage:
    """NotificationLogService 异常分支覆盖"""

    @pytest.mark.asyncio
    async def test_auto_mark_read_plan_deleted(self, db_session, test_user):
        """_auto_mark_read_if_checked: 计划已删除时应 continue（不报错）"""
        # 创建未读站内信，plan_time_id 指向不存在的计划
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        log = NotificationLog(
            plan_id=999999, channel_id=znx_channel.id, plan_time_id=999999,
            user_id=test_user.id, send_time=datetime(2026, 7, 2, 8, 0),
            notify_date=date(2026, 7, 2), status=2, trigger_type=0,
        )
        db_session.add(log)
        await db_session.commit()
        service = NotificationLogService(db_session)
        # 调用 list_znx_by_user 触发 _auto_mark_read_if_checked，不应抛出异常
        result = await service.list_znx_by_user(test_user.id)
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_auto_mark_read_idx_none(self, db_session, test_user):
        """_auto_mark_read_if_checked: plan_time_id 不在计划提醒时间列表中时应 continue"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        plan = await PlanService(db_session).create_plan(
            test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
            [NotificationTimeItem(time="08:00")], [znx_channel.id],
        )
        # 创建站内信，plan_time_id 指向不存在的通知时间点（但计划存在）
        log = NotificationLog(
            plan_id=plan.id, channel_id=znx_channel.id, plan_time_id=999999,
            user_id=test_user.id, send_time=datetime(2026, 7, 2, 8, 0),
            notify_date=date(2026, 7, 2), status=2, trigger_type=0,
        )
        db_session.add(log)
        await db_session.commit()
        service = NotificationLogService(db_session)
        result = await service.list_znx_by_user(test_user.id)
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_auto_mark_read_commit_failure(self, db_session, test_user):
        """_auto_mark_read_if_checked: commit 失败时应回滚但不抛出异常"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        plan_service = PlanService(db_session)
        plan = await plan_service.create_plan(
            test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
            [NotificationTimeItem(time="08:00")], [znx_channel.id],
        )
        # 重新查询以加载关联关系（异步 SQLAlchemy 不支持懒加载）
        plan = await plan_service.get_by_id(plan.id)
        nt = plan.notification_times[0]
        # 创建未读站内信和对应打卡记录（触发 marked=True）
        log = NotificationLog(
            plan_id=plan.id, channel_id=znx_channel.id, plan_time_id=nt.id,
            user_id=test_user.id, send_time=datetime(2026, 7, 2, 8, 0),
            notify_date=date(2026, 7, 2), status=2, trigger_type=0,
        )
        db_session.add(log)
        record = CheckinRecord(
            user_id=test_user.id, plan_id=plan.id, plan_time_id=nt.id,
            actual_time=datetime(2026, 7, 2, 8, 5),
        )
        db_session.add(record)
        await db_session.commit()
        service = NotificationLogService(db_session)
        with patch.object(db_session, "commit", new=AsyncMock(side_effect=Exception("commit失败"))):
            # 不应抛出异常（内部 try-except 回滚）
            await service._auto_mark_read_if_checked(test_user.id)

    @pytest.mark.asyncio
    async def test_mark_as_read_commit_failure(self, db_session, test_user):
        """mark_as_read: commit 失败应抛出 ValueError"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        log = NotificationLog(
            plan_id=1, channel_id=znx_channel.id, plan_time_id=1,
            user_id=test_user.id, send_time=datetime(2026, 7, 2, 8, 0),
            notify_date=date(2026, 7, 2), status=2, trigger_type=0,
        )
        db_session.add(log)
        await db_session.commit()
        await db_session.refresh(log)
        service = NotificationLogService(db_session)
        with patch.object(db_session, "commit", new=AsyncMock(side_effect=Exception("commit失败"))):
            with pytest.raises(ValueError, match="标记已读失败"):
                await service.mark_as_read(log.id, test_user.id)

    @pytest.mark.asyncio
    async def test_mark_all_as_read_commit_failure(self, db_session, test_user):
        """mark_all_as_read: commit 失败应抛出 ValueError"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        log = NotificationLog(
            plan_id=1, channel_id=znx_channel.id, plan_time_id=1,
            user_id=test_user.id, send_time=datetime(2026, 7, 2, 8, 0),
            notify_date=date(2026, 7, 2), status=2, trigger_type=0,
        )
        db_session.add(log)
        await db_session.commit()
        service = NotificationLogService(db_session)
        with patch.object(db_session, "commit", new=AsyncMock(side_effect=Exception("commit失败"))):
            with pytest.raises(ValueError, match="全部标记已读失败"):
                await service.mark_all_as_read(test_user.id)


# ===== notification_channel_service.py 覆盖 =====


class TestNotificationChannelServiceCoverage:
    """NotificationChannelService 异常分支覆盖"""

    @pytest.mark.asyncio
    async def test_delete_channel_no_permission(self, db_session, test_user):
        """delete_channel: 删除他人渠道应抛出 ValueError"""
        # 创建另一个用户（虚拟 ID）及其邮件渠道
        other_user_id = 20003
        other_channel = NotificationChannel(
            user_id=other_user_id, channel_type=CHANNEL_TYPE_EMAIL,
            channel_value='{"smtp_host":"smtp.test.com","smtp_port":465,"email":"other@test.com","password":""}',
            enabled=True,
        )
        db_session.add(other_channel)
        await db_session.commit()
        await db_session.refresh(other_channel)
        # test_user 尝试删除 other_user 的渠道
        service = NotificationChannelService(db_session)
        with pytest.raises(ValueError, match="无权操作该通知渠道"):
            await service.delete_channel(other_channel.id, test_user.id)
