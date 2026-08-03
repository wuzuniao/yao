from typing import Literal

from pydantic import BaseModel, Field, field_validator

from ..core.security import Security


# 允许的通知类型（站内信不允许用户主动创建/修改，邮件/微信/App推送可由用户配置）
CHANNEL_TYPE_ZNX = "站内信"
CHANNEL_TYPE_EMAIL = "邮件"
CHANNEL_TYPE_WECHAT = "微信"
# App 推送（友盟+ U-Push），仅 App 端（#ifdef APP-PLUS）可添加，小程序端不展示
CHANNEL_TYPE_APP_PUSH = "App推送"

# App 推送设备 token 累计失败上限：连续失败达到该次数即从数组中剔除该 token
APP_PUSH_MAX_FAIL_COUNT = 3


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


class UpdateWechatChannel(BaseModel):
    """更新微信通知渠道启用状态请求 Schema（user_id 由 JWT 提供，不入请求体）"""

    channel_id: int
    enabled: bool

    @field_validator("channel_id")
    @classmethod
    def validate_channel_id(cls, v: int) -> int:
        return Security.validate_positive_int(v, "渠道ID")


class AppPushDeviceToken(BaseModel):
    """App 推送渠道 channel_value 中单个设备 token 的结构"""

    token: str
    platform: Literal["android", "ios"]
    fail_count: int = 0

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("设备 token 不能为空")
        if len(v) > 128:
            raise ValueError("设备 token 长度非法")
        return v

    @field_validator("fail_count")
    @classmethod
    def validate_fail_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("失败次数不能为负数")
        return v


class AppPushChannelValue(BaseModel):
    """App 推送通知渠道的 channel_value JSON 结构（每用户单行，值内存设备 token 数组）"""

    device_tokens: list[AppPushDeviceToken] = Field(default_factory=list)


class UpsertAppPushChannel(BaseModel):
    """上报 App 设备 token 请求 Schema（user_id 由 JWT 提供，不入请求体）

    - 由通知方式页添加、App 端打卡完成时调用
    - create_if_missing=False 时（打卡上报）仅刷新已有渠道，不自动建行
    """

    device_token: str
    platform: Literal["android", "ios"]
    create_if_missing: bool = False

    @field_validator("device_token")
    @classmethod
    def validate_device_token(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("设备 token 不能为空")
        if len(v) > 128:
            raise ValueError("设备 token 长度非法")
        return v


class DeleteChannel(BaseModel):
    """删除通知渠道请求 Schema（user_id 由 JWT 提供，不入请求体；仅允许删除邮件渠道）"""

    channel_id: int

    @field_validator("channel_id")
    @classmethod
    def validate_channel_id(cls, v: int) -> int:
        return Security.validate_positive_int(v, "渠道ID")


class UpdateAppPushChannel(BaseModel):
    """更新 App 推送通知渠道启用状态请求 Schema（user_id 由 JWT 提供，不改动设备 token）"""

    channel_id: int
    enabled: bool

    @field_validator("channel_id")
    @classmethod
    def validate_channel_id(cls, v: int) -> int:
        return Security.validate_positive_int(v, "渠道ID")
