"""
安全验证类 - 集中管理业务后端安全相关验证逻辑
--------------------------------------------------------------------------
拆分说明（用户模块独立为 auth 服务后）：
- 密码/用户名/验证码/邮箱/头像校验与 JWT 签发已随用户模块迁移至 auth 服务；
- 本类仅保留业务 Schema 仍需的通用校验（净化/正整数/SMTP），
  并新增 verify_access_token：对 auth 签发的 RS256 access_token 做本地验签
  （JWKS 公钥经 auth_client 缓存；issuer=AUTH_ISSUER；零逐请求网络调用）。
"""
from __future__ import annotations

import re
from typing import Any

import jwt

from . import auth_client
from .config import settings

# === 正则常量 ===
# 控制字符（保留 \t 和 \n），用于输入净化
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# JWT 签名算法（auth 服务签发，本服务仅持公钥本地验签）
_JWT_ALGORITHM = "RS256"

# 令牌校验时间容差（秒）：容忍本服务与 auth 服务间的轻微时钟偏差
_JWT_LEEWAY_SECONDS = 60


class Security:
    """安全验证类 - 业务后端安全相关验证逻辑的唯一入口"""

    # ===== 邮箱安全（邮件通知渠道的发件邮箱校验；用户账号邮箱校验已迁 auth 服务） =====

    @staticmethod
    def validate_email(email: str) -> str:
        """校验邮箱格式（用于非 EmailStr 的手动校验场景）"""
        if not isinstance(email, str):
            raise ValueError("邮箱必须为字符串")
        email = Security.sanitize_string(email, max_length=254, field_name="邮箱")
        if "@" not in email:
            raise ValueError("邮箱地址格式不正确")
        return email

    # ===== SMTP 安全 =====

    @staticmethod
    def validate_smtp_host(host: str) -> str:
        """校验 SMTP 服务器地址"""
        host = Security.sanitize_string(host, max_length=255, field_name="SMTP服务器地址")
        if not host:
            raise ValueError("SMTP服务器地址不能为空")
        return host

    @staticmethod
    def validate_smtp_port(port: int) -> int:
        """校验 SMTP 端口号范围（1-65535）"""
        if not isinstance(port, int):
            raise ValueError("SMTP端口必须为整数")
        if port <= 0 or port > 65535:
            raise ValueError("SMTP服务器端口范围 1-65535")
        return port

    # ===== 通用输入实体化 =====

    @staticmethod
    def sanitize_string(
        value: str, max_length: int = 500, field_name: str = "输入"
    ) -> str:
        """
        字符串输入实体化（净化）：
        1. 去除控制字符（null字节等，保留 \\t 和 \\n）
        2. 去除首尾空白
        3. 校验长度
        """
        if not isinstance(value, str):
            raise ValueError(f"{field_name}必须为字符串")
        value = _CONTROL_CHARS.sub("", value)
        value = value.strip()
        if len(value) > max_length:
            raise ValueError(f"{field_name}长度不能超过 {max_length} 个字符")
        return value

    @staticmethod
    def validate_positive_int(value: int, field_name: str = "ID") -> int:
        """校验正整数（用于 user_id、plan_id、channel_id 等）"""
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name}必须为正整数")
        return value

    # ===== access_token 本地验签（RS256，auth 服务签发） =====

    @staticmethod
    async def verify_access_token(token: str) -> dict[str, Any]:
        """
        校验 auth 服务签发的 access_token（纯本地验签，不逐请求调用 auth）
        - 公钥来源：auth_client 的 JWKS 缓存（内存 + 磁盘），未知 kid 自动重拉
        - 校验项：RS256 签名 / iss（=AUTH_ISSUER）/ exp（leeway 60s）/ sub 存在
        :param token: JWT 字符串（前端经 Authorization: Bearer 携带）
        :return: 解码后的 payload（含 iss/sub/role/azp/jti/iat/exp）
        :raises ValueError: token 无效、已过期、签名错误或签发方不匹配
        """
        if not isinstance(token, str) or not token.strip():
            raise ValueError("令牌不能为空")
        # 1. 解析 header 获取 kid（此步不验签）
        try:
            header = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError:
            raise ValueError("登录凭证无效")
        kid = header.get("kid")

        # 2. 按 kid 取公钥（未知 kid 重拉一次 JWKS，支持 auth 密钥轮换）
        key = auth_client.get_public_key(kid)
        if key is None:
            await auth_client.fetch_jwks()
            key = auth_client.get_public_key(kid)
        if key is None:
            raise ValueError("登录凭证无效")

        # 3. 验签 + issuer + 过期校验
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=[_JWT_ALGORITHM],
                issuer=settings.AUTH_ISSUER,
                leeway=_JWT_LEEWAY_SECONDS,
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("登录已过期，请重新登录")
        except jwt.InvalidIssuerError:
            raise ValueError("登录凭证签发方不正确")
        except jwt.InvalidTokenError:
            raise ValueError("登录凭证无效")

        # 4. sub 声明校验
        if "sub" not in payload:
            raise ValueError("登录凭证格式不正确")
        return payload
