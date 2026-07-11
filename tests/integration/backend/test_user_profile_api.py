"""
用户资料管理 API 集成测试
- 个人信息查询、签名/头像/用户名修改
- 密码修改与设置
- 邮箱绑定与修改
- 账号删除计划与取消
"""
import pytest

from app.core.security import Security
from app.models.user import User as UserModel
from app.services.user_service import _verification_codes

pytestmark = pytest.mark.integration

API_PREFIX = "/api/v1/users"


@pytest.fixture(autouse=True)
def clear_verification_codes():
    """每个测试前清空验证码缓存，确保测试隔离"""
    _verification_codes.clear()


async def _create_wechat_user(db_session, client):
    """创建无密码无邮箱的微信登录用户，并为其设置认证头，返回用户对象"""
    user = UserModel(
        username="微信用户",
        email=None,
        password_hash=None,
        avatar_url="lan",
        signature="微信签名",
        status=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    client.headers["Authorization"] = f"Bearer {Security.generate_token(user.id)}"
    return user


class TestGetUserInfo:
    """GET /users/info - 当前用户信息查询"""

    async def test_get_user_info_success(self, auth_client, test_user):
        """有效 token 返回当前用户完整信息"""
        resp = await auth_client.get(f"{API_PREFIX}/info")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["id"] == test_user.id
        assert data["username"] == "测试用户"
        assert data["signature"] == "测试签名"
        assert data["avatar_url"] == "hei"
        assert data["email"] == "test@example.com"
        assert data["has_password"] is True
        assert data["status"] == 1

    async def test_get_user_info_without_token(self, client):
        """未携带 Authorization 头返回 401"""
        resp = await client.get(f"{API_PREFIX}/info")
        assert resp.status_code == 401

    async def test_get_user_info_invalid_token(self, client):
        """无效 token 返回 401"""
        client.headers["Authorization"] = "Bearer invalid.token.here"
        resp = await client.get(f"{API_PREFIX}/info")
        assert resp.status_code == 401


class TestUpdateSignature:
    """PUT /users/update-signature - 更新签名"""

    async def test_update_signature_success(self, auth_client):
        """更新签名成功，响应中返回新签名"""
        resp = await auth_client.put(
            f"{API_PREFIX}/update-signature",
            json={"signature": "新签名"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["signature"] == "新签名"


class TestChangePassword:
    """PUT /users/change-password - 修改密码"""

    async def test_change_password_success(self, auth_client):
        """旧密码正确时修改密码成功"""
        resp = await auth_client.put(
            f"{API_PREFIX}/change-password",
            json={"old_password": "Test1234!", "new_password": "NewPass123!"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["id"] is not None

    async def test_change_password_wrong_old(self, auth_client):
        """旧密码错误返回 400"""
        resp = await auth_client.put(
            f"{API_PREFIX}/change-password",
            json={"old_password": "WrongPass1!", "new_password": "NewPass123!"},
        )
        assert resp.status_code == 400
        assert "旧密码" in resp.json()["detail"]

    async def test_login_with_new_password(self, auth_client, client):
        """修改密码后可使用新密码登录"""
        # 1. 修改密码
        resp = await auth_client.put(
            f"{API_PREFIX}/change-password",
            json={"old_password": "Test1234!", "new_password": "NewPass123!"},
        )
        assert resp.status_code == 200
        # 2. 使用新密码登录（login 接口不校验 auth 头，复用同一 client 即可）
        resp = await client.post(
            f"{API_PREFIX}/login",
            json={"username": "测试用户", "password": "NewPass123!"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["access_token"]


class TestUpdateAvatar:
    """PUT /users/update-avatar - 更新头像"""

    async def test_update_avatar_success(self, auth_client):
        """更新头像成功，响应中返回新头像地址"""
        resp = await auth_client.put(
            f"{API_PREFIX}/update-avatar",
            json={"avatar_url": "lan"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["avatar_url"] == "lan"


class TestUpdateUsername:
    """PUT /users/update-username - 更新用户名"""

    async def test_update_username_success(self, auth_client):
        """更新用户名成功，响应中返回新用户名"""
        resp = await auth_client.put(
            f"{API_PREFIX}/update-username",
            json={"new_username": "新用户名"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["username"] == "新用户名"

    async def test_update_username_taken(self, auth_client, test_user, db_session):
        """目标用户名已被其他用户占用时返回 400"""
        # 创建另一个用户占用目标用户名
        other = UserModel(
            username="已占用名",
            email="other@example.com",
            password_hash=Security.hash_password("Other123!"),
            avatar_url="hei",
            signature="",
            status=1,
        )
        db_session.add(other)
        await db_session.commit()
        resp = await auth_client.put(
            f"{API_PREFIX}/update-username",
            json={"new_username": "已占用名"},
        )
        assert resp.status_code == 400
        assert "用户名已被占用" in resp.json()["detail"]


class TestAccountDeletion:
    """POST /users/schedule-deletion 与 /users/cancel-deletion - 账号删除计划"""

    async def test_schedule_deletion_success(self, auth_client):
        """预约删除账号成功，status 置为 0"""
        resp = await auth_client.post(f"{API_PREFIX}/schedule-deletion", json={})
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["status"] == 0

    async def test_cancel_deletion_success(self, auth_client):
        """取消删除账号成功，status 恢复为 1"""
        # 1. 先预约删除
        resp = await auth_client.post(f"{API_PREFIX}/schedule-deletion", json={})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == 0
        # 2. 取消删除
        resp = await auth_client.post(f"{API_PREFIX}/cancel-deletion", json={})
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["status"] == 1


class TestSetPassword:
    """PUT /users/set-password - 设置密码（用于无密码用户）"""

    async def test_set_password_success(self, client, db_session):
        """无密码用户首次设置密码成功，且可使用新密码登录"""
        user = await _create_wechat_user(db_session, client)
        resp = await client.put(
            f"{API_PREFIX}/set-password",
            json={"new_password": "FirstPass123!"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["id"] == user.id
        # 验证新密码可用于登录
        resp = await client.post(
            f"{API_PREFIX}/login",
            json={"username": "微信用户", "password": "FirstPass123!"},
        )
        assert resp.status_code == 200

    async def test_set_password_already_has_password(self, auth_client):
        """已有密码的用户设置密码返回 400"""
        resp = await auth_client.put(
            f"{API_PREFIX}/set-password",
            json={"new_password": "FirstPass123!"},
        )
        assert resp.status_code == 400
        assert "已设置密码" in resp.json()["detail"]


class TestBindEmail:
    """PUT /users/bind-email - 绑定邮箱（用于无邮箱用户）"""

    async def test_bind_email_success(self, client, db_session):
        """无邮箱用户绑定新邮箱成功，响应中返回绑定后的邮箱"""
        await _create_wechat_user(db_session, client)
        # 1. 先发送新邮箱验证码（绑定场景允许邮箱已存在以触发账号合并）
        resp = await client.post(
            f"{API_PREFIX}/send-change-email-new-code",
            json={"new_email": "bound@example.com", "allow_existing": True},
        )
        assert resp.status_code == 200
        # 2. 从验证码缓存中取出验证码
        code = _verification_codes["bound@example.com:change_new"][0]
        # 3. 绑定邮箱
        resp = await client.put(
            f"{API_PREFIX}/bind-email",
            json={"new_email": "bound@example.com", "new_code": code},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["email"] == "bound@example.com"

    async def test_bind_email_already_has_email(self, auth_client):
        """已绑定邮箱的用户再次绑定返回 400"""
        resp = await auth_client.put(
            f"{API_PREFIX}/bind-email",
            json={"new_email": "bound@example.com", "new_code": "123456"},
        )
        assert resp.status_code == 400
        assert "已绑定邮箱" in resp.json()["detail"]


class TestChangeEmail:
    """PUT /users/change-email - 修改邮箱（需验证旧邮箱与新邮箱验证码）"""

    async def test_change_email_full_flow(self, auth_client, test_user):
        """完整修改邮箱流程：发送旧邮箱验证码 → 发送新邮箱验证码 → 修改邮箱"""
        # 1. 发送旧邮箱验证码
        resp = await auth_client.post(
            f"{API_PREFIX}/send-change-email-old-code", json={}
        )
        assert resp.status_code == 200
        old_code = _verification_codes[f"{test_user.email}:change_old"][0]
        # 2. 发送新邮箱验证码
        resp = await auth_client.post(
            f"{API_PREFIX}/send-change-email-new-code",
            json={"new_email": "newemail@example.com", "allow_existing": False},
        )
        assert resp.status_code == 200
        new_code = _verification_codes["newemail@example.com:change_new"][0]
        # 3. 修改邮箱
        resp = await auth_client.put(
            f"{API_PREFIX}/change-email",
            json={
                "old_code": old_code,
                "new_email": "newemail@example.com",
                "new_code": new_code,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["email"] == "newemail@example.com"

    async def test_change_email_wrong_old_code(self, auth_client, test_user):
        """旧邮箱验证码错误返回 400"""
        # 1. 发送旧邮箱验证码（生成真实验证码）
        resp = await auth_client.post(
            f"{API_PREFIX}/send-change-email-old-code", json={}
        )
        assert resp.status_code == 200
        real_old_code = _verification_codes[f"{test_user.email}:change_old"][0]
        wrong_old_code = "000000" if real_old_code != "000000" else "111111"
        # 2. 发送新邮箱验证码
        resp = await auth_client.post(
            f"{API_PREFIX}/send-change-email-new-code",
            json={"new_email": "newemail@example.com", "allow_existing": False},
        )
        assert resp.status_code == 200
        new_code = _verification_codes["newemail@example.com:change_new"][0]
        # 3. 使用错误的旧邮箱验证码修改邮箱
        resp = await auth_client.put(
            f"{API_PREFIX}/change-email",
            json={
                "old_code": wrong_old_code,
                "new_email": "newemail@example.com",
                "new_code": new_code,
            },
        )
        assert resp.status_code == 400
        assert "旧邮箱验证码" in resp.json()["detail"]

    async def test_change_email_wrong_new_code(self, auth_client, test_user):
        """新邮箱验证码错误返回 400"""
        # 1. 发送旧邮箱验证码
        resp = await auth_client.post(
            f"{API_PREFIX}/send-change-email-old-code", json={}
        )
        assert resp.status_code == 200
        old_code = _verification_codes[f"{test_user.email}:change_old"][0]
        # 2. 发送新邮箱验证码（生成真实验证码）
        resp = await auth_client.post(
            f"{API_PREFIX}/send-change-email-new-code",
            json={"new_email": "newemail@example.com", "allow_existing": False},
        )
        assert resp.status_code == 200
        real_new_code = _verification_codes["newemail@example.com:change_new"][0]
        wrong_new_code = "000000" if real_new_code != "000000" else "111111"
        # 3. 旧验证码正确、新验证码错误
        resp = await auth_client.put(
            f"{API_PREFIX}/change-email",
            json={
                "old_code": old_code,
                "new_email": "newemail@example.com",
                "new_code": wrong_new_code,
            },
        )
        assert resp.status_code == 400
        assert "新邮箱验证码" in resp.json()["detail"]

    async def test_send_new_code_to_registered_email(self, auth_client):
        """向已注册邮箱发送新邮箱验证码返回 400（allow_existing=False）"""
        # test_user 自身邮箱已注册
        resp = await auth_client.post(
            f"{API_PREFIX}/send-change-email-new-code",
            json={"new_email": "test@example.com", "allow_existing": False},
        )
        assert resp.status_code == 400
        assert "已被注册" in resp.json()["detail"]


class TestValidationErrors:
    """请求体缺少必填字段返回 422"""

    @pytest.mark.parametrize(
        "method,path,body",
        [
            ("put", "/update-signature", {}),
            ("put", "/change-password", {"old_password": "Test1234!"}),
            ("put", "/update-avatar", {}),
            ("put", "/update-username", {}),
            ("put", "/set-password", {}),
            ("put", "/bind-email", {"new_email": "bound@example.com"}),
            ("put", "/change-email", {}),
            ("post", "/send-change-email-new-code", {}),
        ],
    )
    async def test_missing_required_fields(self, auth_client, method, path, body):
        """缺少必填字段返回 422 校验错误"""
        request = getattr(auth_client, method)
        resp = await request(f"{API_PREFIX}{path}", json=body)
        assert resp.status_code == 422


class TestUnauthenticatedAccess:
    """未认证请求受保护接口返回 401"""

    @pytest.mark.parametrize(
        "method,path,body",
        [
            ("get", "/info", None),
            ("put", "/update-signature", {"signature": "签名"}),
            ("put", "/change-password", {"old_password": "Test1234!", "new_password": "NewPass123!"}),
            ("put", "/update-avatar", {"avatar_url": "lan"}),
            ("put", "/update-username", {"new_username": "新名字"}),
            ("put", "/set-password", {"new_password": "FirstPass123!"}),
            ("post", "/schedule-deletion", {}),
            ("post", "/cancel-deletion", {}),
            ("post", "/send-change-email-old-code", {}),
            ("post", "/send-change-email-new-code", {"new_email": "new@example.com", "allow_existing": False}),
            ("put", "/change-email", {"old_code": "123456", "new_email": "new@example.com", "new_code": "654321"}),
            ("put", "/bind-email", {"new_email": "bound@example.com", "new_code": "123456"}),
        ],
    )
    async def test_unauthenticated_request_returns_401(self, client, method, path, body):
        """未携带 token 访问受保护接口返回 401（请求体合法以排除 422 干扰）"""
        request = getattr(client, method)
        if body is None:
            resp = await request(f"{API_PREFIX}{path}")
        else:
            resp = await request(f"{API_PREFIX}{path}", json=body)
        assert resp.status_code == 401
