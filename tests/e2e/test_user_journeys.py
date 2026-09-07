"""
端到端测试：完整业务流程
--------------------------------------------------------------------------
模拟真实用户使用计划/打卡/通知渠道功能的完整操作路径，
验证多个 API 接口协同工作时的数据一致性和业务正确性。
（认证类旅程——注册/登录/密码/邮箱/账号生命周期——已迁 auth 服务仓库；
 本文件全部旅程使用测试私钥直签的 access_token）
"""
import pytest

from app.utils.timezone import today_shanghai


# =============================================================================
# 辅助函数
# =============================================================================


async def _get_channel_id(auth_client) -> int:
    """获取当前用户第一个通知渠道 ID（站内信，list_by_user 懒创建）"""
    resp = await auth_client.get("/api/v1/notification-channels/list")
    assert resp.status_code == 200
    return resp.json()["data"][0]["id"]


# =============================================================================
# 测试 1：完整计划管理流程
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
                "notification_times": [{"time": "08:00"}, {"time": "20:00"}],
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
                "notification_times": [{"time": "09:00"}],
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
# 测试 2：完整打卡流程
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
                "notification_times": [{"time": "08:00"}, {"time": "20:00"}],
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
# 测试 3：完整通知渠道管理流程
# =============================================================================


class TestE2ENotificationChannel:
    """完整通知渠道管理流程：列表(1) → 创建邮件 → 列表(2) → 更新 → 列表(验证) → 删除 → 列表(1)"""

    @pytest.mark.e2e
    async def test_notification_channel_full_flow(self, auth_client):
        # 1. 查询渠道列表（应有 1 个：站内信，由 list_by_user 懒创建）
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
