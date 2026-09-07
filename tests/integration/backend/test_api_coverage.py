"""
集成测试补充：覆盖 API 层异常分支与端点
--------------------------------------------------------------------------
覆盖目标（用户模块 API 用例已迁 auth 服务仓库）：
- main.py: root/health 端点
- checkins.py: 时间格式错误、带时区时间转换
- notification_logs.py: read_all 失败分支
"""
from datetime import date, time as dt_time
from unittest.mock import patch

import pytest

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
