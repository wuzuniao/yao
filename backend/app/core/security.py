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

import ipaddress
import re
import socket
from typing import Any

import jwt

from . import auth_client
from .config import settings

# === 正则常量 ===
# 控制字符（保留 \t 和 \n；\r 一律剥离，防邮件头 CRLF 注入），用于输入净化
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\r]")

# SMTP 端口白名单（主流邮箱 SSL/STARTTLS 端口；收紧任意端口，防借发信探测内网服务）
SMTP_ALLOWED_PORTS = frozenset({25, 465, 587, 994})

# JWT 签名算法（auth 服务签发，本服务仅持公钥本地验签）
_JWT_ALGORITHM = "RS256"

# 令牌校验时间容差（秒）：容忍本服务与 auth 服务间的轻微时钟偏差
_JWT_LEEWAY_SECONDS = 60


class Security:
    """安全验证类 - 业务后端安全相关验证逻辑的唯一入口"""

    # ===== 邮箱安全（邮件通知渠道的发件邮箱校验；用户账号邮箱校验已迁 auth 服务） =====

    @staticmethod
    def validate_email(email: str) -> str:
        """校验邮箱格式（用于非 EmailStr 的手动校验场景；单行，防邮件头注入）"""
        if not isinstance(email, str):
            raise ValueError("邮箱必须为字符串")
        email = Security.sanitize_string(
            email, max_length=254, field_name="邮箱", allow_newline=False
        )
        if "@" not in email:
            raise ValueError("邮箱地址格式不正确")
        return email

    # ===== SMTP 安全 =====

    @staticmethod
    def validate_smtp_host(host: str) -> str:
        """校验 SMTP 服务器地址（单行，禁止换行）"""
        host = Security.sanitize_string(
            host, max_length=255, field_name="SMTP服务器地址", allow_newline=False
        )
        if not host:
            raise ValueError("SMTP服务器地址不能为空")
        return host

    @staticmethod
    def validate_smtp_port(port: int) -> int:
        """校验 SMTP 端口号（白名单 25/465/587/994，防任意内网端口探测）"""
        if not isinstance(port, int):
            raise ValueError("SMTP端口必须为整数")
        if port not in SMTP_ALLOWED_PORTS:
            raise ValueError("SMTP端口仅支持 25、465、587、994（主流邮箱 SSL/STARTTLS 端口）")
        return port

    @staticmethod
    def validate_smtp_target(host: str) -> str:
        """
        SMTP 出网目标安全校验（防 SSRF），并返回通过校验的解析 IP：
        - DNS 解析 host，任一解析结果命中内网/环回/链路本地/保留地址即拒绝
        - 校验通过后返回首个公网解析结果，供调用方固定 IP 建连
          （防 DNS rebinding TOCTOU：校验与实连若各自独立解析，间隙可被
          恶意域名换绑内网地址——调用方应直连本方法返回的 IP，2026-10-25 安全加固）
        - 同步阻塞（含 DNS 查询），Web 层调用须置于 asyncio.to_thread，
          调度器发信路径已在工作线程中可直接调用
        - IP 字面量（如 192.168.1.1、127.0.0.1）经 getaddrinfo 原样返回，同样被覆盖
        :param host: SMTP 服务器地址
        :return: 通过安全校验的解析 IP（首个公网结果）
        :raises ValueError: 域名无法解析、全部结果非 IP 或解析到内网/保留地址
        """
        try:
            addr_infos = socket.getaddrinfo(host, None)
        except socket.gaierror:
            raise ValueError("SMTP服务器地址无法解析，请检查后重试")
        first_public: str | None = None
        for info in addr_infos:
            # IPv6 地址可能带 %zone 后缀（如 fe80::1%eth0），取 % 前段判断
            raw_addr = info[4][0].split("%")[0]
            try:
                ip = ipaddress.ip_address(raw_addr)
            except ValueError:
                continue
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_unspecified
            ):
                raise ValueError("SMTP服务器地址不允许指向内网或保留地址")
            if first_public is None:
                first_public = raw_addr
        if first_public is None:
            raise ValueError("SMTP服务器地址无法解析，请检查后重试")
        return first_public

    # ===== 通用输入实体化 =====

    @staticmethod
    def sanitize_string(
        value: str,
        max_length: int = 500,
        field_name: str = "输入",
        allow_newline: bool = True,
    ) -> str:
        """
        字符串输入实体化（净化）：
        1. 去除控制字符（null字节、\r 等，保留 \\t；\\n 默认保留供多行备注使用）
        2. 去除首尾空白
        3. 校验长度
        4. allow_newline=False 时拒绝换行（用于会进入邮件头等单行语义的字段，防头注入）
        """
        if not isinstance(value, str):
            raise ValueError(f"{field_name}必须为字符串")
        value = _CONTROL_CHARS.sub("", value)
        value = value.strip()
        if not allow_newline and "\n" in value:
            raise ValueError(f"{field_name}不能包含换行")
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
        - 校验项：RS256 签名 / iss（=AUTH_ISSUER）/ exp（leeway 60s）/ sub 存在 / azp（=AUTH_CLIENT_ID）
        :param token: JWT 字符串（前端经 Authorization: Bearer 携带）
        :return: 解码后的 payload（含 iss/sub/roles/azp/jti/iat/exp）
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

        # 5. azp（authorized party）校验（2026-10-25 安全修复）：
        #    令牌须为本项目（AUTH_CLIENT_ID）签发，防止同 auth 下其他 client 的令牌
        #    访问本项目接口（token confusion）；auth 签发时以 client_id 写入 azp
        if payload.get("azp") != settings.AUTH_CLIENT_ID:
            raise ValueError("登录凭证不适用于本项目")
        return payload
