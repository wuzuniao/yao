"""
单元测试补充：覆盖核心模块的异常分支与边界条件
--------------------------------------------------------------------------
覆盖目标：
- security.py: verify_access_token 的空 token/无效 token/无 sub 分支
- crypto.py: _get_key 的密钥未配置、长度错误分支
- deps.py: get_current_user_id 的无 token/格式错误/无效 token/user_id 非正/撤销比对分支
- auth_client.py: is_revoked 本地比对、撤销增量合并逻辑
- schemas/plan.py: notification_times 格式错误分支
"""
import time

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from unittest.mock import patch

from app.core import config
from app.core.deps import get_current_user_id
from app.core.security import Security
from app.utils import crypto
from app.schemas.plan import CreatePlan
from tests import rsa_keys


# ===== security.py 异常分支 =====


class TestSecurityCoverage:
    """Security 类异常分支覆盖"""

    @pytest.mark.asyncio
    async def test_verify_token_empty(self):
        """verify_access_token: 空 token 应抛出 ValueError"""
        with pytest.raises(ValueError, match="令牌不能为空"):
            await Security.verify_access_token("")

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self):
        """verify_access_token: 无效 token 应抛出 ValueError"""
        with pytest.raises(ValueError, match="登录凭证无效"):
            await Security.verify_access_token("invalid.token.here")

    @pytest.mark.asyncio
    async def test_verify_token_no_sub(self):
        """verify_access_token: payload 无 sub 字段应抛出 ValueError"""
        import jwt as pyjwt

        payload = {
            "iss": rsa_keys.TEST_ISSUER,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = pyjwt.encode(
            payload, rsa_keys.PRIVATE_PEM, algorithm="RS256", headers={"kid": rsa_keys.KID}
        )
        with pytest.raises(ValueError, match="登录凭证格式不正确"):
            await Security.verify_access_token(token)


# ===== crypto.py 异常分支 =====


class TestCryptoCoverage:
    """crypto 模块异常分支覆盖"""

    def test_get_key_not_configured(self):
        """_get_key: ENCRYPTION_SECRET_KEY 未配置应抛出 RuntimeError"""
        with patch.object(config.settings, "ENCRYPTION_SECRET_KEY", ""):
            with pytest.raises(RuntimeError, match="未配置 ENCRYPTION_SECRET_KEY"):
                crypto._get_key()

    def test_get_key_wrong_length(self):
        """_get_key: 密钥长度非 32 字节应抛出 RuntimeError"""
        # base64 编码的 16 字节（非 32 字节）
        import base64

        short_key = base64.b64encode(b"0" * 16).decode()
        with patch.object(config.settings, "ENCRYPTION_SECRET_KEY", short_key):
            with pytest.raises(RuntimeError, match="必须是 base64 编码的 32 字节密钥"):
                crypto._get_key()


# ===== deps.py 异常分支 =====


class TestDepsCoverage:
    """get_current_user_id 依赖异常分支覆盖（不触网的分支）"""

    @pytest.mark.asyncio
    async def test_no_authorization(self):
        """无 Authorization 头应返回 401"""
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(authorization=None)
        assert exc.value.status_code == 401
        assert "未登录" in exc.value.detail

    @pytest.mark.asyncio
    async def test_invalid_format(self):
        """Authorization 格式错误（非 Bearer 前缀）应返回 401"""
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(authorization="InvalidFormat")
        assert exc.value.status_code == 401
        assert "格式不正确" in exc.value.detail

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Bearer 无效 token 应返回 401"""
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(authorization="Bearer invalid.token.here")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_token_user_id_non_positive(self):
        """token 中 user_id <= 0 应返回 401"""
        token = rsa_keys.sign_token(0)
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(authorization=f"Bearer {token}")
        assert exc.value.status_code == 401
        assert "无效" in exc.value.detail

    @pytest.mark.asyncio
    async def test_token_sub_not_int(self):
        """token 中 sub 非整数应返回 401（覆盖 deps.py except ValueError 分支）"""
        import jwt as pyjwt

        payload = {
            "iss": rsa_keys.TEST_ISSUER,
            "sub": "not-an-int",
            "role": 0,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = pyjwt.encode(
            payload, rsa_keys.PRIVATE_PEM, algorithm="RS256", headers={"kid": rsa_keys.KID}
        )
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(authorization=f"Bearer {token}")
        assert exc.value.status_code == 401
        assert "格式不正确" in exc.value.detail

    @pytest.mark.asyncio
    async def test_token_revoked(self):
        """令牌 iat 早于该用户最新撤销时刻应返回 401（本地撤销比对，零网络调用）"""
        from app.core import auth_client

        user_id = 888001
        now = int(time.time())
        # 模拟后台撤销同步已合并该用户的撤销记录
        auth_client._revocations[user_id] = float(now)
        # 令牌签发于撤销之前
        token = rsa_keys.sign_token(user_id, issued_at=now - 100)
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(authorization=f"Bearer {token}")
        assert exc.value.status_code == 401
        assert "登录已失效" in exc.value.detail

    @pytest.mark.asyncio
    async def test_admin_role_required(self):
        """普通用户令牌访问管理员依赖应返回 403（role 取自 claims）"""
        # get_current_admin 经 _authenticate_and_validate(require_admin=True) 校验 role
        from app.core.deps import get_current_admin

        token = rsa_keys.sign_token(1, role=0)
        with pytest.raises(HTTPException) as exc:
            await get_current_admin(authorization=f"Bearer {token}")
        assert exc.value.status_code == 403
        # 管理员令牌应通过
        admin_token = rsa_keys.sign_token(1, role=7)
        assert await get_current_admin(authorization=f"Bearer {admin_token}") == 1


# ===== auth_client.py 撤销同步逻辑 =====


class TestAuthClientCoverage:
    """auth_client 撤销比对与增量合并分支覆盖（不触网）"""

    def test_is_revoked(self):
        """is_revoked: iat 早于撤销时刻 → True；晚于 → False；无记录 → False"""
        from app.core import auth_client

        auth_client._revocations[1] = 1000.0
        assert auth_client.is_revoked(1, 999) is True
        assert auth_client.is_revoked(1, 1000) is False
        assert auth_client.is_revoked(2, 999) is False

    @pytest.mark.asyncio
    async def test_pull_revocations_network_failure(self):
        """pull_revocations: auth 不可达时返回 0 且不抛异常（保留旧水位重试）"""
        from app.core import auth_client

        assert await auth_client.pull_revocations() == 0

    def test_parse_shanghai_iso(self):
        """_parse_shanghai_iso: 无时区按上海、带时区按其时区、非法返回 None"""
        from app.core import auth_client

        # 2026-01-01T08:00:00 上海 = 2026-01-01T00:00:00 UTC = 1767225600
        expected = 1767225600.0
        # 无时区：视为上海（UTC+8）
        assert auth_client._parse_shanghai_iso("2026-01-01T08:00:00") == expected
        # 带 +08:00 时区
        assert auth_client._parse_shanghai_iso("2026-01-01T08:00:00+08:00") == expected
        # 带 UTC 时区（00:00 UTC = 08:00 上海）
        assert auth_client._parse_shanghai_iso("2026-01-01T00:00:00Z") == expected
        # 非法输入
        assert auth_client._parse_shanghai_iso("not-a-date") is None


# ===== schemas/plan.py 异常分支 =====


class TestSchemaPlanCoverage:
    """CreatePlan schema notification_times 格式校验分支覆盖"""

    def test_notification_times_invalid_format(self):
        """notification_times 中时间格式错误（parts 数量不在 2-3 之间）应抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            CreatePlan(
                name="测试计划",
                remark="",
                start_date="2026-01-01",
                end_date="2026-12-31",
                notification_times=[{"time": "08"}],  # 格式错误：只有 1 个 part
                channel_ids=[1],
            )
        assert "时间格式不正确" in str(exc_info.value)
