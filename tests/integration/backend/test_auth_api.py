"""
认证相关 API 集成测试
- 注册流程：发送验证码 → 注册 → 登录
- 密码找回：发送重置验证码 → 重置密码
- 登录验证：用户名/邮箱 + 密码
"""
import time

import pytest

from app.services.user_service import _verification_codes

pytestmark = pytest.mark.asyncio

API_PREFIX = "/api/v1/users"


# =============================================================================
# 辅助函数
# =============================================================================

def _get_code(email: str, purpose: str) -> str:
    """从验证码暂存字典中提取指定邮箱和用途的验证码"""
    key = f"{email}:{purpose}"
    return _verification_codes[key][0]


def _inject_code(email: str, purpose: str, code: str = "123456") -> str:
    """
    手动注入验证码到暂存字典
    - 用于测试"已注册邮箱"等无法通过 send-code 接口获取验证码的场景
    - 返回注入的验证码，便于后续断言使用
    """
    key = f"{email}:{purpose}"
    _verification_codes[key] = (code, time.time() + 300)
    return code


# =============================================================================
# 注册流程测试
# =============================================================================

async def test_send_code_unregistered_email(client):
    """发送注册验证码 - 未注册邮箱应成功"""
    resp = await client.post(
        f"{API_PREFIX}/send-code", json={"email": "newuser@example.com"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["msg"] == "验证码已发送"
    assert body["data"] is None


async def test_register_full_flow(client):
    """完整注册流程：发送验证码 → 获取验证码 → 注册成功"""
    email = "newuser@example.com"
    # 1. 发送验证码
    resp = await client.post(f"{API_PREFIX}/send-code", json={"email": email})
    assert resp.status_code == 200
    # 2. 从暂存字典提取验证码（绕过邮件发送）
    code = _get_code(email, "register")
    # 3. 注册
    resp = await client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "新用户",
            "password": "NewPass123!",
            "email": email,
            "code": code,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["msg"] == "注册成功"
    data = body["data"]
    assert data["username"] == "新用户"
    assert data["email"] == email
    assert data["access_token"]  # 非空字符串


async def test_register_wrong_code(client):
    """注册 - 验证码错误应返回 400"""
    email = "newuser@example.com"
    await client.post(f"{API_PREFIX}/send-code", json={"email": email})
    real_code = _get_code(email, "register")
    # 构造一个必定不同的错误验证码
    wrong_code = "000000" if real_code != "000000" else "111111"
    resp = await client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "新用户",
            "password": "NewPass123!",
            "email": email,
            "code": wrong_code,
        },
    )
    assert resp.status_code == 400
    assert "验证码错误" in resp.json()["detail"]


async def test_register_duplicate_username(client, test_user):
    """注册 - 用户名已存在应返回 400"""
    email = "newuser@example.com"
    # 向新邮箱发送验证码（test_user 的邮箱已被注册，无法通过 send-code 获取）
    await client.post(f"{API_PREFIX}/send-code", json={"email": email})
    code = _get_code(email, "register")
    # 使用与 test_user 相同的用户名
    resp = await client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "测试用户",
            "password": "NewPass123!",
            "email": email,
            "code": code,
        },
    )
    assert resp.status_code == 400
    assert "用户名已被注册" in resp.json()["detail"]


async def test_register_duplicate_email(client, test_user):
    """注册 - 邮箱已存在应返回 400"""
    email = "test@example.com"  # test_user 的邮箱
    # 已注册邮箱无法通过 send-code 获取验证码，手动注入验证码以隔离"邮箱重复"校验
    code = _inject_code(email, "register")
    resp = await client.post(
        f"{API_PREFIX}/register",
        json={
            "username": "另一个新用户",
            "password": "NewPass123!",
            "email": email,
            "code": code,
        },
    )
    assert resp.status_code == 400
    assert "邮箱已被注册" in resp.json()["detail"]


async def test_send_code_registered_email(client, test_user):
    """发送注册验证码 - 已注册邮箱应返回 400"""
    resp = await client.post(
        f"{API_PREFIX}/send-code", json={"email": "test@example.com"}
    )
    assert resp.status_code == 400
    assert "已被注册" in resp.json()["detail"]


# =============================================================================
# 登录测试
# =============================================================================

