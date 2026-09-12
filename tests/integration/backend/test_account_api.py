"""
账号生命周期集成测试（业务项目主动执行，auth 不再回调）
--------------------------------------------------------------------------
- 业务数据清理（purge_user_business_data）：幂等删 6 张业务表、不影响他人
- 业务数据合并迁移（merge_business_data）：整体迁移 + 渠道去重 + 微信额度累加
- 账号合并请求（request_account_merge）：auth 任务校验 / 迁移落库 / confirm 上报
- 合并确认重试（retry_pending_merges）：confirm 失败补偿
- POST /api/v1/account/merge API 层（Bearer 认证）
auth 服务交互（get_merge_task / confirm_merge / list_pending_purges / report_purge）
一律经 monkeypatch mock（根 conftest 的 AUTH_BASE_URL 为不可达地址）。
"""
import json
from datetime import date, datetime, time as dt_time

import pytest
from sqlalchemy import select

import app.core.auth_client as auth_client_module
from app.models.checkin_record import CheckinRecord
from app.models.merge_task import MERGE_SYNC_DONE, MERGE_SYNC_PENDING, MergeSyncTask
from app.models.notification_channel import NotificationChannel
from app.models.notification_log import NotificationLog
from app.models.plan import CheckinPlan, PlanNotificationChannel, PlanNotificationTime
from app.schemas.notification_channel import CHANNEL_TYPE_WECHAT, CHANNEL_TYPE_ZNX
from app.services.account_service import (
    merge_business_data,
    purge_user_business_data,
    request_account_merge,
    retry_pending_merges,
)

pytestmark = pytest.mark.integration


# =============================================================================
# 辅助函数
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


async def _assert_business_data_purged(db_session, user_id: int, plan_id: int):
    """断言该用户六类业务数据已全部清除"""
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


# =============================================================================
# 业务数据清理（purge_user_business_data）
# =============================================================================


@pytest.mark.integration
async def test_purge_deletes_all_business_data(db_session):
    """清理：删除该用户的全部业务数据（6 张表）"""
    user_id = 30001
    plan_id = await _create_business_data(db_session, user_id)

    await purge_user_business_data(db_session, user_id)
    await _assert_business_data_purged(db_session, user_id, plan_id)


@pytest.mark.integration
async def test_purge_idempotent_no_data(db_session):
    """清理：目标用户无业务数据亦正常返回（幂等，重复清理无副作用）"""
    await purge_user_business_data(db_session, 999999)
    await purge_user_business_data(db_session, 999999)


@pytest.mark.integration
async def test_purge_does_not_touch_other_users(db_session):
    """清理：仅删除目标用户数据，不影响其他用户"""
    target_id, other_id = 30002, 30003
    await _create_business_data(db_session, target_id)
    other_plan_id = await _create_business_data(db_session, other_id)

    await purge_user_business_data(db_session, target_id)

    other_plan = (await db_session.execute(
        select(CheckinPlan).where(CheckinPlan.id == other_plan_id)
    )).scalar_one()
    assert other_plan is not None


# =============================================================================
# 业务数据合并迁移（merge_business_data）
# =============================================================================


@pytest.mark.integration
async def test_merge_migrates_business_data(db_session):
    """迁移：从账号业务数据整体迁移到主账号名下"""
    sub_id, main_id = 30011, 30012
    sub_plan_id = await _create_business_data(db_session, sub_id)
    # 主账号已有自己的站内信渠道
    main_channel = NotificationChannel(
        user_id=main_id, channel_type=CHANNEL_TYPE_ZNX,
        channel_value=str(main_id), enabled=True,
    )
    db_session.add(main_channel)
    await db_session.commit()

    await merge_business_data(db_session, sub_id, main_id)
    await db_session.commit()

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


@pytest.mark.integration
async def test_merge_wechat_quota_accumulated(db_session):
    """迁移：双方均有微信渠道时额度 granted/sent 累加到主账号"""
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

    await merge_business_data(db_session, sub_id, main_id)
    await db_session.commit()

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


