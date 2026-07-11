"""
通知渠道与站内信 API 集成测试
- 通知渠道：站内信（自动创建）、邮件渠道（增删改查）
- 站内信：列表查询、标记已读、未读数量、全部已读
"""
import json
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.security import Security
from app.models.notification_channel import NotificationChannel
from app.models.notification_log import NotificationLog
from app.models.plan import CheckinPlan
from app.models.user import User as UserModel
from app.utils.timezone import now_shanghai, today_shanghai


# ===== 辅助函数 =====


async def _create_notification_log(
    db_session, user_id, channel_id, status=2, plan_id=None, plan_time_id=None
):
    """创建测试站内信记录"""
    log = NotificationLog(
        plan_id=plan_id or 1,
        channel_id=channel_id,
        plan_time_id=plan_time_id,
        user_id=user_id,
        send_time=now_shanghai() - timedelta(minutes=10),
        notify_date=now_shanghai().date(),
        status=status,  # 2=未读, 0=已读
        trigger_type=0,
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)
    return log


async def _create_another_user(db_session):
    """创建另一个测试用户及其站内信渠道（用于跨用户权限隔离测试）"""
    user = UserModel(
        username="其他用户",
        email="other@example.com",
        password_hash=Security.hash_password("Test1234!"),
        status=1,
    )
    db_session.add(user)
    await db_session.flush()
    channel = NotificationChannel(
        user_id=user.id,
        channel_type="站内信",
        channel_value=str(user.id),
        enabled=True,
    )
    db_session.add(channel)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(channel)
    return user, channel


async def _get_znx_channel(db_session, user_id):
    """获取用户的站内信渠道"""
    result = await db_session.execute(
        select(NotificationChannel).where(
            NotificationChannel.user_id == user_id,
            NotificationChannel.channel_type == "站内信",
        )
    )
    return result.scalar_one()


async def _create_checkin_plan(db_session, user_id, name="测试计划", remark="测试备注"):
    """创建测试打卡计划（站内信列表 JOIN 关联计划名称/备注）"""
    plan = CheckinPlan(
        user_id=user_id,
        name=name,
        remark=remark,
        start_date=today_shanghai(),
        end_date=today_shanghai() + timedelta(days=30),
        status=1,
        priority=3,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


async def _create_email_channel_via_api(
    auth_client, email="sender@example.com", password="mypassword"
):
    """通过 API 创建邮件渠道，返回响应对象"""
    return await auth_client.post(
        "/api/v1/notification-channels/email",
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 465,
            "email": email,
            "password": password,
            "enabled": True,
        },
    )


# ===== 通知渠道：列表查询 =====


