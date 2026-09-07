"""
Security 类单元测试
--------------------------------------------------------------------------
覆盖 SMTP 校验、输入净化、正整数校验（业务 Schema 仍用的通用校验），
以及 verify_access_token 的 RS256 本地验签（测试密钥见 tests/rsa_keys.py；
密码/用户名/验证码/邮箱/头像校验已随用户模块迁移至 auth 服务）
"""
import time

import pytest

from app.core.security import Security
from tests import rsa_keys


class TestValidateSmtp:
    """SMTP 校验"""

    @pytest.mark.unit
    def test_valid_host(self):
        assert Security.validate_smtp_host("smtp.example.com") == "smtp.example.com"

    @pytest.mark.unit
    def test_empty_host(self):
        with pytest.raises(ValueError, match="不能为空"):
            Security.validate_smtp_host("   ")

    @pytest.mark.unit
    def test_valid_port(self):
        assert Security.validate_smtp_port(465) == 465

    @pytest.mark.unit
    def test_port_out_of_range(self):
        with pytest.raises(ValueError, match="端口范围"):
            Security.validate_smtp_port(70000)

    @pytest.mark.unit
    def test_port_zero(self):
        with pytest.raises(ValueError, match="端口范围"):
            Security.validate_smtp_port(0)

    @pytest.mark.unit
    def test_port_not_int(self):
        with pytest.raises(ValueError, match="端口必须为整数"):
            Security.validate_smtp_port("465")


class TestSanitizeString:
    """输入净化"""

    @pytest.mark.unit
    def test_strips_whitespace(self):
        assert Security.sanitize_string("  hello  ") == "hello"

    @pytest.mark.unit
    def test_removes_control_chars(self):
        assert Security.sanitize_string("hello\x00world") == "helloworld"

    @pytest.mark.unit
    def test_too_long(self):
        with pytest.raises(ValueError, match="长度不能超过"):
            Security.sanitize_string("a" * 11, max_length=10)

    @pytest.mark.unit
    def test_not_string(self):
        with pytest.raises(ValueError, match="必须为字符串"):
            Security.sanitize_string(123)

    @pytest.mark.unit
    def test_custom_field_name(self):
        with pytest.raises(ValueError, match="自定义字段"):
            Security.sanitize_string("a" * 11, max_length=10, field_name="自定义字段")


class TestValidatePositiveInt:
    """正整数校验"""

    @pytest.mark.unit
    def test_valid_int(self):
        assert Security.validate_positive_int(1) == 1

    @pytest.mark.unit
    def test_zero(self):
        with pytest.raises(ValueError, match="必须为正整数"):
            Security.validate_positive_int(0)

    @pytest.mark.unit
    def test_negative(self):
        with pytest.raises(ValueError, match="必须为正整数"):
            Security.validate_positive_int(-1)

    @pytest.mark.unit
    def test_not_int(self):
        with pytest.raises(ValueError, match="必须为正整数"):
            Security.validate_positive_int("1")


class TestVerifyAccessToken:
    """verify_access_token：auth 服务签发的 RS256 access_token 本地验签"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_token(self):
        token = rsa_keys.sign_token(1, role=7)
        payload = await Security.verify_access_token(token)
        assert payload["sub"] == "1"
        assert payload["role"] == 7
        assert payload["azp"] == "yao"
        assert "iat" in payload
        assert "exp" in payload

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_token(self):
        with pytest.raises(ValueError, match="令牌不能为空"):
            await Security.verify_access_token("")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_token(self):
        with pytest.raises(ValueError, match="登录凭证无效"):
            await Security.verify_access_token("invalid.token.here")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_expired_token(self):
        """过期 token 应抛出 ValueError（登录已过期；须超出 60s 时钟容差）"""
        token = rsa_keys.sign_token(1, expires_in=-120)
        with pytest.raises(ValueError, match="登录已过期"):
            await Security.verify_access_token(token)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_wrong_issuer(self):
        """签发方不匹配的 token 应抛出 ValueError"""
        token = rsa_keys.sign_token(1, issuer="https://someone-else.example.com")
        with pytest.raises(ValueError, match="签发方不正确"):
            await Security.verify_access_token(token)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_forged_signature(self):
        """非 auth（测试密钥）签名的 token 应验签失败"""
        import jwt as pyjwt
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa as rsa_gen

        rogue = rsa_gen.generate_private_key(public_exponent=65537, key_size=2048)
        rogue_pem = rogue.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        payload = {
            "iss": rsa_keys.TEST_ISSUER,
            "sub": "1",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        forged = pyjwt.encode(
            payload, rogue_pem, algorithm="RS256", headers={"kid": rsa_keys.KID}
        )
        with pytest.raises(ValueError, match="登录凭证无效"):
            await Security.verify_access_token(forged)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unknown_kid(self):
        """未知 kid：重拉 JWKS 失败（测试 AUTH_BASE_URL 不可达）后仍无该公钥 → 登录凭证无效"""
        import jwt as pyjwt

        payload = {
            "iss": rsa_keys.TEST_ISSUER,
            "sub": "1",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = pyjwt.encode(
            payload, rsa_keys.PRIVATE_PEM, algorithm="RS256", headers={"kid": "unknown-kid"}
        )
        with pytest.raises(ValueError, match="登录凭证无效"):
            await Security.verify_access_token(token)
