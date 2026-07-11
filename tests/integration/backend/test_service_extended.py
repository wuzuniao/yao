"""
服务层扩展集成测试
--------------------------------------------------------------------------
直接测试服务类方法，覆盖 API 层难以触达的业务逻辑：
- 微信登录（mock 微信 API）
- 过期账号清理
- 邮箱绑定与账号合并
- 邮件服务（mock SMTP）
- 站内信自动标记已读
- 通知渠道辅助方法
"""
import json
import time
from datetime import datetime, time as dt_time, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import Security
from app.models.checkin_record import CheckinRecord
from app.models.notification_channel import NotificationChannel
from app.models.notification_log import NotificationLog
from app.models.plan import CheckinPlan, PlanNotificationTime
from app.models.user import User as UserModel
from app.models.user_miniapp_account import UserMiniappAccount
from app.services.email_service import Email
from app.services.notification_channel_service import NotificationChannelService
from app.services.notification_log_service import NotificationLogService
from app.services.user_service import User, _verification_codes
from app.utils.timezone import now_shanghai, today_shanghai


# =============================================================================
# 辅助函数与 fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clear_verification_codes():
    """每个测试前清空验证码缓存，确保测试隔离"""
    _verification_codes.clear()


def _inject_code(email: str, purpose: str, code: str = "123456") -> str:
    """手动注入验证码到暂存字典，返回注入的验证码"""
    key = f"{email}:{purpose}"
    _verification_codes[key] = (code, time.time() + 300)
    return code


def _mock_wechat_httpx(mock_response: dict):
    """
    创建微信 httpx.AsyncClient 的 patch 上下文
    - mock_response: jscode2session 接口返回的字典
    """
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        return_value=AsyncMock(json=lambda: mock_response)
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return patch(
        "app.services.user_service.httpx.AsyncClient", return_value=mock_client
    )


async def _get_znx_channel(db_session, user_id: int) -> NotificationChannel:
    """获取用户的站内信通知渠道"""
    result = await db_session.execute(
        select(NotificationChannel).where(
            NotificationChannel.user_id == user_id,
            NotificationChannel.channel_type == "站内信",
        )
    )
    return result.scalar_one()