async def test_login_by_username(client, test_user):
    """使用用户名登录 - 成功"""
    resp = await client.post(
        f"{API_PREFIX}/login",
        json={"username": "测试用户", "password": "Test1234!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["msg"] == "登录成功"
    data = body["data"]
    assert data["username"] == "测试用户"
    assert data["email"] == "test@example.com"
    assert data["access_token"]


async def test_login_by_email(client, test_user):
    """使用邮箱登录 - 成功"""
    resp = await client.post(
        f"{API_PREFIX}/login",
        json={"username": "test@example.com", "password": "Test1234!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["msg"] == "登录成功"
    assert body["data"]["username"] == "测试用户"


async def test_login_wrong_password(client, test_user):
    """登录 - 密码错误应返回 400"""
    resp = await client.post(
        f"{API_PREFIX}/login",
        json={"username": "测试用户", "password": "WrongPass123!"},
    )
    assert resp.status_code == 400
    assert "密码错误" in resp.json()["detail"]


async def test_login_nonexistent_user(client):
    """登录 - 用户不存在应返回 400"""
    resp = await client.post(
        f"{API_PREFIX}/login",
        json={"username": "不存在用户", "password": "Test1234!"},
    )
    assert resp.status_code == 400
    assert "用户不存在" in resp.json()["detail"]


# =============================================================================
# 密码找回测试
# =============================================================================

async def test_send_reset_code_registered_email(client, test_user):
    """发送重置密码验证码 - 已注册邮箱应成功"""
    resp = await client.post(
        f"{API_PREFIX}/send-reset-code", json={"email": "test@example.com"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["msg"] == "验证码已发送"


async def test_send_reset_code_unregistered_email(client):
    """发送重置密码验证码 - 未注册邮箱应返回 400"""
    resp = await client.post(
        f"{API_PREFIX}/send-reset-code", json={"email": "unknown@example.com"}
    )
    assert resp.status_code == 400
    assert "未注册" in resp.json()["detail"]


async def test_reset_password_full_flow(client, test_user):
    """完整密码重置流程：发送重置验证码 → 获取验证码 → 重置密码成功"""
    email = "test@example.com"
    # 1. 发送重置验证码
    resp = await client.post(
        f"{API_PREFIX}/send-reset-code", json={"email": email}
    )
    assert resp.status_code == 200
    # 2. 提取验证码
    code = _get_code(email, "reset")
    # 3. 重置密码
    resp = await client.post(
        f"{API_PREFIX}/reset-password",
        json={
            "email": email,
            "code": code,
            "new_password": "NewPass456!",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["msg"] == "密码重置成功"
    data = body["data"]
    assert data["email"] == email
    assert data["access_token"]


async def test_reset_password_wrong_code(client, test_user):
    """重置密码 - 验证码错误应返回 400"""
    email = "test@example.com"
    await client.post(f"{API_PREFIX}/send-reset-code", json={"email": email})
    real_code = _get_code(email, "reset")
    wrong_code = "000000" if real_code != "000000" else "111111"
    resp = await client.post(
        f"{API_PREFIX}/reset-password",
        json={
            "email": email,
            "code": wrong_code,
            "new_password": "NewPass456!",
        },
    )
    assert resp.status_code == 400
    assert "验证码错误" in resp.json()["detail"]


async def test_login_after_password_reset(client, test_user):
    """重置密码后 - 新密码可登录，旧密码不可登录"""
    email = "test@example.com"
    new_password = "NewPass456!"
    # 1. 发送重置验证码并重置密码
    await client.post(f"{API_PREFIX}/send-reset-code", json={"email": email})
    code = _get_code(email, "reset")
    resp = await client.post(
        f"{API_PREFIX}/reset-password",
        json={"email": email, "code": code, "new_password": new_password},
    )
    assert resp.status_code == 200
    # 2. 新密码登录应成功
    resp = await client.post(
        f"{API_PREFIX}/login",
        json={"username": "测试用户", "password": new_password},
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 0
    # 3. 旧密码登录应失败
    resp = await client.post(
        f"{API_PREFIX}/login",
        json={"username": "测试用户", "password": "Test1234!"},
    )
    assert resp.status_code == 400
    assert "密码错误" in resp.json()["detail"]


# =============================================================================
# 参数校验测试（422）
# =============================================================================

async def test_register_missing_fields(client):
    """注册 - 缺少必填字段应返回 422"""
    resp = await client.post(f"{API_PREFIX}/register", json={})
    assert resp.status_code == 422


async def test_send_code_missing_email(client):
    """发送验证码 - 缺少邮箱字段应返回 422"""
    resp = await client.post(f"{API_PREFIX}/send-code", json={})
    assert resp.status_code == 422


async def test_send_code_invalid_email_format(client):
    """发送验证码 - 邮箱格式不正确应返回 422"""
    resp = await client.post(
        f"{API_PREFIX}/send-code", json={"email": "not-an-email"}
    )
    assert resp.status_code == 422
