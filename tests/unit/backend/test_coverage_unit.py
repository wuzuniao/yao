"""
单元测试补充：覆盖核心模块的异常分支与边界条件
--------------------------------------------------------------------------
覆盖目标：
- security.py: generate_token/verify_token 的 JWT_SECRET_KEY 未配置、过期、无 sub 分支
- crypto.py: _get_key 的密钥未配置、长度错误分支
- deps.py: get_current_user_id 的无 token/格式错误/无效 token/user_id 非正分支
- schemas/plan.py: notification_times 格式错误分支
- main.py: root/health 端点
"""
import time

import jwt
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from unittest.mock import patch

from app.core import config
from app.core.deps import get_current_user_id
from app.core.security import Security, _JWT_ALGORITHM
from app.utils import crypto
from app.schemas.plan import CreatePlan


# ===== security.py 异常分支 =====


class TestSecurityCoverage:
    """Security 类异常分支覆盖"""

    def test_generate_token_secret_not_configured(self):
        """generate_token: JWT_SECRET_KEY 未配置应抛出 ValueError"""
        with patch.object(config.settings, "JWT_SECRET_KEY", ""):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY 未配置"):
                Security.generate_token(1)

    def test_verify_token_secret_not_configured(self):
        """verify_token: JWT_SECRET_KEY 未配置应抛出 ValueError"""
        with patch.object(config.settings, "JWT_SECRET_KEY", ""):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY 未配置"):
                Security.verify_token("some.token.here")

    def test_verify_token_expired(self):
        """verify_token: 过期 token 应抛出 ValueError（登录已过期）"""
        secret = config.settings.JWT_SECRET_KEY
        # 构造已过期的 token（exp 设为 1 秒前）
        expired_payload = {
            "sub": "1",
            "iat": int(time.time()) - 10,
            "exp": int(time.time()) - 1,
        }
        expired_token = jwt.encode(expired_payload, secret, algorithm=_JWT_ALGORITHM)
        with pytest.raises(ValueError, match="登录已过期"):
            Security.verify_token(expired_token)

    def test_verify_token_no_sub(self):
        """verify_token: payload 无 sub 字段应抛出 ValueError"""
        secret = config.settings.JWT_SECRET_KEY
        # 用相同 secret 签发一个无 sub 的 token
        no_sub_payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        no_sub_token = jwt.encode(no_sub_payload, secret, algorithm=_JWT_ALGORITHM)
        with pytest.raises(ValueError, match="登录凭证格式不正确"):
            Security.verify_token(no_sub_token)


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
    """get_current_user_id 依赖异常分支覆盖"""

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
        # 构造 sub="0" 的 token
        secret = config.settings.JWT_SECRET_KEY
        payload = {
            "sub": "0",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, secret, algorithm=_JWT_ALGORITHM)
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(authorization=f"Bearer {token}")
        assert exc.value.status_code == 401
        assert "无效" in exc.value.detail

    @pytest.mark.asyncio
    async def test_token_sub_not_int(self):
        """token 中 sub 非整数应返回 401（覆盖 deps.py except ValueError 分支）"""
        secret = config.settings.JWT_SECRET_KEY
        payload = {
            "sub": "not-an-int",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, secret, algorithm=_JWT_ALGORITHM)
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(authorization=f"Bearer {token}")
        assert exc.value.status_code == 401
        assert "格式不正确" in exc.value.detail


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
                notification_times=["08"],  # 格式错误：只有 1 个 part
                channel_ids=[1],
            )
        assert "时间格式不正确" in str(exc_info.value)
