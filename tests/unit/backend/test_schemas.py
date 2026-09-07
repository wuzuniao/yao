"""
Pydantic Schema 校验单元测试
--------------------------------------------------------------------------
覆盖 plan、checkin_record、notification_channel、notification_log
请求 Schema 的字段校验逻辑（用户 Schema 已随用户模块迁移至 auth 服务）
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


class TestCreatePlanSchema:
    """创建计划请求 Schema"""

    @pytest.mark.unit
    def test_valid(self):
        from datetime import date

        p = CreatePlan(
            name="吃药计划",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            notification_times=[{"time": "08:00"}, {"time": "20:00"}],
            channel_ids=[1],
        )
        assert p.name == "吃药计划"
        assert p.status == 1
        assert p.priority == 3
        # notification_times 为 NotificationTimeItem 对象数组，未传字段取默认值
        assert [nt.time for nt in p.notification_times] == ["08:00", "20:00"]
        assert p.notification_times[0].followup_count == 3

    @pytest.mark.unit
    def test_empty_name(self):
        with pytest.raises(ValidationError):
            CreatePlan(
                name="  ",
                start_date="2026-01-01",
                end_date="2026-12-31",
                notification_times=[{"time": "08:00"}],
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
                notification_times=[{"time": "25:00"}],
                channel_ids=[1],
            )

    @pytest.mark.unit
    def test_empty_channel_ids(self):
        with pytest.raises(ValidationError):
            CreatePlan(
                name="计划",
                start_date="2026-01-01",
                end_date="2026-12-31",
                notification_times=[{"time": "08:00"}],
                channel_ids=[],
            )

    @pytest.mark.unit
    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            CreatePlan(
                name="计划",
                start_date="2026-01-01",
                end_date="2026-12-31",
                notification_times=[{"time": "08:00"}],
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
                notification_times=[{"time": "08:00"}],
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
