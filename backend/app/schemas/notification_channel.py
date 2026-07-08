from pydantic import BaseModel, field_validator

from ..core.security import Security


# 允许的通知类型（站内信不允许用户主动创建/修改，仅邮件可由用户配置）
CHANNEL_TYPE_ZNX = "站内信"
CHANNEL_TYPE_EMAIL = "邮件"


class EmailChannelValue(BaseModel):
    """邮件通知渠道的 channel_value JSON 结构"""

    smtp_host: str
    smtp_port: int
    email: str
    password: str  # 客户端专用密码

    @field_validator("smtp_host")
    @classmethod
    def validate_smtp_host(cls, v: str) -> str:
        return Security.validate_smtp_host(v)

    @field_validator("smtp_port")
    @classmethod
    def validate_smtp_port(cls, v: int) -> int:
        return Security.validate_smtp_port(v)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return Security.validate_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("客户端专用密码不能为空")
        return v


class CreateEmailChannel(BaseModel):
    """创建邮件通知渠道请求 Schema（user_id 由 JWT 提供，不入请求体）"""

    smtp_host: str
    smtp_port: int
    email: str
    password: str
    enabled: bool = True  # 是否启用，默认启用

    @field_validator("smtp_host")
    @classmethod
    def validate_smtp_host(cls, v: str) -> str:
        return Security.validate_smtp_host(v)

    @field_validator("smtp_port")
    @classmethod
    def validate_smtp_port(cls, v: int) -> int:
        return Security.validate_smtp_port(v)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return Security.validate_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("客户端专用密码不能为空")
        return v


class UpdateEmailChannel(BaseModel):
    """更新邮件通知渠道请求 Schema（user_id 由 JWT 提供，不入请求体）"""

    channel_id: int
    smtp_host: str
    smtp_port: int
    email: str
    password: str = ""  # 空字符串表示保留原密码（前端修改时不展示密码）
    enabled: bool = True  # 是否启用

    @field_validator("channel_id")
    @classmethod
    def validate_channel_id(cls, v: int) -> int:
        return Security.validate_positive_int(v, "渠道ID")

    @field_validator("smtp_host")
    @classmethod
    def validate_smtp_host(cls, v: str) -> str:
        return Security.validate_smtp_host(v)

    @field_validator("smtp_port")
    @classmethod
    def validate_smtp_port(cls, v: int) -> int:
        return Security.validate_smtp_port(v)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return Security.validate_email(v)


class DeleteChannel(BaseModel):
    """删除通知渠道请求 Schema（user_id 由 JWT 提供，不入请求体；仅允许删除邮件渠道）"""

    channel_id: int

    @field_validator("channel_id")
    @classmethod
    def validate_channel_id(cls, v: int) -> int:
        return Security.validate_positive_int(v, "渠道ID")