class TestListChannels:
    """通知渠道列表查询"""

    @pytest.mark.integration
    async def test_list_channels_with_znx(self, auth_client, test_user):
        """列表查询：默认存在站内信渠道"""
        resp = await auth_client.get("/api/v1/notification-channels/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        channels = body["data"]
        assert len(channels) == 1
        ch = channels[0]
        assert ch["channel_type"] == "站内信"
        assert ch["channel_value"] == str(test_user.id)
        assert ch["enabled"] is True
        assert ch["user_id"] == test_user.id

    @pytest.mark.integration
    async def test_list_channels_after_creating_email(self, auth_client, test_user):
        """列表查询：创建邮件渠道后应返回 2 个渠道"""
        # 先创建邮件渠道
        resp = await _create_email_channel_via_api(auth_client)
        assert resp.status_code == 200
        # 查询列表
        resp = await auth_client.get("/api/v1/notification-channels/list")
        assert resp.status_code == 200
        channels = resp.json()["data"]
        assert len(channels) == 2
        types = {ch["channel_type"] for ch in channels}
        assert types == {"站内信", "邮件"}

    @pytest.mark.integration
    async def test_list_channels_after_deletion(self, auth_client, test_user):
        """列表查询：删除邮件渠道后仅剩站内信"""
        # 创建邮件渠道
        resp = await _create_email_channel_via_api(auth_client)
        channel_id = resp.json()["data"]["id"]
        # 删除邮件渠道
        resp = await auth_client.request("DELETE",
            "/api/v1/notification-channels", json={"channel_id": channel_id}
        )
        assert resp.status_code == 200
        # 查询列表，仅剩站内信
        resp = await auth_client.get("/api/v1/notification-channels/list")
        assert resp.status_code == 200
        channels = resp.json()["data"]
        assert len(channels) == 1
        assert channels[0]["channel_type"] == "站内信"


# ===== 通知渠道：创建邮件渠道 =====


class TestCreateEmailChannel:
    """创建邮件通知渠道"""

    @pytest.mark.integration
    async def test_create_email_channel_success(self, auth_client, test_user):
        """创建邮件渠道成功：响应包含 email_config，password 为空字符串"""
        resp = await _create_email_channel_via_api(
            auth_client, email="sender@example.com", password="mypassword"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["msg"] == "邮件通知方式添加成功"
        data = body["data"]
        assert data["channel_type"] == "邮件"
        assert data["enabled"] is True
        assert data["user_id"] == test_user.id
        # email_config 应包含 SMTP 配置，password 始终为空（安全考虑）
        cfg = data["email_config"]
        assert cfg["smtp_host"] == "smtp.example.com"
        assert cfg["smtp_port"] == 465
        assert cfg["email"] == "sender@example.com"
        assert cfg["password"] == ""

    @pytest.mark.integration
    async def test_create_email_channel_duplicate_email(self, auth_client, test_user):
        """创建邮件渠道：相同邮箱地址重复配置返回 400"""
        # 第一次创建
        resp = await _create_email_channel_via_api(
            auth_client, email="dup@example.com", password="pass1"
        )
        assert resp.status_code == 200
        # 第二次用相同邮箱创建 → 400
        resp = await _create_email_channel_via_api(
            auth_client, email="dup@example.com", password="pass2"
        )
        assert resp.status_code == 400
        assert "已配置" in resp.json()["detail"]

    @pytest.mark.integration
    async def test_create_email_channel_invalid_port(self, auth_client, test_user):
        """创建邮件渠道：非法 SMTP 端口返回 422"""
        resp = await auth_client.post(
            "/api/v1/notification-channels/email",
            json={
                "smtp_host": "smtp.example.com",
                "smtp_port": 0,  # 非法端口（范围 1-65535）
                "email": "port@example.com",
                "password": "mypassword",
                "enabled": True,
            },
        )
        assert resp.status_code == 422

    @pytest.mark.integration
    async def test_create_email_channel_invalid_email(self, auth_client, test_user):
        """创建邮件渠道：非法邮箱格式返回 422"""
        resp = await auth_client.post(
            "/api/v1/notification-channels/email",
            json={
                "smtp_host": "smtp.example.com",
                "smtp_port": 465,
                "email": "invalid-email",  # 缺少 @ 符号
                "password": "mypassword",
                "enabled": True,
            },
        )
        assert resp.status_code == 422


# ===== 通知渠道：更新邮件渠道 =====


class TestUpdateEmailChannel:
    """更新邮件通知渠道"""

    @pytest.mark.integration
    async def test_update_email_channel_success(self, auth_client, test_user):
        """更新邮件渠道成功：字段已更新"""
        # 先创建邮件渠道
        resp = await _create_email_channel_via_api(auth_client)
        channel_id = resp.json()["data"]["id"]
        # 更新渠道
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
        body = resp.json()
        assert body["code"] == 0
        assert body["msg"] == "邮件通知方式更新成功"
        data = body["data"]
        assert data["enabled"] is False
        cfg = data["email_config"]
        assert cfg["smtp_host"] == "smtp.updated.com"
        assert cfg["smtp_port"] == 587
        assert cfg["email"] == "updated@example.com"
        assert cfg["password"] == ""

    @pytest.mark.integration
    async def test_update_email_channel_empty_password_keeps_original(
        self, auth_client, test_user, db_session
    ):
        """更新邮件渠道：password 为空时保留原密码"""
        # 创建渠道，密码为 mypassword
        resp = await _create_email_channel_via_api(
            auth_client, password="mypassword"
        )
        channel_id = resp.json()["data"]["id"]
        # 更新时 password="" 表示保留原密码
        resp = await auth_client.put(
            "/api/v1/notification-channels/email",
            json={
                "channel_id": channel_id,
                "smtp_host": "smtp.updated.com",
                "smtp_port": 587,
                "email": "updated@example.com",
                "password": "",  # 空字符串 → 保留原密码
                "enabled": True,
            },
        )
        assert resp.status_code == 200
        # 查询数据库验证密码未被清空（仍为加密后的非空字符串）
        result = await db_session.execute(
            select(NotificationChannel).where(NotificationChannel.id == channel_id)
        )
        channel = result.scalar_one()
        cfg = json.loads(channel.channel_value)
        assert cfg["password"] != ""  # 原加密密码被保留
        assert cfg["smtp_host"] == "smtp.updated.com"

    @pytest.mark.integration
    async def test_update_nonexistent_channel(self, auth_client, test_user):
        """更新不存在的渠道返回 400"""
        resp = await auth_client.put(
            "/api/v1/notification-channels/email",
            json={
                "channel_id": 99999,
                "smtp_host": "smtp.example.com",
                "smtp_port": 465,
                "email": "noreply@example.com",
                "password": "mypassword",
                "enabled": True,
            },
        )
        assert resp.status_code == 400
        assert "不存在" in resp.json()["detail"]

    @pytest.mark.integration
    async def test_update_channel_belonging_to_another_user(
        self, auth_client, test_user, db_session
    ):
        """更新其他用户的渠道返回 400"""
        # 创建另一个用户及其邮件渠道
        other_user, _ = await _create_another_user(db_session)
        other_channel = NotificationChannel(
            user_id=other_user.id,
            channel_type="邮件",
            channel_value=json.dumps(
                {
                    "smtp_host": "smtp.other.com",
                    "smtp_port": 465,
                    "email": "other@example.com",
                    "password": "encrypted-pwd",
                }
            ),
            enabled=True,
        )
        db_session.add(other_channel)
        await db_session.commit()
        await db_session.refresh(other_channel)
        # 当前用户尝试更新别人的渠道 → 400
        resp = await auth_client.put(
            "/api/v1/notification-channels/email",
            json={
                "channel_id": other_channel.id,
                "smtp_host": "smtp.hacked.com",
                "smtp_port": 587,
                "email": "hacked@example.com",
                "password": "hacked",
                "enabled": False,
            },
        )
        assert resp.status_code == 400
        assert "无权" in resp.json()["detail"]


# ===== 通知渠道：删除渠道 =====


class TestDeleteChannel:
    """删除通知渠道"""

    @pytest.mark.integration
    async def test_delete_email_channel(self, auth_client, test_user):
        """删除邮件渠道成功"""
        # 先创建邮件渠道
        resp = await _create_email_channel_via_api(auth_client)
        channel_id = resp.json()["data"]["id"]
        # 删除
        resp = await auth_client.request("DELETE",
            "/api/v1/notification-channels", json={"channel_id": channel_id}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["msg"] == "通知方式删除成功"

    @pytest.mark.integration
    async def test_delete_znx_channel_not_allowed(self, auth_client, test_user, db_session):
        """删除站内信渠道返回 400（站内信不允许删除）"""
        znx_channel = await _get_znx_channel(db_session, test_user.id)
        resp = await auth_client.request("DELETE",
            "/api/v1/notification-channels",
            json={"channel_id": znx_channel.id},
        )
        assert resp.status_code == 400
        assert "不允许删除" in resp.json()["detail"]

    @pytest.mark.integration
    async def test_delete_nonexistent_channel(self, auth_client, test_user):
        """删除不存在的渠道返回 400"""
        resp = await auth_client.request("DELETE",
            "/api/v1/notification-channels", json={"channel_id": 99999}
        )
        assert resp.status_code == 400
        assert "不存在" in resp.json()["detail"]


# ===== 站内信：列表查询 =====


class TestListNotificationLogs:
    """站内信列表查询"""

    @pytest.mark.integration
    async def test_list_logs_empty(self, auth_client, test_user):
        """列表查询：无站内信记录时返回空列表"""
        resp = await auth_client.get("/api/v1/notification-logs/list?page=1&limit=20")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["limit"] == 20
        assert data["has_more"] is False
        assert data["unread_count"] == 0

    @pytest.mark.integration
    async def test_list_logs_with_data(self, auth_client, test_user, db_session):
        """列表查询：有站内信记录时返回正确数据"""
        # 创建计划与站内信记录
        plan = await _create_checkin_plan(db_session, test_user.id, name="喝水提醒", remark="每日8杯")
        znx = await _get_znx_channel(db_session, test_user.id)
        log = await _create_notification_log(
            db_session, test_user.id, znx.id, status=2, plan_id=plan.id
        )
        # 查询列表
        resp = await auth_client.get("/api/v1/notification-logs/list?page=1&limit=20")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["id"] == log.id
        assert item["plan_name"] == "喝水提醒"
        assert item["plan_remark"] == "每日8杯"
        assert item["send_time"] is not None
        assert item["is_unread"] is True
        # 存在未读 → unread_count 为 1
        assert data["unread_count"] == 1

    @pytest.mark.integration
    async def test_list_logs_pagination(self, auth_client, test_user, db_session):
        """列表查询：分页参数正确"""
        # 批量创建 25 条站内信记录
        znx = await _get_znx_channel(db_session, test_user.id)
        for i in range(25):
            await _create_notification_log(
                db_session, test_user.id, znx.id, status=2, plan_id=1
            )
        # 第一页：10 条，has_more=True
        resp = await auth_client.get("/api/v1/notification-logs/list?page=1&limit=10")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 25
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["limit"] == 10
        assert data["has_more"] is True
        # 第三页：5 条，has_more=False
        resp = await auth_client.get("/api/v1/notification-logs/list?page=3&limit=10")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 5
        assert data["has_more"] is False


# ===== 站内信：未读数量 =====


class TestUnreadCount:
    """站内信未读数量查询"""

    @pytest.mark.integration
    async def test_unread_count_with_unread(self, auth_client, test_user, db_session):
        """未读数量：存在未读记录时返回正确计数"""
        znx = await _get_znx_channel(db_session, test_user.id)
        # 创建 3 条未读 + 2 条已读
        for _ in range(3):
            await _create_notification_log(db_session, test_user.id, znx.id, status=2)
        for _ in range(2):
            await _create_notification_log(db_session, test_user.id, znx.id, status=0)
        resp = await auth_client.get("/api/v1/notification-logs/unread-count")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["unread_count"] == 3

    @pytest.mark.integration
    async def test_unread_count_when_none(self, auth_client, test_user):
        """未读数量：无未读记录时返回 0"""
        resp = await auth_client.get("/api/v1/notification-logs/unread-count")
        assert resp.status_code == 200
        assert resp.json()["data"]["unread_count"] == 0

    @pytest.mark.integration
    async def test_unread_count_after_mark_all_read(
        self, auth_client, test_user, db_session
    ):
        """未读数量：全部标记已读后返回 0"""
        znx = await _get_znx_channel(db_session, test_user.id)
        for _ in range(3):
            await _create_notification_log(db_session, test_user.id, znx.id, status=2)
        # 全部标记已读
        resp = await auth_client.put("/api/v1/notification-logs/read-all")
        assert resp.status_code == 200
        assert resp.json()["data"]["updated_count"] == 3
        # 查询未读数量 → 0
        resp = await auth_client.get("/api/v1/notification-logs/unread-count")
        assert resp.status_code == 200
        assert resp.json()["data"]["unread_count"] == 0


# ===== 站内信：标记已读 =====


class TestMarkAsRead:
    """站内信标记已读"""

    @pytest.mark.integration
    async def test_mark_as_read_success(self, auth_client, test_user, db_session):
        """标记已读成功：状态从未读变为已读"""
        znx = await _get_znx_channel(db_session, test_user.id)
        log = await _create_notification_log(
            db_session, test_user.id, znx.id, status=2
        )
        resp = await auth_client.put(
            "/api/v1/notification-logs/read", json={"log_id": log.id}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["msg"] == "已标记为已读"
        data = body["data"]
        assert data["id"] == log.id
        assert data["status"] == 0
        assert data["is_unread"] is False

    @pytest.mark.integration
    async def test_mark_already_read_no_error(self, auth_client, test_user, db_session):
        """标记已读：已读记录重复标记不报错"""
        znx = await _get_znx_channel(db_session, test_user.id)
        log = await _create_notification_log(
            db_session, test_user.id, znx.id, status=0  # 已读
        )
        resp = await auth_client.put(
            "/api/v1/notification-logs/read", json={"log_id": log.id}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_unread"] is False

    @pytest.mark.integration
    async def test_mark_nonexistent_log(self, auth_client, test_user):
        """标记已读：不存在的消息返回 400"""
        resp = await auth_client.put(
            "/api/v1/notification-logs/read", json={"log_id": 99999}
        )
        assert resp.status_code == 400
        assert "不存在" in resp.json()["detail"]

    @pytest.mark.integration
    async def test_mark_log_belonging_to_another_user(
        self, auth_client, test_user, db_session
    ):
        """标记已读：其他用户的消息返回 400"""
        # 创建另一个用户及其站内信记录
        other_user, other_channel = await _create_another_user(db_session)
        other_log = await _create_notification_log(
            db_session, other_user.id, other_channel.id, status=2
        )
        # 当前用户尝试标记别人的消息 → 400
        resp = await auth_client.put(
            "/api/v1/notification-logs/read", json={"log_id": other_log.id}
        )
        assert resp.status_code == 400
        assert "无权" in resp.json()["detail"]


# ===== 站内信：全部标记已读 =====


class TestMarkAllAsRead:
    """站内信全部标记已读"""

    @pytest.mark.integration
    async def test_mark_all_as_read_success(self, auth_client, test_user, db_session):
        """全部标记已读：返回更新的记录数"""
        znx = await _get_znx_channel(db_session, test_user.id)
        # 创建 5 条未读
        for _ in range(5):
            await _create_notification_log(db_session, test_user.id, znx.id, status=2)
        resp = await auth_client.put("/api/v1/notification-logs/read-all")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["msg"] == "已全部标记为已读"
        assert body["data"]["updated_count"] == 5

    @pytest.mark.integration
    async def test_mark_all_as_read_when_none(self, auth_client, test_user):
        """全部标记已读：无未读记录时返回 updated_count=0"""
        resp = await auth_client.put("/api/v1/notification-logs/read-all")
        assert resp.status_code == 200
        assert resp.json()["data"]["updated_count"] == 0


# ===== 未认证访问 =====


class TestUnauthenticatedAccess:
    """未认证请求返回 401"""

    @pytest.mark.integration
    async def test_channels_list_unauthenticated(self, client):
        """通知渠道列表：未登录返回 401"""
        resp = await client.get("/api/v1/notification-channels/list")
        assert resp.status_code == 401

    @pytest.mark.integration
    async def test_logs_list_unauthenticated(self, client):
        """站内信列表：未登录返回 401"""
        resp = await client.get("/api/v1/notification-logs/list")
        assert resp.status_code == 401
