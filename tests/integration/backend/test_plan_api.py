"""
计划管理 API 集成测试
- 计划的增删改查（CRUD）
- 通知时间点与关联渠道的维护
- 权限校验（仅能操作自己的计划）
"""
from datetime import date, time

import pytest

from app.core.security import Security
from app.models.notification_channel import NotificationChannel
from app.models.plan import (
    CheckinPlan,
    PlanNotificationChannel,
    PlanNotificationTime,
)
from app.models.user import User as UserModel


async def _get_channel_id(auth_client) -> int:
    """获取测试用户的第一个通知渠道ID（站内信）"""
    resp = await auth_client.get("/api/v1/notification-channels/list")
    assert resp.status_code == 200
    return resp.json()["data"][0]["id"]


async def _create_plan(auth_client, **overrides):
    """创建测试计划并返回响应数据"""
    payload = {
        "name": "测试计划",
        "remark": "测试备注",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "notification_times": ["08:00", "20:00"],
        "channel_ids": [],  # Will be filled with actual channel_id
        "status": 1,
        "priority": 3,
    }
    payload.update(overrides)
    # Get channel_id from notification-channels list
    resp = await auth_client.get("/api/v1/notification-channels/list")
    channel_id = resp.json()["data"][0]["id"]
    payload["channel_ids"] = [channel_id]
    resp = await auth_client.post("/api/v1/plans", json=payload)
    assert resp.status_code == 200
    return resp.json()["data"]


async def _create_other_user_plan(db_session) -> int:
    """创建另一个用户及其计划（直接操作数据库），返回计划ID

    用于测试“越权操作他人计划”场景：该计划属于非当前登录用户，
    通过 auth_client（当前用户 token）访问应被拒绝。
    """
    other_user = UserModel(
        username="其他用户",
        email="other@example.com",
        password_hash=Security.hash_password("Test1234!"),
        status=1,
    )
    db_session.add(other_user)
    await db_session.flush()

    other_channel = NotificationChannel(
        user_id=other_user.id,
        channel_type="站内信",
        channel_value=str(other_user.id),
        enabled=True,
    )
    db_session.add(other_channel)
    await db_session.flush()

    plan = CheckinPlan(
        user_id=other_user.id,
        name="其他用户的计划",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=1,
        priority=3,
    )
    db_session.add(plan)
    await db_session.flush()

    db_session.add(
        PlanNotificationTime(plan_id=plan.id, notification_time=time(8, 0))
    )
    db_session.add(
        PlanNotificationChannel(plan_id=plan.id, channel_id=other_channel.id)
    )
    await db_session.commit()
    return plan.id


