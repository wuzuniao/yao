"""
Pydantic Schema 校验单元测试
--------------------------------------------------------------------------
覆盖 user、plan、checkin_record、notification_channel、notification_log
所有请求 Schema 的字段校验逻辑
"""
import pytest
from pydantic import ValidationError

from app.schemas.checkin_record import CreateCheckin
from app.schemas.notification_channel import (
    CHANNEL_TYPE_EMAIL,
    CHANNEL_TYPE_ZNX,
    CreateEmailChannel,
    DeleteChannel,
    UpdateEmailChannel,
)
from app.schemas.notification_log import LOG_STATUS_UNREAD, MarkRead
from app.schemas.plan import CreatePlan
from app.schemas.user import (
    BindEmail,
    ChangeEmail,
    ChangePassword,
    LoginUser,
    RegisterUser,
    ResetPassword,
    SendChangeEmailNewCode,
    UpdateAvatar,
    UpdateSignature,
    UpdateUsername,
    WeChatLogin,
)


class TestRegisterUserSchema:
    """注册请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        user = RegisterUser(
            username="测试用户", password="Abc1234!", email="test@example.com", code="123456"
        )
        assert user.username == "测试用户"

    @pytest.mark.unit
    def test_invalid_username(self):
        with pytest.raises(ValidationError):
            RegisterUser(
                username="a", password="Abc1234!", email="test@example.com", code="123456"
            )

    @pytest.mark.unit
    def test_invalid_password(self):
        with pytest.raises(ValidationError):
            RegisterUser(
                username="testuser", password="123", email="test@example.com", code="123456"
            )

    @pytest.mark.unit
    def test_invalid_code(self):
        with pytest.raises(ValidationError):
            RegisterUser(
                username="testuser", password="Abc1234!", email="test@example.com", code="abc"
            )

    @pytest.mark.unit
    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterUser(
                username="testuser", password="Abc1234!", email="notanemail", code="123456"
            )


class TestLoginUserSchema:
    """登录请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        user = LoginUser(username="testuser", password="Abc1234!")
        assert user.username == "testuser"

    @pytest.mark.unit
    def test_empty_username(self):
        with pytest.raises(ValidationError):
            LoginUser(username="  ", password="Abc1234!")

    @pytest.mark.unit
    def test_empty_password(self):
        with pytest.raises(ValidationError):
            LoginUser(username="testuser", password="")


class TestResetPasswordSchema:
    """重置密码请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        r = ResetPassword(
            email="test@example.com", code="123456", new_password="Abc1234!"
        )
        assert r.code == "123456"

    @pytest.mark.unit
    def test_invalid_code(self):
        with pytest.raises(ValidationError):
            ResetPassword(
                email="test@example.com", code="abc", new_password="Abc1234!"
            )

    @pytest.mark.unit
    def test_invalid_password(self):
        with pytest.raises(ValidationError):
            ResetPassword(
                email="test@example.com", code="123456", new_password="123"
            )


class TestChangePasswordSchema:
    """修改密码请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        r = ChangePassword(old_password="Old1234!", new_password="New1234!")
        assert r.new_password == "New1234!"

    @pytest.mark.unit
    def test_weak_new_password(self):
        with pytest.raises(ValidationError):
            ChangePassword(old_password="Old1234!", new_password="123")


class TestUpdateSignatureSchema:
    """更新签名请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        r = UpdateSignature(signature="这是签名")
        assert r.signature == "这是签名"

    @pytest.mark.unit
    def test_too_long(self):
        with pytest.raises(ValidationError):
            UpdateSignature(signature="a" * 71)


class TestUpdateAvatarSchema:
    """更新头像请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        r = UpdateAvatar(avatar_url="hei")
        assert r.avatar_url == "hei"

    @pytest.mark.unit
    def test_empty(self):
        with pytest.raises(ValidationError):
            UpdateAvatar(avatar_url="  ")


class TestUpdateUsernameSchema:
    """更新用户名请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        r = UpdateUsername(new_username="新用户名")
        assert r.new_username == "新用户名"

    @pytest.mark.unit
    def test_invalid(self):
        with pytest.raises(ValidationError):
            UpdateUsername(new_username="a")


class TestChangeEmailSchema:
    """修改邮箱请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        r = ChangeEmail(
            old_code="123456", new_email="new@example.com", new_code="654321"
        )
        assert r.old_code == "123456"

    @pytest.mark.unit
    def test_invalid_codes(self):
        with pytest.raises(ValidationError):
            ChangeEmail(
                old_code="abc", new_email="new@example.com", new_code="654321"
            )


class TestBindEmailSchema:
    """绑定邮箱请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        r = BindEmail(new_email="test@example.com", new_code="123456")
        assert r.new_code == "123456"

    @pytest.mark.unit
    def test_invalid_code(self):
        with pytest.raises(ValidationError):
            BindEmail(new_email="test@example.com", new_code="abc")


class TestWeChatLoginSchema:
    """微信登录请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        r = WeChatLogin(code="wx_code_123")
        assert r.code == "wx_code_123"

    @pytest.mark.unit
    def test_empty_code(self):
        with pytest.raises(ValidationError):
            WeChatLogin(code="  ")