# =============================================================================
# 账号合并请求（request_account_merge，auth 交互 mock）
# =============================================================================


@pytest.mark.integration
async def test_merge_request_no_task_rejected(db_session, monkeypatch):
    """合并请求：auth 无待合并任务时抛 ValueError"""
    async def fake_get_merge_task(from_user_id):
        return None

    monkeypatch.setattr(auth_client_module, "get_merge_task", fake_get_merge_task)

    with pytest.raises(ValueError, match="无待合并任务"):
        await request_account_merge(db_session, 30031)


@pytest.mark.integration
async def test_merge_request_success(db_session, monkeypatch):
    """合并请求：迁移业务数据 + 落 done 记录 + confirm 上报成功返回 completed"""
    sub_id, main_id = 30032, 30033
    plan_id = await _create_business_data(db_session, sub_id)

    async def fake_get_merge_task(from_user_id):
        assert from_user_id == sub_id
        return {"from_user_id": sub_id, "to_user_id": main_id}

    confirmed = []

    async def fake_confirm_merge(from_user_id, to_user_id):
        confirmed.append((from_user_id, to_user_id))

    monkeypatch.setattr(auth_client_module, "get_merge_task", fake_get_merge_task)
    monkeypatch.setattr(auth_client_module, "confirm_merge", fake_confirm_merge)

    status = await request_account_merge(db_session, sub_id)
    assert status == "completed"
    assert confirmed == [(sub_id, main_id)]

    # 业务数据已迁移到主账号
    plan = (await db_session.execute(
        select(CheckinPlan).where(CheckinPlan.id == plan_id)
    )).scalar_one()
    assert plan.user_id == main_id
    # 本地同步记录已置 done（完成状态）
    task = (await db_session.execute(
        select(MergeSyncTask).where(MergeSyncTask.from_user_id == sub_id)
    )).scalar_one()
    assert task.status == MERGE_SYNC_DONE
    assert task.to_user_id == main_id


@pytest.mark.integration
async def test_merge_request_confirm_failure_keeps_pending(db_session, monkeypatch):
    """合并请求：confirm 上报失败时返回 processing 并保留 pending（后台重试）"""
    sub_id, main_id = 30034, 30035
    await _create_business_data(db_session, sub_id)

    async def fake_get_merge_task(from_user_id):
        return {"from_user_id": sub_id, "to_user_id": main_id}

    async def fake_confirm_merge(from_user_id, to_user_id):
        raise ConnectionError("auth 不可达")

    monkeypatch.setattr(auth_client_module, "get_merge_task", fake_get_merge_task)
    monkeypatch.setattr(auth_client_module, "confirm_merge", fake_confirm_merge)

    status = await request_account_merge(db_session, sub_id)
    assert status == "processing"

    task = (await db_session.execute(
        select(MergeSyncTask).where(MergeSyncTask.from_user_id == sub_id)
    )).scalar_one()
    assert task.status == MERGE_SYNC_PENDING


@pytest.mark.integration
async def test_merge_request_local_done_idempotent(db_session, monkeypatch):
    """合并请求：本地记录已 done 时直接返回 completed（不再调用 auth）"""
    sub_id, main_id = 30036, 30037
    db_session.add(MergeSyncTask(
        from_user_id=sub_id, to_user_id=main_id, status=MERGE_SYNC_DONE,
    ))
    await db_session.commit()

    async def fail_get_merge_task(from_user_id):
        raise AssertionError("本地已完成时不应再调用 auth")

    monkeypatch.setattr(auth_client_module, "get_merge_task", fail_get_merge_task)

    status = await request_account_merge(db_session, sub_id)
    assert status == "completed"


@pytest.mark.integration
async def test_merge_request_same_user_rejected(db_session, monkeypatch):
    """合并请求：auth 任务的主账号与从账号相同时拒绝"""
    async def fake_get_merge_task(from_user_id):
        return {"from_user_id": 30038, "to_user_id": 30038}

    monkeypatch.setattr(auth_client_module, "get_merge_task", fake_get_merge_task)

    with pytest.raises(ValueError, match="不能相同"):
        await request_account_merge(db_session, 30038)


