"""
服务层扩展集成测试
--------------------------------------------------------------------------
直接测试服务类方法，覆盖 API 层难以触达的业务逻辑：
- 站内信自动标记已读
- 通知渠道辅助方法
（微信登录/账号清理/邮箱绑定与账号合并/验证码邮件等用户模块用例已迁 auth 服务仓库）
"""
from datetime import datetime, time as dt_time, timedelta

import pytest
from sqlalchemy import select

from app.models.checkin_record import CheckinRecord
from app.models.notification_channel import NotificationChannel
from app.models.notification_log import NotificationLog
from app.models.plan import CheckinPlan, PlanNotificationTime
from app.services.notification_channel_service import NotificationChannelService
from app.services.notification_log_service import NotificationLogService
from app.utils.timezone import now_shanghai, today_shanghai


# =============================================================================
# 辅助函数
# =============================================================================

async def _get_znx_channel(db_session, user_id: int) -> NotificationChannel:
    """获取用户的站内信通知渠道"""
    result = await db_session.execute(
        select(NotificationChannel).where(
            NotificationChannel.user_id == user_id,
            NotificationChannel.channel_type == "站内信",
        )
    )
    return result.scalar_one()


async def _create_plan_with_times(db_session, user_id):
    """创建带两个通知时间点（08:00、20:00）的计划，返回 (plan, time1, time2)"""
    today = today_shanghai()
    plan = CheckinPlan(
        user_id=user_id,
        name="自动标记测试计划",
        remark="测试备注",
        start_date=today,
        end_date=today + timedelta(days=30),
        status=1,
        priority=3,
    )
    db_session.add(plan)
    await db_session.flush()

    time1 = PlanNotificationTime(plan_id=plan.id, notification_time=dt_time(8, 0))
    time2 = PlanNotificationTime(plan_id=plan.id, notification_time=dt_time(20, 0))
    db_session.add_all([time1, time2])
    await db_session.flush()
    return plan, time1, time2


async def _create_unread_log(db_session, user_id, channel_id, plan_id, plan_time_id):
    """创建未读站内信记录"""
    log = NotificationLog(
        plan_id=plan_id,
        channel_id=channel_id,
        plan_time_id=plan_time_id,
        user_id=user_id,
        send_time=now_shanghai(),
        notify_date=today_shanghai(),
        status=2,  # 未读
        trigger_type=0,
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)
    return log


# =============================================================================
# 1. 站内信自动标记已读测试
# =============================================================================

@pytest.mark.integration
async def test_auto_mark_read_when_checkin_exists(db_session, test_user):
    """自动标记已读：匹配区间内有打卡记录时自动标记为已读"""
    plan, time1, _ = await _create_plan_with_times(db_session, test_user.id)
    channel = await _get_znx_channel(db_session, test_user.id)
    log = await _create_unread_log(
        db_session, test_user.id, channel.id, plan.id, time1.id
    )

    # 创建匹配区间内的打卡记录（08:30 在 08:00 的区间 [0:00, 14:00] 内）
    checkin = CheckinRecord(
        user_id=test_user.id,
        plan_id=plan.id,
        plan_time_id=time1.id,
        actual_time=datetime.combine(today_shanghai(), dt_time(8, 30)),
    )
    db_session.add(checkin)
    await db_session.commit()

    service = NotificationLogService(db_session)
    await service._auto_mark_read_if_checked(test_user.id)

    await db_session.refresh(log)
    assert log.status == 0  # 已标记为已读


@pytest.mark.integration
async def test_auto_mark_read_no_checkin(db_session, test_user):
    """自动标记已读：无打卡记录时保持未读"""
    plan, time1, _ = await _create_plan_with_times(db_session, test_user.id)
    channel = await _get_znx_channel(db_session, test_user.id)
    log = await _create_unread_log(
        db_session, test_user.id, channel.id, plan.id, time1.id
    )

    service = NotificationLogService(db_session)
    await service._auto_mark_read_if_checked(test_user.id)

    await db_session.refresh(log)
    assert log.status == 2  # 仍为未读


@pytest.mark.integration
async def test_auto_mark_read_skips_already_read(db_session, test_user):
    """自动标记已读：已读记录不参与判定，状态不变"""
    plan, time1, _ = await _create_plan_with_times(db_session, test_user.id)
    channel = await _get_znx_channel(db_session, test_user.id)

    # 创建已读站内信记录（status=0）
    log = NotificationLog(
        plan_id=plan.id,
        channel_id=channel.id,
        plan_time_id=time1.id,
        user_id=test_user.id,
        send_time=now_shanghai(),
        notify_date=today_shanghai(),
        status=0,  # 已读
        trigger_type=0,
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    # 创建匹配区间内的打卡记录
    checkin = CheckinRecord(
        user_id=test_user.id,
        plan_id=plan.id,
        plan_time_id=time1.id,
        actual_time=datetime.combine(today_shanghai(), dt_time(8, 30)),
    )
    db_session.add(checkin)
    await db_session.commit()

    service = NotificationLogService(db_session)
    await service._auto_mark_read_if_checked(test_user.id)

    await db_session.refresh(log)
    assert log.status == 0  # 仍为已读，不受影响


# =============================================================================
# 2. 通知渠道辅助方法测试
# =============================================================================

@pytest.mark.integration
async def test_ensure_znx_channel_returns_existing(db_session, test_user):
    """确保站内信渠道：用户已有站内信渠道时返回现有记录"""
    service = NotificationChannelService(db_session)
    channel = await service.ensure_znx_channel(test_user.id)

    assert channel.channel_type == "站内信"
    assert channel.channel_value == str(test_user.id)


@pytest.mark.integration
async def test_ensure_znx_channel_creates_new(db_session):
    """确保站内信渠道：用户无站内信渠道时创建新记录"""
    # 使用虚拟用户ID（业务表 user_id 无外键约束）
    virtual_user_id = 20001
    service = NotificationChannelService(db_session)
    channel = await service.ensure_znx_channel(virtual_user_id)

    assert channel.id is not None
    assert channel.channel_type == "站内信"
    assert channel.channel_value == str(virtual_user_id)
    assert channel.enabled is True


@pytest.mark.integration
async def test_list_by_user_lazy_creates_znx(db_session):
    """list_by_user 懒创建：用户无站内信渠道时首次查询自动补建（拆分后由 yao 懒创建）"""
    virtual_user_id = 20002
    service = NotificationChannelService(db_session)
    channels = await service.list_by_user(virtual_user_id)

    # 首次查询即包含自动补建的站内信渠道
    assert any(ch.channel_type == "站内信" for ch in channels)


@pytest.mark.integration
async def test_parse_email_channel_value_valid():
    """解析邮件渠道值：有效 JSON 返回字典"""
    import json
    valid_json = json.dumps({
        "smtp_host": "smtp.test.com",
        "smtp_port": 465,
        "email": "test@test.com",
        "password": "encrypted",
    })
    result = NotificationChannelService.parse_email_channel_value(valid_json)

    assert result is not None
    assert result["smtp_host"] == "smtp.test.com"
    assert result["smtp_port"] == 465
    assert result["email"] == "test@test.com"


@pytest.mark.integration
async def test_parse_email_channel_value_invalid():
    """解析邮件渠道值：无效 JSON 返回 None"""
    result = NotificationChannelService.parse_email_channel_value("invalid json")
    assert result is None
