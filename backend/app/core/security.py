"""
安全验证类 - 集中管理所有后端安全相关验证逻辑
--------------------------------------------------------------------------
所有输入数据的实体化（校验+净化）和输出数据的过滤均通过此类完成。
其他类（Schema、Service、API）只做调用，不自行实现安全验证逻辑。
"""
from __future__ import annotations

import re
import time
from typing import Any

import bcrypt
import jwt

from .config import settings

# === 正则常量 ===
# 用户名：仅允许中文、英文及数字字符
_USERNAME_RE = re.compile(r"^[\u4e00-\u9fa5a-zA-Z0-9]+$")
# 验证码：6 位数字
_CODE_RE = re.compile(r"^\d{6}$")
# 控制字符（保留 \t 和 \n），用于输入净化
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# === 敏感字段（输出过滤） ===
_SENSITIVE_FIELDS = frozenset({
    "password_hash",
    "session_key",
    "wx_session_key",
    "verification_code",
    "secret",
    "token",
})

# JWT 签名算法（HS256，与 JWT_SECRET_KEY 配合使用）
_JWT_ALGORITHM = "HS256"


class Security:
    """安全验证类 - 所有后端安全验证逻辑的唯一入口"""

    # ===== 密码安全 =====

    @staticmethod
    def hash_password(password: str) -> str:
        """生成密码的 bcrypt 哈希值"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """校验明文密码与哈希值是否匹配"""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    @staticmethod
    def validate_password(password: str) -> str:
        """
        校验密码复杂度（8-20位，至少三种字符类型）
        注意：密码不做 strip()，空格可能是密码的一部分
        """
        if not isinstance(password, str):
            raise ValueError("密码必须为字符串")
        # 去除控制字符（但不 strip，空格可能是密码的一部分）
        password = _CONTROL_CHARS.sub("", password)
        if len(password) < 8 or len(password) > 20:
            raise ValueError("密码长度需为 8-20 位")
        categories = 0
        if re.search(r"[a-z]", password):
            categories += 1
        if re.search(r"[A-Z]", password):
            categories += 1
        if re.search(r"[0-9]", password):
            categories += 1
        if re.search(r"[^a-zA-Z0-9]", password):
            categories += 1
        if categories < 3:
            raise ValueError("密码需包含大小写字母、数字、特殊符号中的至少三种")
        return password

    # ===== 用户名安全 =====

    @staticmethod
    def validate_username(username: str) -> str:
        """校验用户名格式（2-15位，仅中文、英文、数字）"""
        if not isinstance(username, str):
            raise ValueError("用户名必须为字符串")
        username = Security.sanitize_string(username, max_length=15, field_name="用户名")
        if len(username) < 2:
            raise ValueError("用户名长度需为 2-15 个字符")
        if not _USERNAME_RE.match(username):
            raise ValueError("用户名仅允许中文、英文及数字字符")
        return username

    # ===== 验证码安全 =====

    @staticmethod
    def validate_code(code: str) -> str:
        """校验验证码格式（6位数字）"""
        if not isinstance(code, str):
            raise ValueError("验证码必须为字符串")
        code = code.strip()
        if not _CODE_RE.match(code):
            raise ValueError("验证码为 6 位数字")
        return code

    # ===== 邮箱安全 =====

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

    # ===== JWT 认证 =====

    @staticmethod
    def generate_token(user_id: int, role: int = 0) -> str:
        """
        生成 JWT 访问令牌
        :param user_id: 用户ID（写入 sub 声明）
        :param role: 用户角色（写入 role 声明，0-普通用户，7-管理员）
        :return: 签名后的 JWT 字符串
        :raises ValueError: JWT_SECRET_KEY 未配置或 user_id 非正整数
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("用户ID必须为正整数")
        secret = settings.JWT_SECRET_KEY
        if not secret:
            raise ValueError("JWT_SECRET_KEY 未配置，请在 .env 中设置")
        now = int(time.time())
        payload = {
            "sub": str(user_id),  # subject：用户ID（字符串形式，JWT 标准）
            "role": role,         # 角色：0-普通用户，7-管理员
            "iat": now,           # issued at：签发时间
            "exp": now + settings.JWT_EXPIRE_DAYS * 86400,  # expiration：过期时间
        }
        return jwt.encode(payload, secret, algorithm=_JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> dict[str, Any]:
        """
        校验 JWT 访问令牌
        :param token: JWT 字符串
        :return: 解码后的 payload（含 sub/iat/exp）
        :raises ValueError: token 无效、已过期或签名错误
        """
        if not isinstance(token, str) or not token.strip():
            raise ValueError("令牌不能为空")
        secret = settings.JWT_SECRET_KEY
        if not secret:
            raise ValueError("JWT_SECRET_KEY 未配置，请在 .env 中设置")
        try:
            payload = jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise ValueError("登录已过期，请重新登录")
        except jwt.InvalidTokenError:
            raise ValueError("登录凭证无效")
        if "sub" not in payload:
            raise ValueError("登录凭证格式不正确")
        return payload

    # ===== 通用输出实体化 =====

    @staticmethod
    def filter_output(data: dict) -> dict:
        """
        输出数据实体化（过滤）：
        移除敏感字段（password_hash、session_key 等），防止敏感信息泄露
        """
        if not isinstance(data, dict):
            return data
        return {k: v for k, v in data.items() if k not in _SENSITIVE_FIELDS}
