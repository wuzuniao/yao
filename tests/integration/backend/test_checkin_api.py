"""
打卡记录 API 集成测试
- 打卡创建、查询
- 今日打卡记录、按计划查询
- 月度打卡日历、日打卡详情
- 权限校验与数据归属验证
"""
from datetime import date, time as dt_time

import pytest

from app.core.security import Security
from app.models.plan import CheckinPlan, PlanNotificationTime
from app.models.user import User as UserModel
from app.utils.timezone import today_shanghai


async def _create_plan_with_times(auth_client):
    """创建带通知时间点的计划，返回 (plan_id, plan_time_ids)"""
    # 获取站内信通知渠道 ID（test_user fixture 自动创建）
    resp = await auth_client.get("/api/v1/notification-channels/list")
    channel_id = resp.json()["data"][0]["id"]
    today = today_shanghai()
    resp = await auth_client.post("/api/v1/plans", json={
        "name": "打卡测试计划",
        "remark": "测试备注",
        "start_date": f"{today.year}-01-01",
        "end_date": f"{today.year}-12-31",
        "notification_times": ["08:00", "20:00"],
        "channel_ids": [channel_id],
        "status": 1,
        "priority": 3,
    })
    data = resp.json()["data"]
    plan_id = data["id"]
    time_ids = [nt["id"] for nt in data["notification_times"]]
    return plan_id, time_ids


async def _create_other_user_plan(db_session):
    """创建另一个用户的计划（直接通过 ORM 写入），返回 (plan_id, plan_time_ids)"""
    other_user = UserModel(
        username="其他用户",
        email="other@example.com",
        password_hash=Security.hash_password("Test1234!"),
        status=1,
    )
    db_session.add(other_user)
    await db_session.flush()

    today = today_shanghai()
    plan = CheckinPlan(
        user_id=other_user.id,
        name="其他用户的计划",
        start_date=date(today.year, 1, 1),
        end_date=date(today.year, 12, 31),
        status=1,
        priority=3,
    )
    db_session.add(plan)
    await db_session.flush()

    time_ids = []
    for h, m in [(8, 0), (20, 0)]:
        nt = PlanNotificationTime(
            plan_id=plan.id,
            notification_time=dt_time(h, m),
        )
        db_session.add(nt)
        await db_session.flush()
        time_ids.append(nt.id)

    await db_session.commit()
    return plan.id, time_ids


def _today_actual_time() -> str:
    """返回今日 08:30 的 ISO 时间字符串（无时区后缀）"""
    today_str = today_shanghai().isoformat()
    return f"{today_str}T08:30:00"


