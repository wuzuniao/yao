"""
服务层测试补充：覆盖 service 层异常分支与边界条件
--------------------------------------------------------------------------
覆盖目标：
- user_service.py: verify_code 无记录/过期、_ensure_znx_channel 已存在、各方法用户不存在、bind_email 账号合并、change_email 邮箱已注册
- plan_service.py: create/update_plan 无渠道/无效渠道/HH:MM:SS 格式、auto_close_expired_plans
- checkin_service.py: create_checkin commit 失败、get_latest_checkin、list_by_month 12月分支
- notification_log_service.py: _auto_mark_read 计划已删除/idx None、commit 失败分支
- email_service.py: send_verification_code 非 SMTP 认证异常
- notification_channel_service.py: delete_channel 无权操作
"""
import time
from datetime import date, datetime, time as dt_time, timedelta
from unittest.mock import patch, AsyncMock

import pytest

from app.core.security import Security
from app.models.checkin_record import CheckinRecord
from app.models.notification_channel import NotificationChannel
from app.models.notification_log import NotificationLog
from app.models.plan import CheckinPlan, PlanNotificationTime, PlanNotificationChannel
from app.models.user import User as UserModel
from app.models.user_miniapp_account import UserMiniappAccount
from app.services.user_service import User, _verification_codes
from app.services.plan_service import PlanService
from app.services.checkin_service import CheckinService
from app.services.notification_log_service import NotificationLogService
from app.services.notification_channel_service import NotificationChannelService
from app.schemas.notification_channel import CHANNEL_TYPE_ZNX, CHANNEL_TYPE_EMAIL
from sqlalchemy import select


# ===== user_service.py 覆盖 =====