@pytest.mark.integration
async def test_merge_request_auth_task_gone_local_pending(db_session, monkeypatch):
    """合并请求：本地 pending 但 auth 任务已不存在（auth 已合并的残局）→ 补记 done"""
    sub_id, main_id = 30039, 30040
    db_session.add(MergeSyncTask(
        from_user_id=sub_id, to_user_id=main_id, status=MERGE_SYNC_PENDING,
    ))
    await db_session.commit()

    async def fake_get_merge_task(from_user_id):
        return None

    monkeypatch.setattr(auth_client_module, "get_merge_task", fake_get_merge_task)

    status = await request_account_merge(db_session, sub_id)
    assert status == "completed"
    task = (await db_session.execute(
        select(MergeSyncTask).where(MergeSyncTask.from_user_id == sub_id)
    )).scalar_one()
    assert task.status == MERGE_SYNC_DONE


@pytest.mark.integration
async def test_retry_pending_merges_confirms(db_session, monkeypatch):
    """合并重试：pending 记录经重试上报成功后置 done"""
    sub_id, main_id = 30041, 30042
    db_session.add(MergeSyncTask(
        from_user_id=sub_id, to_user_id=main_id, status=MERGE_SYNC_PENDING,
    ))
    await db_session.commit()

    confirmed = []

    async def fake_confirm_merge(from_user_id, to_user_id):
        confirmed.append((from_user_id, to_user_id))

    monkeypatch.setattr(auth_client_module, "confirm_merge", fake_confirm_merge)

    count = await retry_pending_merges(db_session)
    assert count == 1
    assert confirmed == [(sub_id, main_id)]
    task = (await db_session.execute(
        select(MergeSyncTask).where(MergeSyncTask.from_user_id == sub_id)
    )).scalar_one()
    assert task.status == MERGE_SYNC_DONE


@pytest.mark.integration
async def test_retry_pending_merges_tolerates_failure(db_session, monkeypatch):
    """合并重试：auth 不可达时保留 pending，下一轮重试"""
    db_session.add(MergeSyncTask(
        from_user_id=30043, to_user_id=30044, status=MERGE_SYNC_PENDING,
    ))
    await db_session.commit()

    async def fake_confirm_merge(from_user_id, to_user_id):
        raise ConnectionError("auth 不可达")

    monkeypatch.setattr(auth_client_module, "confirm_merge", fake_confirm_merge)

    count = await retry_pending_merges(db_session)
    assert count == 0
    task = (await db_session.execute(
        select(MergeSyncTask).where(MergeSyncTask.from_user_id == 30043)
    )).scalar_one()
    assert task.status == MERGE_SYNC_PENDING


# =============================================================================
# POST /api/v1/account/merge（API 层，Bearer 认证）
# =============================================================================


@pytest.mark.integration
async def test_account_merge_api_requires_auth(client):
    """未携带 Bearer 令牌返回 401"""
    resp = await client.post("/api/v1/account/merge")
    assert resp.status_code == 401


@pytest.mark.integration
async def test_account_merge_api_completed(auth_client, db_session, monkeypatch):
    """API 层：合并成功返回 status=completed"""
    # auth_client fixture 的当前用户由 conftest 的 test_user（SimpleNamespace）签发，
    # 此处直接 mock 服务交互并断言响应结构
    async def fake_get_merge_task(from_user_id):
        return {"from_user_id": from_user_id, "to_user_id": 30051}

    async def fake_confirm_merge(from_user_id, to_user_id):
        return None

    monkeypatch.setattr(auth_client_module, "get_merge_task", fake_get_merge_task)
    monkeypatch.setattr(auth_client_module, "confirm_merge", fake_confirm_merge)

    resp = await auth_client.post("/api/v1/account/merge")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "completed"