@pytest.mark.integration
class TestCheckinAPI:
    """打卡记录 API 集成测试"""

    # ==================== 创建打卡 ====================

    async def test_create_checkin_success(self, auth_client):
        """创建打卡成功：返回 200，验证记录字段完整性"""
        plan_id, time_ids = await _create_plan_with_times(auth_client)
        actual_time = _today_actual_time()

        resp = await auth_client.post("/api/v1/checkins", json={
            "plan_id": plan_id,
            "plan_time_id": time_ids[0],
            "actual_time": actual_time,
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["msg"] == "打卡成功"
        data = body["data"]
        assert "id" in data and data["id"] > 0
        assert data["user_id"] > 0
        assert data["plan_id"] == plan_id
        assert data["plan_time_id"] == time_ids[0]
        assert data["actual_time"] == actual_time

    async def test_create_checkin_nonexistent_plan(self, auth_client):
        """计划不存在：返回 400"""
        resp = await auth_client.post("/api/v1/checkins", json={
            "plan_id": 999999,
            "plan_time_id": 999999,
            "actual_time": _today_actual_time(),
        })

        assert resp.status_code == 400
        assert "计划不存在" in resp.json()["detail"]

    async def test_create_checkin_other_user_plan(self, auth_client, db_session):
        """计划属于其他用户：返回 400"""
        plan_id, time_ids = await _create_other_user_plan(db_session)

        resp = await auth_client.post("/api/v1/checkins", json={
            "plan_id": plan_id,
            "plan_time_id": time_ids[0],
            "actual_time": _today_actual_time(),
        })

        assert resp.status_code == 400
        assert "无权" in resp.json()["detail"]

    async def test_create_checkin_nonexistent_plan_time(self, auth_client):
        """通知时间点不存在：返回 400"""
        plan_id, _ = await _create_plan_with_times(auth_client)

        resp = await auth_client.post("/api/v1/checkins", json={
            "plan_id": plan_id,
            "plan_time_id": 999999,
            "actual_time": _today_actual_time(),
        })

        assert resp.status_code == 400
        assert "通知时间点不存在" in resp.json()["detail"]

    async def test_create_checkin_plan_time_not_belong_to_plan(self, auth_client):
        """通知时间点不属于该计划：返回 400"""
        plan_a_id, _ = await _create_plan_with_times(auth_client)
        _, time_b_ids = await _create_plan_with_times(auth_client)

        resp = await auth_client.post("/api/v1/checkins", json={
            "plan_id": plan_a_id,
            "plan_time_id": time_b_ids[0],
            "actual_time": _today_actual_time(),
        })

        assert resp.status_code == 400
        assert "不属于该计划" in resp.json()["detail"]

    async def test_create_checkin_invalid_time_format(self, auth_client):
        """打卡时间格式不正确：Pydantic schema 校验器优先拦截，返回 422"""
        plan_id, time_ids = await _create_plan_with_times(auth_client)

        resp = await auth_client.post("/api/v1/checkins", json={
            "plan_id": plan_id,
            "plan_time_id": time_ids[0],
            "actual_time": "not-a-valid-time",
        })

        # CreateCheckin schema 的 field_validator 先于端点逻辑校验时间格式，
        # 非法格式触发 Pydantic ValidationError，FastAPI 默认返回 422（非 400）
        assert resp.status_code == 422

    async def test_create_checkin_duplicate(self, auth_client):
        """重复打卡：系统允许，两次均返回 200 且生成不同记录"""
        plan_id, time_ids = await _create_plan_with_times(auth_client)
        payload = {
            "plan_id": plan_id,
            "plan_time_id": time_ids[0],
            "actual_time": _today_actual_time(),
        }

        resp1 = await auth_client.post("/api/v1/checkins", json=payload)
        resp2 = await auth_client.post("/api/v1/checkins", json=payload)

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["data"]["id"] != resp2.json()["data"]["id"]

    # ==================== 查询今日打卡 ====================

    async def test_list_today_checkins(self, auth_client):
        """查询今日打卡记录：返回已创建的记录列表"""
        plan_id, time_ids = await _create_plan_with_times(auth_client)
        await auth_client.post("/api/v1/checkins", json={
            "plan_id": plan_id,
            "plan_time_id": time_ids[0],
            "actual_time": _today_actual_time(),
        })

        resp = await auth_client.get("/api/v1/checkins/today")

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]) >= 1
        record = body["data"][0]
        assert record["plan_id"] == plan_id
        assert record["plan_time_id"] == time_ids[0]

    async def test_list_today_checkins_empty(self, auth_client):
        """查询今日打卡记录（无数据）：返回空列表"""
        resp = await auth_client.get("/api/v1/checkins/today")

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"] == []

    async def test_list_today_checkins_by_plan(self, auth_client):
        """按计划查询今日打卡：返回 checked_time_ids 和 records"""
        plan_id, time_ids = await _create_plan_with_times(auth_client)
        await auth_client.post("/api/v1/checkins", json={
            "plan_id": plan_id,
            "plan_time_id": time_ids[0],
            "actual_time": _today_actual_time(),
        })

        resp = await auth_client.get(f"/api/v1/checkins/today/{plan_id}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert time_ids[0] in data["checked_time_ids"]
        assert len(data["records"]) >= 1

    async def test_list_today_checkins_by_nonexistent_plan(self, auth_client):
        """按不存在的计划查询今日打卡：返回 200 空结果（不校验计划存在性）"""
        resp = await auth_client.get("/api/v1/checkins/today/999999")

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["checked_time_ids"] == []
        assert body["data"]["records"] == []

    # ==================== 月度打卡日历 ====================

    async def test_list_month_checkins(self, auth_client):
        """查询月度打卡日历：返回有打卡记录的日期列表"""
        plan_id, time_ids = await _create_plan_with_times(auth_client)
        await auth_client.post("/api/v1/checkins", json={
            "plan_id": plan_id,
            "plan_time_id": time_ids[0],
            "actual_time": _today_actual_time(),
        })

        today = today_shanghai()
        resp = await auth_client.get(
            f"/api/v1/checkins/month?year={today.year}&month={today.month}"
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert today.day in body["data"]["checked_days"]

    async def test_list_month_checkins_empty(self, auth_client):
        """查询月度打卡日历（无记录）：返回空 checked_days"""
        today = today_shanghai()
        resp = await auth_client.get(
            f"/api/v1/checkins/month?year={today.year}&month={today.month}"
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["checked_days"] == []

    # ==================== 日打卡详情 ====================

    async def test_list_day_detail(self, auth_client):
        """查询日打卡详情：包含计划信息和打卡状态"""
        plan_id, time_ids = await _create_plan_with_times(auth_client)
        await auth_client.post("/api/v1/checkins", json={
            "plan_id": plan_id,
            "plan_time_id": time_ids[0],
            "actual_time": _today_actual_time(),
        })

        today_str = today_shanghai().isoformat()
        resp = await auth_client.get(f"/api/v1/checkins/day?date={today_str}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        # 计划有两个通知时间点，应返回对应详情
        assert len(data) >= 1
        item = data[0]
        assert "plan_name" in item
        assert "notification_time" in item
        assert "checked" in item
        assert "checkin_count" in item
        # 08:30 打卡应匹配到 08:00 提醒时间，标记为已打卡
        checked_items = [d for d in data if d["checked"]]
        assert len(checked_items) >= 1
        assert checked_items[0]["first_actual_time"] is not None

    async def test_list_day_detail_invalid_date(self, auth_client):
        """日打卡详情日期格式不正确：返回 400"""
        resp = await auth_client.get("/api/v1/checkins/day?date=invalid-date")

        assert resp.status_code == 400
        assert "日期格式" in resp.json()["detail"]

    # ==================== 权限校验 ====================

    async def test_unauthenticated_request(self, client):
        """未认证请求：返回 401"""
        resp = await client.post("/api/v1/checkins", json={
            "plan_id": 1,
            "plan_time_id": 1,
            "actual_time": "2026-07-11T08:30:00",
        })

        assert resp.status_code == 401
