"""
端到端测试：完整用户流程
--------------------------------------------------------------------------
模拟真实用户从注册到使用各功能的完整操作路径，
验证多个 API 接口协同工作时的数据一致性和业务正确性。
"""
import pytest

from app.services.user_service import _verification_codes
from app.utils.timezone import today_shanghai

API_PREFIX = "/api/v1/users"


# =============================================================================
# 辅助函数
# =============================================================================


def _get_code(email: str, purpose: str) -> str:
    """从内存中获取验证码"""
    key = f"{email}:{purpose}"
    record = _verification_codes.get(key)
    assert record is not None, f"验证码不存在：{key}"
    return record[0]


async def _get_channel_id(auth_client) -> int:
    """获取当前用户第一个通知渠道 ID（站内信）"""
    resp = await auth_client.get("/api/v1/notification-channels/list")
    assert resp.status_code == 200
    return resp.json()["data"][0]["id"]


# =============================================================================
# 测试 1：完整注册到登录流程
# =============================================================================


class TestE2ERegistrationLogin:
    """完整注册到登录流程：发送验证码 → 注册 → 用户名登录 → 邮箱登录 → 查询用户信息"""

    @pytest.mark.e2e
    async def test_registration_login_full_flow(self, client):
        email = "newuser@example.com"

        # 1. 发送注册验证码
        resp = await client.post(f"{API_PREFIX}/send-code", json={"email": email})
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

        # 2. 从内存中获取验证码（绕过邮件发送）
        code = _get_code(email, "register")

        # 3. 注册
        resp = await client.post(
            f"{API_PREFIX}/register",
            json={
                "username": "新用户",
                "password": "NewPass123!",
                "email": email,
                "code": code,
            },
        )
        assert resp.status_code == 200
        register_data = resp.json()["data"]
        assert register_data["username"] == "新用户"
        assert register_data["email"] == email

        # 4. 验证注册响应包含 access_token
        assert register_data["access_token"]

        # 5. 使用用户名登录
        resp = await client.post(
            f"{API_PREFIX}/login",
            json={"username": "新用户", "password": "NewPass123!"},
        )
        assert resp.status_code == 200

        # 6. 验证登录响应包含 access_token
        assert resp.json()["data"]["access_token"]

        # 7. 使用邮箱登录
        resp = await client.post(
            f"{API_PREFIX}/login",
            json={"username": email, "password": "NewPass123!"},
        )
        assert resp.status_code == 200

        # 8. 验证邮箱登录响应
        assert resp.json()["data"]["access_token"]

        # 9. 携带注册返回的 token 查询用户信息
        token = register_data["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        resp = await client.get(f"{API_PREFIX}/info")
        assert resp.status_code == 200

        # 10. 验证用户信息与注册数据一致
        user_info = resp.json()["data"]
        assert user_info["username"] == "新用户"
        assert user_info["email"] == email


# =============================================================================
# 测试 2：完整密码重置流程
# =============================================================================


class TestE2EPasswordReset:
    """完整密码重置流程：发送重置验证码 → 重置密码 → 新密码登录 → 旧密码登录失败"""

    @pytest.mark.e2e
    async def test_password_reset_full_flow(self, client, test_user):
        email = "test@example.com"

        # 1. 发送重置验证码（test_user 的邮箱已注册）
        resp = await client.post(
            f"{API_PREFIX}/send-reset-code", json={"email": email}
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

        # 2. 从内存中获取验证码
        code = _get_code(email, "reset")

        # 3. 重置密码
        resp = await client.post(
            f"{API_PREFIX}/reset-password",
            json={
                "email": email,
                "code": code,
                "new_password": "ResetPass123!",
            },
        )
        assert resp.status_code == 200

        # 4. 验证响应包含 access_token
        assert resp.json()["data"]["access_token"]

        # 5. 使用新密码登录应成功
        resp = await client.post(
            f"{API_PREFIX}/login",
            json={"username": "测试用户", "password": "ResetPass123!"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

        # 6. 使用旧密码登录应失败
        resp = await client.post(
            f"{API_PREFIX}/login",
            json={"username": "测试用户", "password": "Test1234!"},
        )
        assert resp.status_code == 400
        assert "密码错误" in resp.json()["detail"]


# =============================================================================
# 测试 3：完整计划管理流程
# =============================================================================


class TestE2EPlanManagement:
    """完整计划管理流程：列表(空) → 创建 → 列表(1条) → 更新 → 验证 → 删除 → 列表(空)"""

    @pytest.mark.e2e
    async def test_plan_management_full_flow(self, auth_client):
        # 1. 查询计划列表（应为空）
        resp = await auth_client.get("/api/v1/plans/list")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

        # 2. 获取通知渠道 ID
        channel_id = await _get_channel_id(auth_client)

        # 3. 创建计划
        resp = await auth_client.post(
            "/api/v1/plans",
            json={
                "name": "晨间打卡",
                "remark": "每天早起打卡",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "notification_times": ["08:00", "20:00"],
                "channel_ids": [channel_id],
                "status": 1,
                "priority": 3,
            },
        )
        assert resp.status_code == 200
        plan_id = resp.json()["data"]["id"]

        # 4. 查询计划列表（应有 1 条）
        resp = await auth_client.get("/api/v1/plans/list")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

        # 5. 更新计划名称
        resp = await auth_client.put(
            f"/api/v1/plans/{plan_id}",
            json={
                "name": "更新后的打卡计划",
                "remark": "更新后的备注",
                "start_date": "2026-02-01",
                "end_date": "2026-11-30",
                "notification_times": ["09:00"],
                "channel_ids": [channel_id],
                "status": 1,
                "priority": 2,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "更新后的打卡计划"

        # 6. 查询计划列表（验证更新后的名称）
        resp = await auth_client.get("/api/v1/plans/list")
        assert resp.status_code == 200
        plans = resp.json()["data"]
        assert len(plans) == 1
        assert plans[0]["name"] == "更新后的打卡计划"

        # 7. 删除计划
        resp = await auth_client.delete(f"/api/v1/plans/{plan_id}")
        assert resp.status_code == 200

        # 8. 查询计划列表（应恢复为空）
        resp = await auth_client.get("/api/v1/plans/list")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


# =============================================================================
# 测试 4：完整打卡流程
# =============================================================================


class TestE2ECheckin:
    """完整打卡流程：创建计划 → 打卡 → 今日记录 → 按计划查 → 月度日历 → 日详情"""

    @pytest.mark.e2e
    async def test_checkin_full_flow(self, auth_client):
        today = today_shanghai()

        # 1. 获取通知渠道 ID
        channel_id = await _get_channel_id(auth_client)

        # 2. 创建带通知时间点的计划
        resp = await auth_client.post(
            "/api/v1/plans",
            json={
                "name": "打卡测试计划",
                "remark": "测试备注",
                "start_date": f"{today.year}-01-01",
                "end_date": f"{today.year}-12-31",
                "notification_times": ["08:00", "20:00"],
                "channel_ids": [channel_id],
                "status": 1,
                "priority": 3,
            },
        )
        assert resp.status_code == 200
        plan_data = resp.json()["data"]
        plan_id = plan_data["id"]
        time_ids = [nt["id"] for nt in plan_data["notification_times"]]

        # 3. 创建打卡记录（今日 08:30 打卡，匹配 08:00 提醒时间）
        actual_time = f"{today.isoformat()}T08:30:00"
        resp = await auth_client.post(
            "/api/v1/checkins",
            json={
                "plan_id": plan_id,
                "plan_time_id": time_ids[0],
                "actual_time": actual_time,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

        # 4. 查询今日打卡记录（验证打卡已生成）
        resp = await auth_client.get("/api/v1/checkins/today")
        assert resp.status_code == 200
        today_records = resp.json()["data"]
        assert len(today_records) >= 1
        assert today_records[0]["plan_id"] == plan_id
        assert today_records[0]["plan_time_id"] == time_ids[0]

        # 5. 按计划查询今日打卡（验证 checked_time_ids 包含已打卡时间点）
        resp = await auth_client.get(f"/api/v1/checkins/today/{plan_id}")
        assert resp.status_code == 200
        plan_today = resp.json()["data"]
        assert time_ids[0] in plan_today["checked_time_ids"]
        assert len(plan_today["records"]) >= 1

        # 6. 查询月度打卡日历（验证今日已打卡）
        resp = await auth_client.get(
            f"/api/v1/checkins/month?year={today.year}&month={today.month}"
        )
        assert resp.status_code == 200
        assert today.day in resp.json()["data"]["checked_days"]

        # 7. 查询日打卡详情（验证计划标记为已打卡）
        resp = await auth_client.get(
            f"/api/v1/checkins/day?date={today.isoformat()}"
        )
        assert resp.status_code == 200
        day_detail = resp.json()["data"]
        assert len(day_detail) >= 1
        checked_items = [d for d in day_detail if d["checked"]]
        assert len(checked_items) >= 1
        assert checked_items[0]["first_actual_time"] is not None


# =============================================================================
# 测试 5：完整通知渠道管理流程
# =============================================================================


class TestE2ENotificationChannel:
    """完整通知渠道管理流程：列表(1) → 创建邮件 → 列表(2) → 更新 → 列表(验证) → 删除 → 列表(1)"""

    @pytest.mark.e2e
    async def test_notification_channel_full_flow(self, auth_client):
        # 1. 查询渠道列表（应有 1 个：站内信）
        resp = await auth_client.get("/api/v1/notification-channels/list")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
        assert resp.json()["data"][0]["channel_type"] == "站内信"

        # 2. 创建邮件渠道
        resp = await auth_client.post(
            "/api/v1/notification-channels/email",
            json={
                "smtp_host": "smtp.example.com",
                "smtp_port": 465,
                "email": "sender@example.com",
                "password": "mypassword",
                "enabled": True,
            },
        )
        assert resp.status_code == 200
        channel_id = resp.json()["data"]["id"]

        # 3. 查询渠道列表（应有 2 个）
        resp = await auth_client.get("/api/v1/notification-channels/list")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

        # 4. 更新邮件渠道（修改 SMTP 主机）
        resp = await auth_client.put(
            "/api/v1/notification-channels/email",
            json={
                "channel_id": channel_id,
                "smtp_host": "smtp.updated.com",
                "smtp_port": 587,
                "email": "updated@example.com",
                "password": "newpassword",
                "enabled": False,
            },
        )
        assert resp.status_code == 200
        cfg = resp.json()["data"]["email_config"]
        assert cfg["smtp_host"] == "smtp.updated.com"
        assert cfg["smtp_port"] == 587

        # 5. 查询渠道列表（验证更新后仍为 2 个）
        resp = await auth_client.get("/api/v1/notification-channels/list")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

        # 6. 删除邮件渠道（httpx delete 不支持 json，使用 request 方法）
        resp = await auth_client.request(
            "DELETE",
            "/api/v1/notification-channels",
            json={"channel_id": channel_id},
        )
        assert resp.status_code == 200

        # 7. 查询渠道列表（应恢复为 1 个，仅剩站内信）
        resp = await auth_client.get("/api/v1/notification-channels/list")
        assert resp.status_code == 200
        channels = resp.json()["data"]
        assert len(channels) == 1
        assert channels[0]["channel_type"] == "站内信"


# =============================================================================
# 测试 6：完整账号生命周期流程
# =============================================================================


class TestE2EAccountLifecycle:
    """完整账号生命周期流程：预约删除 → 取消 → 更新签名/头像/用户名 → 验证"""

    @pytest.mark.e2e
    async def test_account_lifecycle_full_flow(self, auth_client):
        # 1. 查询用户信息（初始 status=1）
        resp = await auth_client.get(f"{API_PREFIX}/info")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == 1

        # 2. 预约删除账号
        resp = await auth_client.post(f"{API_PREFIX}/schedule-deletion", json={})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == 0

        # 3. 查询用户信息（status 已变为 0）
        resp = await auth_client.get(f"{API_PREFIX}/info")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == 0

        # 4. 取消删除
        resp = await auth_client.post(f"{API_PREFIX}/cancel-deletion", json={})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == 1

        # 5. 查询用户信息（status 恢复为 1）
        resp = await auth_client.get(f"{API_PREFIX}/info")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == 1

        # 6. 更新签名
        resp = await auth_client.put(
            f"{API_PREFIX}/update-signature",
            json={"signature": "生命周期新签名"},
        )
        assert resp.status_code == 200

        # 7. 更新头像
        resp = await auth_client.put(
            f"{API_PREFIX}/update-avatar",
            json={"avatar_url": "new-avatar"},
        )
        assert resp.status_code == 200

        # 8. 更新用户名
        resp = await auth_client.put(
            f"{API_PREFIX}/update-username",
            json={"new_username": "生命周期用户"},
        )
        assert resp.status_code == 200

        # 9. 查询用户信息（验证所有更新已生效）
        resp = await auth_client.get(f"{API_PREFIX}/info")
        assert resp.status_code == 200
        user_info = resp.json()["data"]
        assert user_info["signature"] == "生命周期新签名"
        assert user_info["avatar_url"] == "new-avatar"
        assert user_info["username"] == "生命周期用户"


# =============================================================================
# 测试 7：完整邮箱修改流程
# =============================================================================


class TestE2EEmailChange:
    """完整邮箱修改流程：发送旧邮箱验证码 → 发送新邮箱验证码 → 修改邮箱 → 验证"""

    @pytest.mark.e2e
    async def test_email_change_full_flow(self, auth_client, test_user):
        old_email = test_user.email
        new_email = "newemail@example.com"

        # 1. 发送旧邮箱验证码
        resp = await auth_client.post(
            f"{API_PREFIX}/send-change-email-old-code", json={}
        )
        assert resp.status_code == 200

        # 2. 从内存中获取旧邮箱验证码
        old_code = _get_code(old_email, "change_old")

        # 3. 发送新邮箱验证码
        resp = await auth_client.post(
            f"{API_PREFIX}/send-change-email-new-code",
            json={"new_email": new_email, "allow_existing": False},
        )
        assert resp.status_code == 200

        # 4. 从内存中获取新邮箱验证码
        new_code = _get_code(new_email, "change_new")

        # 5. 修改邮箱
        resp = await auth_client.put(
            f"{API_PREFIX}/change-email",
            json={
                "old_code": old_code,
                "new_email": new_email,
                "new_code": new_code,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == new_email

        # 6. 查询用户信息（验证邮箱已变更为新邮箱）
        resp = await auth_client.get(f"{API_PREFIX}/info")
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == new_email


# =============================================================================
# 测试 8：完整密码修改流程
# =============================================================================


class TestE2EPasswordChange:
    """完整密码修改流程：修改密码 → 旧密码登录失败 → 新密码登录成功"""

    @pytest.mark.e2e
    async def test_password_change_full_flow(self, auth_client, client, test_user):
        # 1. 修改密码
        resp = await auth_client.put(
            f"{API_PREFIX}/change-password",
            json={
                "old_password": "Test1234!",
                "new_password": "ChangedPass123!",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

        # 2. 使用旧密码登录应失败
        resp = await client.post(
            f"{API_PREFIX}/login",
            json={"username": "测试用户", "password": "Test1234!"},
        )
        assert resp.status_code == 400
        assert "密码错误" in resp.json()["detail"]

        # 3. 使用新密码登录应成功
        resp = await client.post(
            f"{API_PREFIX}/login",
            json={"username": "测试用户", "password": "ChangedPass123!"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["access_token"]
