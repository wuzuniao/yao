"""
服务间内部接口集成测试（/internal/*，X-Service-Token 守卫，auth 服务回调）
--------------------------------------------------------------------------
- 令牌守卫：缺失/错误令牌返回 401
- POST /internal/users/{user_id}/purge：账号删除清理（幂等删 6 张业务表）
- POST /internal/users/merge：账号合并（业务数据迁移 + 渠道去重合并）
"""
import json
from datetime import date, datetime, time as dt_time

import pytest
from sqlalchemy import select

from app.models.checkin_record import CheckinRecord
from app.models.notification_channel import NotificationChannel
from app.models.notification_log import NotificationLog
from app.models.plan import CheckinPlan, PlanNotificationChannel, PlanNotificationTime
from app.schemas.notification_channel import CHANNEL_TYPE_ZNX, CHANNEL_TYPE_WECHAT

pytestmark = pytest.mark.integration

# 根 conftest.py 设置的测试服务令牌
SERVICE_TOKEN_HEADERS = {"X-Service-Token": "test-service-token"}


# =============================================================================
# 令牌守卫
# =============================================================================


async def test_internal_without_token(client):
    """未携带 X-Service-Token 应返回 401"""
    resp = await client.post("/internal/users/10001/purge")
    assert resp.status_code == 401
    assert "服务间通信令牌无效" in resp.json()["detail"]


async def test_internal_wrong_token(client):
    """错误的 X-Service-Token 应返回 401"""
    resp = await client.post(
        "/internal/users/10001/purge",
        headers={"X-Service-Token": "wrong-token"},
    )
    assert resp.status_code == 401


async def test_internal_merge_without_token(client):
    """merge 端点同样受令牌守卫保护"""
    resp = await client.post(
        "/internal/users/merge",
        json={"from_user_id": 1, "to_user_id": 2},
    )
    assert resp.status_code == 401


# =============================================================================
# POST /internal/users/{user_id}/purge（账号删除清理，幂等）
# =============================================================================


async def _create_business_data(db_session, user_id: int) -> int:
    """为指定用户创建全套业务数据（计划/时间点/渠道/关联/打卡/日志），返回计划ID"""
    channel = NotificationChannel(
        user_id=user_id, channel_type=CHANNEL_TYPE_ZNX,
        channel_value=str(user_id), enabled=True,
    )
    db_session.add(channel)
    await db_session.flush()

    plan = CheckinPlan(
        user_id=user_id, name="待清理计划",
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        status=1, priority=3,
    )
    db_session.add(plan)
    await db_session.flush()

    nt = PlanNotificationTime(plan_id=plan.id, notification_time=dt_time(8, 0))
    db_session.add(nt)
    await db_session.flush()

    db_session.add(PlanNotificationChannel(plan_id=plan.id, channel_id=channel.id))
    db_session.add(CheckinRecord(
        user_id=user_id, plan_id=plan.id, plan_time_id=nt.id,
        actual_time=datetime(2026, 7, 2, 8, 0),
    ))
    db_session.add(NotificationLog(
        plan_id=plan.id, channel_id=channel.id, plan_time_id=nt.id,
        user_id=user_id, send_time=datetime(2026, 7, 2, 8, 0),
        notify_date=date(2026, 7, 2), status=2, trigger_type=0,
    ))
    await db_session.commit()
    return plan.id