class TestCreatePlanSchema:
    """创建计划请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        from datetime import date

        p = CreatePlan(
            name="吃药计划",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            notification_times=["08:00", "20:00"],
            channel_ids=[1],
        )
        assert p.name == "吃药计划"
        assert p.status == 1
        assert p.priority == 3

    @pytest.mark.unit
    def test_empty_name(self):
        with pytest.raises(ValidationError):
            CreatePlan(
                name="  ",
                start_date="2026-01-01",
                end_date="2026-12-31",
                notification_times=["08:00"],
                channel_ids=[1],
            )

    @pytest.mark.unit
    def test_empty_notification_times(self):
        with pytest.raises(ValidationError):
            CreatePlan(
                name="计划",
                start_date="2026-01-01",
                end_date="2026-12-31",
                notification_times=[],
                channel_ids=[1],
            )

    @pytest.mark.unit
    def test_invalid_time_format(self):
        with pytest.raises(ValidationError):
            CreatePlan(
                name="计划",
                start_date="2026-01-01",
                end_date="2026-12-31",
                notification_times=["25:00"],
                channel_ids=[1],
            )

    @pytest.mark.unit
    def test_empty_channel_ids(self):
        with pytest.raises(ValidationError):
            CreatePlan(
                name="计划",
                start_date="2026-01-01",
                end_date="2026-12-31",
                notification_times=["08:00"],
                channel_ids=[],
            )

    @pytest.mark.unit
    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            CreatePlan(
                name="计划",
                start_date="2026-01-01",
                end_date="2026-12-31",
                notification_times=["08:00"],
                channel_ids=[1],
                status=5,
            )

    @pytest.mark.unit
    def test_invalid_priority(self):
        with pytest.raises(ValidationError):
            CreatePlan(
                name="计划",
                start_date="2026-01-01",
                end_date="2026-12-31",
                notification_times=["08:00"],
                channel_ids=[1],
                priority=10,
            )


class TestCreateCheckinSchema:
    """打卡请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        c = CreateCheckin(
            plan_id=1, plan_time_id=2, actual_time="2026-07-01T08:30:00"
        )
        assert c.plan_id == 1

    @pytest.mark.unit
    def test_invalid_plan_id(self):
        with pytest.raises(ValidationError):
            CreateCheckin(plan_id=0, plan_time_id=2, actual_time="2026-07-01T08:30:00")

    @pytest.mark.unit
    def test_invalid_plan_time_id(self):
        with pytest.raises(ValidationError):
            CreateCheckin(plan_id=1, plan_time_id=0, actual_time="2026-07-01T08:30:00")

    @pytest.mark.unit
    def test_empty_actual_time(self):
        with pytest.raises(ValidationError):
            CreateCheckin(plan_id=1, plan_time_id=2, actual_time="")

    @pytest.mark.unit
    def test_invalid_time_format(self):
        with pytest.raises(ValidationError):
            CreateCheckin(plan_id=1, plan_time_id=2, actual_time="not-a-time")


class TestNotificationChannelSchemas:
    """通知渠道 Schema"""

    @pytest.mark.unit
    def test_create_email_channel_valid(self):
        c = CreateEmailChannel(
            smtp_host="smtp.example.com",
            smtp_port=465,
            email="test@example.com",
            password="password123",
        )
        assert c.enabled is True

    @pytest.mark.unit
    def test_create_email_channel_invalid_port(self):
        with pytest.raises(ValidationError):
            CreateEmailChannel(
                smtp_host="smtp.example.com",
                smtp_port=99999,
                email="test@example.com",
                password="password123",
            )

    @pytest.mark.unit
    def test_create_email_channel_empty_password(self):
        with pytest.raises(ValidationError):
            CreateEmailChannel(
                smtp_host="smtp.example.com",
                smtp_port=465,
                email="test@example.com",
                password="",
            )

    @pytest.mark.unit
    def test_create_email_channel_invalid_email(self):
        with pytest.raises(ValidationError):
            CreateEmailChannel(
                smtp_host="smtp.example.com",
                smtp_port=465,
                email="notanemail",
                password="password123",
            )

    @pytest.mark.unit
    def test_update_email_channel_valid(self):
        c = UpdateEmailChannel(
            channel_id=1,
            smtp_host="smtp.example.com",
            smtp_port=465,
            email="test@example.com",
        )
        assert c.password == ""

    @pytest.mark.unit
    def test_update_email_channel_invalid_id(self):
        with pytest.raises(ValidationError):
            UpdateEmailChannel(
                channel_id=0,
                smtp_host="smtp.example.com",
                smtp_port=465,
                email="test@example.com",
            )

    @pytest.mark.unit
    def test_delete_channel_valid(self):
        d = DeleteChannel(channel_id=1)
        assert d.channel_id == 1

    @pytest.mark.unit
    def test_delete_channel_invalid_id(self):
        with pytest.raises(ValidationError):
            DeleteChannel(channel_id=0)

    @pytest.mark.unit
    def test_channel_type_constants(self):
        assert CHANNEL_TYPE_ZNX == "站内信"
        assert CHANNEL_TYPE_EMAIL == "邮件"


class TestNotificationLogSchema:
    """通知日志 Schema"""

    @pytest.mark.unit
    def test_mark_read_valid(self):
        m = MarkRead(log_id=1)
        assert m.log_id == 1

    @pytest.mark.unit
    def test_mark_read_invalid_id(self):
        with pytest.raises(ValidationError):
            MarkRead(log_id=0)

    @pytest.mark.unit
    def test_status_constants(self):
        assert LOG_STATUS_UNREAD == 2