async def _create_wechat_user(db_session, username="微信用户"):
    """创建无邮箱无密码的微信登录用户，返回用户对象"""
    user = UserModel(
        username=username,
        email=None,
        password_hash=None,
        avatar_url="lan",
        signature="微信签名",
        status=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# =============================================================================
# 1. 微信登录测试
# =============================================================================

@pytest.mark.integration
async def test_wechat_login_new_user(db_session):
    """微信登录：新 openid 自动创建用户"""
    mock_response = {"openid": "test_openid_123", "session_key": "test_session_key"}
    with _mock_wechat_httpx(mock_response):
        user_service = User(db_session)
        user = await user_service.wechat_login("test_code")
        await db_session.commit()

    assert user.username.startswith("无足鸟")
    assert user.avatar_url == "lan"
    assert user.status == 1
    assert user.email is None
    assert user.password_hash is None


@pytest.mark.integration
async def test_wechat_login_existing_user(db_session):
    """微信登录：已绑定 openid 的用户复用现有账号"""
    # 1. 预先创建用户及小程序绑定记录
    existing_user = UserModel(
        username="已存在微信用户",
        email=None,
        password_hash=None,
        avatar_url="lan",
        signature="已有签名",
        status=1,
    )
    db_session.add(existing_user)
    await db_session.flush()

    account = UserMiniappAccount(
        user_id=existing_user.id,
        app_id=settings.WX_APPID,
        openid="existing_openid_456",
        session_key="old_session_key",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(existing_user)

    # 2. mock 微信接口返回相同 openid，验证用户被复用
    mock_response = {
        "openid": "existing_openid_456",
        "session_key": "new_session_key",
    }
    with _mock_wechat_httpx(mock_response):
        user_service = User(db_session)
        user = await user_service.wechat_login("test_code")

    assert user.id == existing_user.id
    assert user.username == "已存在微信用户"
    # 验证 session_key 已更新
    result = await db_session.execute(
        select(UserMiniappAccount).where(
            UserMiniappAccount.user_id == existing_user.id
        )
    )
    updated_account = result.scalar_one()
    assert updated_account.session_key == "new_session_key"


@pytest.mark.integration
async def test_wechat_login_invalid_code(db_session):
    """微信登录：微信接口返回 errcode 时抛出 ValueError"""
    mock_response = {"errcode": 40029, "errmsg": "invalid code"}
    with _mock_wechat_httpx(mock_response):
        user_service = User(db_session)
        with pytest.raises(ValueError, match="微信登录失败"):
            await user_service.wechat_login("invalid_code")


@pytest.mark.integration
async def test_wechat_login_generates_default_username(db_session):
    """微信登录：默认用户名以"无足鸟"为前缀并自增编号"""
    # 1. 预先创建一个名为"无足鸟1"的用户
    existing = UserModel(
        username="无足鸟1",
        email=None,
        password_hash=None,
        avatar_url="lan",
        signature="",
        status=1,
    )
    db_session.add(existing)
    await db_session.commit()

    # 2. 微信登录新用户，验证生成的用户名为"无足鸟2"
    mock_response = {"openid": "new_openid_789", "session_key": "test_key"}
    with _mock_wechat_httpx(mock_response):
        user_service = User(db_session)
        user = await user_service.wechat_login("test_code")
        await db_session.commit()

    assert user.username == "无足鸟2"


# =============================================================================
# 2. 过期账号清理测试
# =============================================================================

@pytest.mark.integration
async def test_purge_expired_deletions(db_session, test_user):
    """清理过期删除计划：status=0 且 updated_at 超过24小时的用户被删除"""
    test_user.status = 0
    test_user.updated_at = now_shanghai() - timedelta(hours=25)
    await db_session.commit()

    user_service = User(db_session)
    count = await user_service.purge_expired_deletions()
    assert count == 1


@pytest.mark.integration
async def test_purge_not_expired_user(db_session, test_user):
    """清理过期删除计划：status=0 但未超过24小时的用户不删除"""
    test_user.status = 0
    test_user.updated_at = now_shanghai() - timedelta(hours=12)
    await db_session.commit()

    user_service = User(db_session)
    count = await user_service.purge_expired_deletions()
    assert count == 0


@pytest.mark.integration
async def test_purge_active_user_not_deleted(db_session, test_user):
    """清理过期删除计划：status=1 的用户不删除"""
    test_user.status = 1
    test_user.updated_at = now_shanghai() - timedelta(hours=48)
    await db_session.commit()

    user_service = User(db_session)
    count = await user_service.purge_expired_deletions()
    assert count == 0


@pytest.mark.integration
async def test_purge_multiple_expired_users(db_session):
    """清理过期删除计划：批量删除多个过期用户"""
    for i in range(3):
        user = UserModel(
            username=f"待删除用户{i}",
            email=f"delete{i}@example.com",
            password_hash=Security.hash_password("Test1234!"),
            avatar_url="hei",
            signature="",
            status=0,
        )
        user.updated_at = now_shanghai() - timedelta(hours=30)
        db_session.add(user)
    await db_session.commit()

    user_service = User(db_session)
    count = await user_service.purge_expired_deletions()
    assert count == 3


@pytest.mark.integration
async def test_purge_also_deletes_miniapp_accounts(db_session):
    """清理过期删除计划：同时删除关联的小程序绑定记录"""
    # 1. 创建待删除用户及其小程序绑定记录
    user = UserModel(
        username="微信待删除用户",
        email=None,
        password_hash=None,
        avatar_url="lan",
        signature="",
        status=0,
    )
    user.updated_at = now_shanghai() - timedelta(hours=25)
    db_session.add(user)
    await db_session.flush()

    account = UserMiniappAccount(
        user_id=user.id,
        app_id=settings.WX_APPID,
        openid="purge_openid_001",
        session_key="test_key",
    )
    db_session.add(account)
    await db_session.commit()
    user_id = user.id

    # 2. 执行清理
    user_service = User(db_session)
    count = await user_service.purge_expired_deletions()
    assert count == 1

    # 3. 验证小程序绑定记录已删除
    result = await db_session.execute(
        select(UserMiniappAccount).where(UserMiniappAccount.user_id == user_id)
    )
    assert result.scalar_one_or_none() is None


# =============================================================================
# 3. 邮箱绑定与账号合并测试
# =============================================================================

@pytest.mark.integration
async def test_bind_email_direct_binding(db_session):
    """绑定邮箱：邮箱不存在时直接绑定到当前账号"""
    wechat_user = await _create_wechat_user(db_session)
    _inject_code("newbind@example.com", "change_new")

    user_service = User(db_session)
    result = await user_service.bind_email(
        wechat_user.id, "newbind@example.com", "123456"
    )

    assert result.id == wechat_user.id
    assert result.email == "newbind@example.com"


@pytest.mark.integration
async def test_bind_email_merge_accounts(db_session):
    """绑定邮箱：邮箱已存在时触发账号合并，返回主账号并删除从账号"""
    # 1. 创建主账号（已有邮箱）
    main_user = UserModel(
        username="主账号",
        email="existing@example.com",
        password_hash=Security.hash_password("Existing123!"),
        avatar_url="hei",
        signature="主账号签名",
        status=1,
    )
    db_session.add(main_user)
    await db_session.flush()

    # 2. 创建微信用户（从账号，无邮箱无密码）
    wechat_user = UserModel(
        username="微信用户",
        email=None,
        password_hash=None,
        avatar_url="lan",
        signature="微信用户签名",
        status=1,
    )
    db_session.add(wechat_user)
    await db_session.flush()

    # 3. 注入验证码
    _inject_code("existing@example.com", "change_new")

    # 4. 执行绑定（触发账号合并）
    user_service = User(db_session)
    result = await user_service.bind_email(
        wechat_user.id, "existing@example.com", "123456"
    )

    # 5. 验证返回主账号
    assert result.id == main_user.id
    assert result.email == "existing@example.com"

    # 6. 验证从账号已被删除
    deleted = await user_service.get_by_id(wechat_user.id)
    assert deleted is None


@pytest.mark.integration
async def test_bind_email_user_already_has_email(db_session, test_user):
    """绑定邮箱：用户已有邮箱时抛出 ValueError"""
    _inject_code("any@example.com", "change_new")

    user_service = User(db_session)
    with pytest.raises(ValueError, match="已绑定邮箱"):
        await user_service.bind_email(
            test_user.id, "any@example.com", "123456"
        )


@pytest.mark.integration
async def test_bind_email_wrong_code(db_session):
    """绑定邮箱：验证码错误时抛出 ValueError"""
    wechat_user = await _create_wechat_user(db_session)
    # 注入正确的验证码，但传入错误的验证码
    _inject_code("wrong@example.com", "change_new", code="999999")

    user_service = User(db_session)
    with pytest.raises(ValueError, match="验证码错误"):
        await user_service.bind_email(
            wechat_user.id, "wrong@example.com", "000000"
        )


# =============================================================================
# 4. 邮件服务测试（mock SMTP）
# =============================================================================

@pytest.mark.integration
async def test_email_service_send_code_success():
    """邮件服务：成功发送验证码邮件"""
    with patch("app.services.email_service.smtplib.SMTP_SSL") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=None)

        email = Email()
        email.send_verification_code("test@example.com", "123456")

        # 验证 SMTP_SSL 被调用
        mock_smtp.assert_called_once()
        # 验证 sendmail 被调用
        mock_server.sendmail.assert_called_once()


@pytest.mark.integration
async def test_email_service_send_code_auth_failure():
    """邮件服务：SMTP 认证失败时抛出 RuntimeError"""
    with patch("app.services.email_service.smtplib.SMTP_SSL") as mock_smtp:
        mock_server = MagicMock()
        # 设置 esmtp_features 使 _smtp_authenticate 走 AUTH PLAIN 分支
        mock_server.esmtp_features = {"auth": "PLAIN"}
        # docmd 返回认证失败码 535
        mock_server.docmd.return_value = (535, b"Authentication failed")
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=None)

        email = Email()
        with pytest.raises(RuntimeError, match="邮件发送失败"):
            email.send_verification_code("test@example.com", "123456")


@pytest.mark.integration
async def test_email_service_init_with_settings():
    """邮件服务：初始化时从 settings 读取 SMTP 配置"""
    email = Email()
    assert email.host == settings.SMTP_HOST
    assert email.port == settings.SMTP_PORT
    assert email.user == settings.SMTP_USER
    assert email.password == settings.SMTP_PASSWORD


# =============================================================================
# 5. 站内信自动标记已读测试
# =============================================================================

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
# 6. 通知渠道辅助方法测试
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
    # 创建无站内信渠道的用户
    user = UserModel(
        username="无渠道用户",
        email="nochannel@example.com",
        password_hash=Security.hash_password("Test1234!"),
        avatar_url="hei",
        signature="",
        status=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = NotificationChannelService(db_session)
    channel = await service.ensure_znx_channel(user.id)

    assert channel.id is not None
    assert channel.channel_type == "站内信"
    assert channel.channel_value == str(user.id)
    assert channel.enabled is True


@pytest.mark.integration
async def test_parse_email_channel_value_valid():
    """解析邮件渠道值：有效 JSON 返回字典"""
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