class TestListPlans:
    """计划列表查询"""

    @pytest.mark.integration
    async def test_list_empty(self, auth_client):
        """无计划时返回空列表"""
        resp = await auth_client.get("/api/v1/plans/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"] == []

    @pytest.mark.integration
    async def test_list_after_create(self, auth_client):
        """创建后列表包含该计划"""
        plan_data = await _create_plan(auth_client)
        resp = await auth_client.get("/api/v1/plans/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]) == 1
        assert body["data"][0]["id"] == plan_data["id"]

    @pytest.mark.integration
    async def test_list_fields_match(self, auth_client):
        """列表中的计划字段与创建返回一致"""
        plan_data = await _create_plan(auth_client)
        resp = await auth_client.get("/api/v1/plans/list")
        list_plan = resp.json()["data"][0]
        assert list_plan["id"] == plan_data["id"]
        assert list_plan["name"] == plan_data["name"]
        assert list_plan["remark"] == plan_data["remark"]
        assert list_plan["start_date"] == plan_data["start_date"]
        assert list_plan["end_date"] == plan_data["end_date"]
        assert list_plan["status"] == plan_data["status"]
        assert list_plan["priority"] == plan_data["priority"]
        assert list_plan["notification_times"] == plan_data["notification_times"]
        assert list_plan["channel_ids"] == plan_data["channel_ids"]


class TestCreatePlan:
    """创建计划"""

    @pytest.mark.integration
    async def test_create_success(self, auth_client, test_user):
        """成功创建计划，验证所有字段"""
        data = await _create_plan(auth_client)
        assert data["id"] > 0
        assert data["user_id"] == test_user.id
        assert data["name"] == "测试计划"
        assert data["remark"] == "测试备注"
        assert data["start_date"] == "2026-01-01"
        assert data["end_date"] == "2026-12-31"
        assert data["status"] == 1
        assert data["priority"] == 3
        times = [t["notification_time"] for t in data["notification_times"]]
        assert set(times) == {"08:00", "20:00"}
        assert len(data["channel_ids"]) == 1
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    @pytest.mark.integration
    async def test_create_multiple_notification_times(self, auth_client):
        """创建含多个通知时间点的计划"""
        data = await _create_plan(
            auth_client,
            notification_times=["06:00", "12:00", "18:00", "22:00"],
        )
        times = [t["notification_time"] for t in data["notification_times"]]
        assert set(times) == {"06:00", "12:00", "18:00", "22:00"}

    @pytest.mark.integration
    async def test_create_invalid_channel_ids(self, auth_client):
        """channel_ids 不属于当前用户时返回 400"""
        channel_id = await _get_channel_id(auth_client)
        payload = {
            "name": "测试计划",
            "remark": "备注",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "notification_times": ["08:00"],
            "channel_ids": [channel_id + 999999],  # 不存在的渠道ID
            "status": 1,
            "priority": 3,
        }
        resp = await auth_client.post("/api/v1/plans", json=payload)
        assert resp.status_code == 400

    @pytest.mark.integration
    async def test_create_empty_channel_ids(self, auth_client):
        """channel_ids 为空时返回 422"""
        payload = {
            "name": "测试计划",
            "remark": "备注",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "notification_times": ["08:00"],
            "channel_ids": [],
            "status": 1,
            "priority": 3,
        }
        resp = await auth_client.post("/api/v1/plans", json=payload)
        assert resp.status_code == 422

    @pytest.mark.integration
    async def test_create_empty_notification_times(self, auth_client):
        """notification_times 为空时返回 422"""
        channel_id = await _get_channel_id(auth_client)
        payload = {
            "name": "测试计划",
            "remark": "备注",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "notification_times": [],
            "channel_ids": [channel_id],
            "status": 1,
            "priority": 3,
        }
        resp = await auth_client.post("/api/v1/plans", json=payload)
        assert resp.status_code == 422

    @pytest.mark.integration
    async def test_create_invalid_time_format(self, auth_client):
        """通知时间格式非法时返回 422"""
        channel_id = await _get_channel_id(auth_client)
        payload = {
            "name": "测试计划",
            "remark": "备注",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "notification_times": ["25:00"],  # 小时越界
            "channel_ids": [channel_id],
            "status": 1,
            "priority": 3,
        }
        resp = await auth_client.post("/api/v1/plans", json=payload)
        assert resp.status_code == 422

    @pytest.mark.integration
    async def test_create_invalid_status(self, auth_client):
        """status 值非法时返回 422"""
        channel_id = await _get_channel_id(auth_client)
        payload = {
            "name": "测试计划",
            "remark": "备注",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "notification_times": ["08:00"],
            "channel_ids": [channel_id],
            "status": 3,  # 只允许 0/1/2
            "priority": 3,
        }
        resp = await auth_client.post("/api/v1/plans", json=payload)
        assert resp.status_code == 422

    @pytest.mark.integration
    async def test_create_priority_out_of_range(self, auth_client):
        """priority 超出范围时返回 422"""
        channel_id = await _get_channel_id(auth_client)
        payload = {
            "name": "测试计划",
            "remark": "备注",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "notification_times": ["08:00"],
            "channel_ids": [channel_id],
            "status": 1,
            "priority": 8,  # 只允许 0-7
        }
        resp = await auth_client.post("/api/v1/plans", json=payload)
        assert resp.status_code == 422


class TestUpdatePlan:
    """更新计划"""

    @pytest.mark.integration
    async def test_update_success(self, auth_client):
        """成功更新计划，验证字段已更新"""
        plan_data = await _create_plan(auth_client)
        channel_id = await _get_channel_id(auth_client)
        payload = {
            "name": "更新后的计划",
            "remark": "更新后的备注",
            "start_date": "2026-02-01",
            "end_date": "2026-11-30",
            "notification_times": ["09:00"],
            "channel_ids": [channel_id],
            "status": 2,
            "priority": 1,
        }
        resp = await auth_client.put(
            f"/api/v1/plans/{plan_data['id']}", json=payload
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == plan_data["id"]
        assert data["name"] == "更新后的计划"
        assert data["remark"] == "更新后的备注"
        assert data["start_date"] == "2026-02-01"
        assert data["end_date"] == "2026-11-30"
        assert data["status"] == 2
        assert data["priority"] == 1
        times = [t["notification_time"] for t in data["notification_times"]]
        assert times == ["09:00"]

    @pytest.mark.integration
    async def test_update_notification_times(self, auth_client):
        """更新计划的通知时间点，旧时间点被替换"""
        plan_data = await _create_plan(auth_client)
        channel_id = await _get_channel_id(auth_client)
        payload = {
            "name": "测试计划",
            "remark": "测试备注",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "notification_times": ["10:00", "14:00", "18:00"],
            "channel_ids": [channel_id],
            "status": 1,
            "priority": 3,
        }
        resp = await auth_client.put(
            f"/api/v1/plans/{plan_data['id']}", json=payload
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        times = [t["notification_time"] for t in data["notification_times"]]
        assert set(times) == {"10:00", "14:00", "18:00"}
        # 确保旧时间点已被替换
        assert "08:00" not in times
        assert "20:00" not in times

    @pytest.mark.integration
    async def test_update_nonexistent_plan(self, auth_client):
        """更新不存在的计划返回 400"""
        channel_id = await _get_channel_id(auth_client)
        payload = {
            "name": "测试计划",
            "remark": "备注",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "notification_times": ["08:00"],
            "channel_ids": [channel_id],
            "status": 1,
            "priority": 3,
        }
        resp = await auth_client.put("/api/v1/plans/999999", json=payload)
        assert resp.status_code == 400

    @pytest.mark.integration
    async def test_update_other_user_plan(self, auth_client, db_session):
        """更新他人计划返回 400"""
        other_plan_id = await _create_other_user_plan(db_session)
        channel_id = await _get_channel_id(auth_client)
        payload = {
            "name": "篡改",
            "remark": "备注",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "notification_times": ["08:00"],
            "channel_ids": [channel_id],
            "status": 1,
            "priority": 3,
        }
        resp = await auth_client.put(
            f"/api/v1/plans/{other_plan_id}", json=payload
        )
        assert resp.status_code == 400


class TestDeletePlan:
    """删除计划"""

    @pytest.mark.integration
    async def test_delete_success(self, auth_client):
        """成功删除计划"""
        plan_data = await _create_plan(auth_client)
        resp = await auth_client.delete(f"/api/v1/plans/{plan_data['id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.integration
    async def test_delete_nonexistent_plan(self, auth_client):
        """删除不存在的计划返回 400"""
        resp = await auth_client.delete("/api/v1/plans/999999")
        assert resp.status_code == 400

    @pytest.mark.integration
    async def test_delete_other_user_plan(self, auth_client, db_session):
        """删除他人计划返回 400"""
        other_plan_id = await _create_other_user_plan(db_session)
        resp = await auth_client.delete(f"/api/v1/plans/{other_plan_id}")
        assert resp.status_code == 400

    @pytest.mark.integration
    async def test_list_after_delete(self, auth_client):
        """删除后列表不再包含该计划"""
        plan_data = await _create_plan(auth_client)
        await auth_client.delete(f"/api/v1/plans/{plan_data['id']}")
        resp = await auth_client.get("/api/v1/plans/list")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestPlanAuth:
    """计划接口鉴权"""

    @pytest.mark.integration
    async def test_unauthenticated_request(self, client):
        """未携带 token 访问返回 401"""
        resp = await client.get("/api/v1/plans/list")
        assert resp.status_code == 401