class TestUserServiceCoverage:
    """User 服务异常分支覆盖"""

    @pytest.mark.asyncio
    async def test_verify_code_no_record(self, db_session):
        """verify_code_for_purpose: 无验证码记录应返回 False"""
        user = User(db_session)
        assert user.verify_code_for_purpose("nobody@example.com", "123456", "register") is False

    @pytest.mark.asyncio
    async def test_verify_code_expired(self, db_session):
        """verify_code_for_purpose: 过期验证码应返回 False 并清理记录"""
        key = "expired@example.com:register"
        _verification_codes[key] = ("123456", time.time() - 1)
        user = User(db_session)
        assert user.verify_code_for_purpose("expired@example.com", "123456", "register") is False
        assert key not in _verification_codes
        _verification_codes.clear()

    @pytest.mark.asyncio
    async def test_ensure_znx_channel_existing(self, db_session, test_user):
        """_ensure_znx_channel: 已存在站内信渠道应直接返回现有记录"""
        user = User(db_session)
        channel = await user._ensure_znx_channel(test_user.id)
        assert channel is not None
        assert channel.channel_type == CHANNEL_TYPE_ZNX

    @pytest.mark.asyncio
    async def test_update_signature_user_not_found(self, db_session):
        """update_signature: 用户不存在应抛出 ValueError"""
        user = User(db_session)
        with pytest.raises(ValueError, match="用户不存在"):
            await user.update_signature(999999, "签名")

    @pytest.mark.asyncio
    async def test_send_change_email_old_code_user_not_found(self, db_session):
        """send_change_email_old_code: 用户不存在应抛出 ValueError"""
        user = User(db_session)
        with pytest.raises(ValueError, match="用户不存在"):
            await user.send_change_email_old_code(999999)

    @pytest.mark.asyncio
    async def test_change_email_user_not_found(self, db_session):
        """change_email: 用户不存在应抛出 ValueError"""
        user = User(db_session)
        with pytest.raises(ValueError, match="用户不存在"):
            await user.change_email(999999, "123456", "new@example.com", "654321")

    @pytest.mark.asyncio
    async def test_change_email_already_registered(self, db_session, test_user):
        """change_email: 新邮箱已被注册应抛出 ValueError（竞态检查）"""
        other = UserModel(
            username="其他用户", email="new@example.com",
            password_hash=Security.hash_password("Test1234!"),
            avatar_url="hei", signature="签名", status=1,
        )
        db_session.add(other)
        await db_session.commit()
        _verification_codes["test@example.com:change_old"] = ("111111", time.time() + 300)
        _verification_codes["new@example.com:change_new"] = ("222222", time.time() + 300)
        user = User(db_session)
        with pytest.raises(ValueError, match="该邮箱已被注册"):
            await user.change_email(test_user.id, "111111", "new@example.com", "222222")
        _verification_codes.clear()

    @pytest.mark.asyncio
    async def test_update_avatar_user_not_found(self, db_session):
        """update_avatar: 用户不存在应抛出 ValueError"""
        user = User(db_session)
        with pytest.raises(ValueError, match="用户不存在"):
            await user.update_avatar(999999, "new")

    @pytest.mark.asyncio
    async def test_schedule_deletion_user_not_found(self, db_session):
        """schedule_deletion: 用户不存在应抛出 ValueError"""
        user = User(db_session)
        with pytest.raises(ValueError, match="用户不存在"):
            await user.schedule_deletion(999999)

    @pytest.mark.asyncio
    async def test_cancel_deletion_user_not_found(self, db_session):
        """cancel_deletion: 用户不存在应抛出 ValueError"""
        user = User(db_session)
        with pytest.raises(ValueError, match="用户不存在"):
            await user.cancel_deletion(999999)

    @pytest.mark.asyncio
    async def test_update_username_user_not_found(self, db_session):
        """update_username: 用户不存在应抛出 ValueError"""
        user = User(db_session)
        with pytest.raises(ValueError, match="用户不存在"):
            await user.update_username(999999, "新用户名")

    @pytest.mark.asyncio
    async def test_bind_email_user_not_found(self, db_session):
        """bind_email: 用户不存在应抛出 ValueError"""
        user = User(db_session)
        with pytest.raises(ValueError, match="用户不存在"):
            await user.bind_email(999999, "new@example.com", "123456")

    @pytest.mark.asyncio
    async def test_bind_email_account_merge(self, db_session):
        """bind_email: 邮箱已存在时应触发账号合并（字段填充+小程序转移+从账号删除）"""
        # 主账号：有邮箱，无用户名/密码/签名/头像
        main_user = UserModel(
            username=None, email="main@example.com",
            password_hash=None, avatar_url=None, signature=None, status=1,
        )
        db_session.add(main_user)
        await db_session.flush()
        # 从账号：无邮箱，有用户名/密码/签名/头像/小程序绑定/最后登录时间
        sub_user = UserModel(
            username="从账号", email=None,
            password_hash=Security.hash_password("Test1234!"),
            avatar_url="lan", signature="从账号签名", status=1,
            last_login_at=datetime(2026, 7, 1, 12, 0, 0),
        )
        db_session.add(sub_user)
        await db_session.flush()
        miniapp = UserMiniappAccount(
            user_id=sub_user.id, app_id="test_app",
            openid="test_openid", session_key="test_session",
        )
        db_session.add(miniapp)
        _verification_codes["main@example.com:change_new"] = ("654321", time.time() + 300)
        user = User(db_session)
        result = await user.bind_email(sub_user.id, "main@example.com", "654321")
        # 验证合并结果：主账号字段被从账号填充
        assert result.id == main_user.id
        assert result.username == "从账号"
        assert result.password_hash is not None
        assert result.signature == "从账号签名"
        assert result.avatar_url == "lan"
        assert result.last_login_at == datetime(2026, 7, 1, 12, 0, 0)
        # 验证小程序绑定已转移到主账号
        miniapp_result = await db_session.execute(
            select(UserMiniappAccount).where(UserMiniappAccount.user_id == main_user.id)
        )
        assert len(miniapp_result.scalars().all()) == 1
        # 验证从账号已删除
        sub_result = await db_session.execute(
            select(UserModel).where(UserModel.id == sub_user.id)
        )
        assert sub_result.scalar_one_or_none() is None
        _verification_codes.clear()

    @pytest.mark.asyncio
    async def test_wechat_login_user_data_anomaly(self, db_session):
        """wechat_login: 小程序账号已绑定但关联用户不存在时应抛出 ValueError"""
        from unittest.mock import AsyncMock
        from app.services.user_service import User
        from app.core.config import settings

        # 创建小程序账号但不创建关联用户（模拟用户数据异常）
        # app_id 必须与 settings.WX_APPID 一致，否则 wechat_login 查询不到
        miniapp = UserMiniappAccount(
            user_id=999999, app_id=settings.WX_APPID,
            openid="test_openid", session_key="test_session",
        )
        db_session.add(miniapp)
        await db_session.commit()
        user = User(db_session)
        # mock _code2session 返回匹配的 openid
        with patch.object(
            user, "_code2session",
            new=AsyncMock(return_value={"openid": "test_openid", "session_key": "new_session"}),
        ):
            with pytest.raises(ValueError, match="用户数据异常"):
                await user.wechat_login("test_code")


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
                ["08:00"], [],
            )

    @pytest.mark.asyncio
    async def test_create_plan_hh_mm_ss_format(self, db_session, test_user):
        """create_plan: HH:MM:SS 格式时间应正确解析"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        service = PlanService(db_session)
        plan = await service.create_plan(
            test_user.id, "测试计划", "", date(2026, 1, 1), date(2026, 12, 31),
            ["08:00:30"], [znx_channel.id],
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
            ["08:00"], [znx_channel.id],
        )
        with pytest.raises(ValueError, match="至少选择一个通知方式"):
            await service.update_plan(
                plan.id, test_user.id, "更新", "", date(2026, 1, 1), date(2026, 12, 31),
                ["08:00"], [],
            )

    @pytest.mark.asyncio
    async def test_update_plan_invalid_channels(self, db_session, test_user):
        """update_plan: 包含无效渠道应抛出 ValueError"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        service = PlanService(db_session)
        plan = await service.create_plan(
            test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
            ["08:00"], [znx_channel.id],
        )
        with pytest.raises(ValueError, match="包含无效或非本用户的通知渠道"):
            await service.update_plan(
                plan.id, test_user.id, "更新", "", date(2026, 1, 1), date(2026, 12, 31),
                ["08:00"], [999999],
            )

    @pytest.mark.asyncio
    async def test_update_plan_hh_mm_ss_format(self, db_session, test_user):
        """update_plan: HH:MM:SS 格式时间应正确解析"""
        znx_channel = await NotificationChannelService(db_session).ensure_znx_channel(test_user.id)
        service = PlanService(db_session)
        plan = await service.create_plan(
            test_user.id, "计划", "", date(2026, 1, 1), date(2026, 12, 31),
            ["08:00"], [znx_channel.id],
        )
        updated = await service.update_plan(
            plan.id, test_user.id, "更新", "", date(2026, 1, 1), date(2026, 12, 31),
            ["20:00:45"], [znx_channel.id],
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
            ["08:00"], [znx_channel.id], status=1,
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
            ["08:00"], [znx_channel.id],
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
            ["08:00"], [znx_channel.id],
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
            ["08:00"], [znx_channel.id],
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
            ["08:00"], [znx_channel.id],
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
            ["08:00"], [znx_channel.id],
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


# ===== email_service.py 覆盖 =====


class TestEmailServiceCoverage:
    """Email 服务异常分支覆盖"""

    def test_send_verification_code_other_exception(self):
        """send_verification_code: 非 SMTPAuthenticationError 异常应抛出 RuntimeError"""
        from app.services.email_service import Email
        with patch("smtplib.SMTP_SSL", side_effect=Exception("连接失败")):
            email = Email()
            with pytest.raises(RuntimeError, match="邮件发送失败"):
                email.send_verification_code("to@example.com", "123456")


# ===== notification_channel_service.py 覆盖 =====


class TestNotificationChannelServiceCoverage:
    """NotificationChannelService 异常分支覆盖"""

    @pytest.mark.asyncio
    async def test_delete_channel_no_permission(self, db_session, test_user):
        """delete_channel: 删除他人渠道应抛出 ValueError"""
        # 创建另一个用户及其邮件渠道
        other_user = UserModel(
            username="其他", email="other@example.com",
            password_hash=Security.hash_password("Test1234!"),
            avatar_url="hei", signature="签名", status=1,
        )
        db_session.add(other_user)
        await db_session.flush()
        other_channel = NotificationChannel(
            user_id=other_user.id, channel_type=CHANNEL_TYPE_EMAIL,
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