async def test_purge_deletes_all_business_data(client, db_session):
    """purge：删除该用户的全部业务数据（6 张表）"""
    user_id = 30001
    plan_id = await _create_business_data(db_session, user_id)

    resp = await client.post(
        f"/internal/users/{user_id}/purge", headers=SERVICE_TOKEN_HEADERS
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 0

    # 验证六类数据全部清除
    assert (await db_session.execute(
        select(CheckinPlan).where(CheckinPlan.user_id == user_id)
    )).scalars().all() == []
    assert (await db_session.execute(
        select(PlanNotificationTime).where(PlanNotificationTime.plan_id == plan_id)
    )).scalars().all() == []
    assert (await db_session.execute(
        select(PlanNotificationChannel).where(PlanNotificationChannel.plan_id == plan_id)
    )).scalars().all() == []
    assert (await db_session.execute(
        select(CheckinRecord).where(CheckinRecord.user_id == user_id)
    )).scalars().all() == []
    assert (await db_session.execute(
        select(NotificationLog).where(NotificationLog.user_id == user_id)
    )).scalars().all() == []
    assert (await db_session.execute(
        select(NotificationChannel).where(NotificationChannel.user_id == user_id)
    )).scalars().all() == []


async def test_purge_idempotent_no_data(client, db_session):
    """purge：目标用户无业务数据亦返回成功（幂等，auth 据此决定删除用户库数据）"""
    resp = await client.post(
        "/internal/users/999999/purge", headers=SERVICE_TOKEN_HEADERS
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


async def test_purge_does_not_touch_other_users(client, db_session):
    """purge：仅删除目标用户数据，不影响其他用户"""
    target_id, other_id = 30002, 30003
    await _create_business_data(db_session, target_id)
    other_plan_id = await _create_business_data(db_session, other_id)

    resp = await client.post(
        f"/internal/users/{target_id}/purge", headers=SERVICE_TOKEN_HEADERS
    )
    assert resp.status_code == 200

    # 其他用户数据完好
    assert (await db_session.execute(
        select(CheckinPlan).where(CheckinPlan.id == other_plan_id)
    )).scalar_one() is not None


# =============================================================================
# POST /internal/users/merge（账号合并）
# =============================================================================


async def test_merge_migrates_business_data(client, db_session):
    """merge：从账号业务数据整体迁移到主账号名下"""
    sub_id, main_id = 30011, 30012
    sub_plan_id = await _create_business_data(db_session, sub_id)
    # 主账号已有自己的站内信渠道
    main_channel = NotificationChannel(
        user_id=main_id, channel_type=CHANNEL_TYPE_ZNX,
        channel_value=str(main_id), enabled=True,
    )
    db_session.add(main_channel)
    await db_session.commit()

    resp = await client.post(
        "/internal/users/merge",
        headers=SERVICE_TOKEN_HEADERS,
        json={"from_user_id": sub_id, "to_user_id": main_id},
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 0

    # 计划已归属主账号；打卡/日志随 user_id 迁移
    plan = (await db_session.execute(
        select(CheckinPlan).where(CheckinPlan.id == sub_plan_id)
    )).scalar_one()
    assert plan.user_id == main_id
    assert (await db_session.execute(
        select(CheckinRecord).where(CheckinRecord.user_id == sub_id)
    )).scalars().all() == []
    assert (await db_session.execute(
        select(NotificationLog).where(NotificationLog.user_id == sub_id)
    )).scalars().all() == []
    # 站内信渠道去重合并：从账号渠道被删除，主账号保留一条
    sub_channels = (await db_session.execute(
        select(NotificationChannel).where(NotificationChannel.user_id == sub_id)
    )).scalars().all()
    main_znx = (await db_session.execute(
        select(NotificationChannel).where(
            NotificationChannel.user_id == main_id,
            NotificationChannel.channel_type == CHANNEL_TYPE_ZNX,
        )
    )).scalars().all()
    assert sub_channels == []
    assert len(main_znx) == 1


async def test_merge_wechat_quota_accumulated(client, db_session):
    """merge：双方均有微信渠道时额度 granted/sent 累加到主账号"""
    sub_id, main_id = 30021, 30022
    db_session.add(NotificationChannel(
        user_id=sub_id, channel_type=CHANNEL_TYPE_WECHAT,
        channel_value=json.dumps({"granted": 3, "sent": 1}), enabled=True,
    ))
    db_session.add(NotificationChannel(
        user_id=main_id, channel_type=CHANNEL_TYPE_WECHAT,
        channel_value=json.dumps({"granted": 2, "sent": 0}), enabled=True,
    ))
    await db_session.commit()

    resp = await client.post(
        "/internal/users/merge",
        headers=SERVICE_TOKEN_HEADERS,
        json={"from_user_id": sub_id, "to_user_id": main_id},
    )
    assert resp.status_code == 200

    # 主账号微信渠道：granted=5, sent=1；从账号渠道被删除
    wx = (await db_session.execute(
        select(NotificationChannel).where(
            NotificationChannel.user_id == main_id,
            NotificationChannel.channel_type == CHANNEL_TYPE_WECHAT,
        )
    )).scalar_one()
    assert json.loads(wx.channel_value) == {"granted": 5, "sent": 1}
    assert wx.enabled is True
    assert (await db_session.execute(
        select(NotificationChannel).where(NotificationChannel.user_id == sub_id)
    )).scalars().all() == []


async def test_merge_same_user_rejected(client):
    """merge：从账号与主账号相同时返回 400"""
    resp = await client.post(
        "/internal/users/merge",
        headers=SERVICE_TOKEN_HEADERS,
        json={"from_user_id": 1, "to_user_id": 1},
    )
    assert resp.status_code == 400


async def test_merge_invalid_body(client):
    """merge：请求体缺参或非法 ID 返回 422"""
    resp = await client.post(
        "/internal/users/merge",
        headers=SERVICE_TOKEN_HEADERS,
        json={"from_user_id": 1},
    )
    assert resp.status_code == 422
    resp = await client.post(
        "/internal/users/merge",
        headers=SERVICE_TOKEN_HEADERS,
        json={"from_user_id": 0, "to_user_id": 1},
    )
    assert resp.status_code == 422
