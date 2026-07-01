from pydantic import BaseModel, field_validator


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
        if not v or not v.strip():
            raise ValueError("SMTP服务器地址不能为空")
        return v.strip()

    @field_validator("smtp_port")
    @classmethod
    def validate_smtp_port(cls, v: int) -> int:
        if v <= 0 or v > 65535:
            raise ValueError("SMTP服务器端口范围 1-65535")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or "@" not in v:
            raise ValueError("发件邮箱地址格式不正确")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("客户端专用密码不能为空")
        return v


class CreateEmailChannel(BaseModel):
    """创建邮件通知渠道请求 Schema"""

    user_id: int
    smtp_host: str
    smtp_port: int
    email: str
    password: str
    enabled: bool = True  # 是否启用，默认启用

    @field_validator("smtp_host")
    @classmethod
    def validate_smtp_host(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("SMTP服务器地址不能为空")
        return v.strip()

    @field_validator("smtp_port")
    @classmethod
    def validate_smtp_port(cls, v: int) -> int:
        if v <= 0 or v > 65535:
            raise ValueError("SMTP服务器端口范围 1-65535")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or "@" not in v:
            raise ValueError("发件邮箱地址格式不正确")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("客户端专用密码不能为空")
        return v


class UpdateEmailChannel(BaseModel):
    """更新邮件通知渠道请求 Schema"""

    channel_id: int
    user_id: int
    smtp_host: str
    smtp_port: int
    email: str
    password: str = ""  # 空字符串表示保留原密码（前端修改时不展示密码）
    enabled: bool = True  # 是否启用

    @field_validator("smtp_host")
    @classmethod
    def validate_smtp_host(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("SMTP服务器地址不能为空")
        return v.strip()

    @field_validator("smtp_port")
    @classmethod
    def validate_smtp_port(cls, v: int) -> int:
        if v <= 0 or v > 65535:
            raise ValueError("SMTP服务器端口范围 1-65535")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or "@" not in v:
            raise ValueError("发件邮箱地址格式不正确")
        return v.strip()


class DeleteChannel(BaseModel):
    """删除通知渠道请求 Schema（仅允许删除邮件渠道）"""

    channel_id: int
    user_id: int
