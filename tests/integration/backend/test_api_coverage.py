"""
集成测试补充：覆盖 API 层异常分支与端点
--------------------------------------------------------------------------
覆盖目标：
- main.py: root/health 端点
- users.py: RuntimeError/ValueError/Exception 分支（邮件发送失败、用户不存在、微信登录异常、JWT 配置异常）
- checkins.py: 时间格式错误、带时区时间转换
- notification_logs.py: read_all 失败分支
"""
from datetime import date, time as dt_time
from unittest.mock import patch

import pytest

from app.core.security import Security
from app.models.plan import CheckinPlan, PlanNotificationTime


# ===== main.py 端点 =====


class TestMainEndpoints:
    """main.py root/health 端点覆盖"""

    @pytest.mark.asyncio
    async def test_root(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ===== users.py 异常分支 =====


class TestUsersApiCoverage:
    """users.py API 异常分支覆盖"""

    @pytest.mark.asyncio
    async def test_register_runtime_error(self, client, mock_email_service):
        """register: 内部 RuntimeError 应返回 500"""
        with patch("app.services.user_service.User.register", side_effect=RuntimeError("内部错误")):
            resp = await client.post("/api/v1/users/register", json={
                "username": "新用户", "password": "Test1234!", "email": "new@example.com", "code": "123456"
            })
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_send_code_runtime_error(self, client, mock_email_service):
        """send_code: 邮件发送失败应返回 500"""
        mock_email_service.return_value.send_verification_code.side_effect = RuntimeError("发送失败")
        resp = await client.post("/api/v1/users/send-code", json={"email": "new@example.com"})
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_send_reset_code_runtime_error(self, client, test_user, mock_email_service):
        """send_reset_code: 邮件发送失败应返回 500"""
        mock_email_service.return_value.send_verification_code.side_effect = RuntimeError("发送失败")
        resp = await client.post("/api/v1/users/send-reset-code", json={"email": "test@example.com"})
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_send_change_email_old_code_value_error(self, client):
        """send_change_email_old_code: 用户不存在应返回 400"""
        token = Security.generate_token(999999)
        client.headers["Authorization"] = f"Bearer {token}"
        resp = await client.post("/api/v1/users/send-change-email-old-code", json={})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_send_change_email_old_code_runtime_error(self, auth_client, mock_email_service):
        """send_change_email_old_code: 邮件发送失败应返回 500"""
        mock_email_service.return_value.send_verification_code.side_effect = RuntimeError("发送失败")
        resp = await auth_client.post("/api/v1/users/send-change-email-old-code", json={})
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_send_change_email_new_code_runtime_error(self, auth_client, mock_email_service):
        """send_change_email_new_code: 邮件发送失败应返回 500"""
        mock_email_service.return_value.send_verification_code.side_effect = RuntimeError("发送失败")
        resp = await auth_client.post("/api/v1/users/send-change-email-new-code", json={
            "new_email": "new@example.com", "allow_existing": False
        })
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_change_email_runtime_error(self, auth_client):
        """change_email: 内部 RuntimeError 应返回 500"""
        with patch("app.services.user_service.User.change_email", side_effect=RuntimeError("内部错误")):
            resp = await auth_client.put("/api/v1/users/change-email", json={
                "old_code": "123456", "new_email": "new@example.com", "new_code": "654321"
            })
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_update_signature_user_not_found(self, client):
        """update_signature: 用户不存在应返回 400"""
        token = Security.generate_token(999999)
        client.headers["Authorization"] = f"Bearer {token}"
        resp = await client.put("/api/v1/users/update-signature", json={"signature": "新签名"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_update_avatar_user_not_found(self, client):
        """update_avatar: 用户不存在应返回 400"""
        token = Security.generate_token(999999)
        client.headers["Authorization"] = f"Bearer {token}"
        resp = await client.put("/api/v1/users/update-avatar", json={"avatar_url": "new"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_schedule_deletion_user_not_found(self, client):
        """schedule_deletion: 用户不存在应返回 400"""
        token = Security.generate_token(999999)
        client.headers["Authorization"] = f"Bearer {token}"
        resp = await client.post("/api/v1/users/schedule-deletion", json={})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_cancel_deletion_user_not_found(self, client):
        """cancel_deletion: 用户不存在应返回 400"""
        token = Security.generate_token(999999)
        client.headers["Authorization"] = f"Bearer {token}"
        resp = await client.post("/api/v1/users/cancel-deletion", json={})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_get_user_info_not_found(self, client):
        """get_user_info: 用户不存在应返回 404"""
        token = Security.generate_token(999999)
        client.headers["Authorization"] = f"Bearer {token}"
        resp = await client.get("/api/v1/users/info")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_login_jwt_config_error(self, client, test_user, mock_email_service):
        """login: JWT 配置异常（generate_token 抛出 ValueError）应返回 500"""
        with patch("app.api.v1.users.Security.generate_token", side_effect=ValueError("JWT配置异常")):
            resp = await client.post("/api/v1/users/login", json={
                "username": "test@example.com", "password": "Test1234!"
            })
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_wechat_login_value_error(self, client):
        """wechat_login: ValueError 应返回 400"""
        with patch("app.services.user_service.User.wechat_login", side_effect=ValueError("微信登录失败")):
            resp = await client.post("/api/v1/users/wechat-login", json={"code": "testcode"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_wechat_login_exception(self, client):
        """wechat_login: 其他异常应返回 500"""
        with patch("app.services.user_service.User.wechat_login", side_effect=Exception("网络异常")):
            resp = await client.post("/api/v1/users/wechat-login", json={"code": "testcode"})
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_wechat_login_success(self, client, mock_email_service):
        """wechat_login: 成功应返回 200（覆盖 return 分支）"""
        from unittest.mock import AsyncMock, MagicMock
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "微信用户"
        mock_user.signature = "签名"
        mock_user.avatar_url = "lan"
        mock_user.email = None
        mock_user.password_hash = None
        mock_user.status = 1
        with patch("app.services.user_service.User.wechat_login", new=AsyncMock(return_value=mock_user)):
            resp = await client.post("/api/v1/users/wechat-login", json={"code": "testcode"})
        assert resp.status_code == 200
        assert resp.json()["code"] == 0


# ===== checkins.py 异常分支 =====


class TestCheckinsApiCoverage:
    """checkins.py API 异常分支覆盖"""

    @pytest.mark.asyncio
    async def test_create_checkin_invalid_time_format(self, auth_client):
        """create_checkin: 时间格式错误应返回 422（CreateCheckin.validate_actual_time 拦截）"""
        resp = await auth_client.post("/api/v1/checkins", json={
            "plan_id": 1, "plan_time_id": 1, "actual_time": "invalid-format"
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_checkin_with_timezone(self, auth_client, db_session, test_user):
        """create_checkin: 带时区的时间应正常转换并打卡成功"""
        plan = CheckinPlan(
            user_id=test_user.id, name="测试计划",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status=1, priority=3,
        )
        db_session.add(plan)
        await db_session.flush()
        nt = PlanNotificationTime(plan_id=plan.id, notification_time=dt_time(14, 0))
        db_session.add(nt)
        await db_session.commit()
        await db_session.refresh(nt)
        # 发送带时区的时间字符串
        resp = await auth_client.post("/api/v1/checkins", json={
            "plan_id": plan.id, "plan_time_id": nt.id,
            "actual_time": "2026-07-02T14:30:00+08:00"
        })
        assert resp.status_code == 200


# ===== notification_logs.py 异常分支 =====


class TestNotificationLogsApiCoverage:
    """notification_logs.py API 异常分支覆盖"""

    @pytest.mark.asyncio
    async def test_read_all_failure(self, auth_client):
        """read_all: mark_all_as_read 抛出 ValueError 应返回 400"""
        with patch(
            "app.services.notification_log_service.NotificationLogService.mark_all_as_read",
            side_effect=ValueError("标记失败"),
        ):
            resp = await auth_client.request("PUT", "/api/v1/notification-logs/read-all")
        assert resp.status_code == 400
