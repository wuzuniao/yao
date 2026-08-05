import re

from pydantic import BaseModel, EmailStr, field_validator

from ..core.security import Security


# device_id UUID v4 格式校验正则（前端 getDeviceId 生成标准 UUID v4）
# 校验目的：拒绝任意短串/非 UUID，降低伪造与脏数据风险
_DEVICE_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _validate_device_id(v: str | None) -> str | None:
    """device_id 校验：None 跳过（非必填），非空必须为合法 UUID v4 格式"""
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    if not _DEVICE_ID_RE.match(v):
        raise ValueError("设备标识格式不合法")
    return v


class RegisterUser(BaseModel):
    """注册请求 Schema（后端输入校验）"""

    username: str
    password: str
    email: EmailStr
    code: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return Security.validate_username(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return Security.validate_password(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return Security.validate_code(v)


class SendCode(BaseModel):
    """发送验证码请求 Schema"""

    email: EmailStr


class LoginUser(BaseModel):
    """登录请求 Schema"""

    username: str  # 用户名或邮箱（前端统一用 username 字段传递）

    password: str

    # 设备标识（前端首次登录生成的 UUID），传入后下发生物识别登录凭证，用于 App 端指纹一键登录
    device_id: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("请输入用户名或邮箱")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("请输入密码")
        return v

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str | None) -> str | None:
        return _validate_device_id(v)


class SendResetCode(BaseModel):
    """发送密码找回验证码请求 Schema"""

    email: EmailStr


class ResetPassword(BaseModel):
    """重置密码请求 Schema"""

    email: EmailStr
    code: str
    new_password: str
    # 设备标识（前端首次登录生成的 UUID），传入后下发生物识别登录凭证，用于 App 端指纹一键登录
    device_id: str | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return Security.validate_code(v)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return Security.validate_password(v)

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str | None) -> str | None:
        return _validate_device_id(v)


class UpdateSignature(BaseModel):
    """更新签名请求 Schema（user_id 由 JWT 提供，不入请求体）"""

    signature: str

    @field_validator("signature")
    @classmethod
    def validate_signature(cls, v: str) -> str:
        return Security.sanitize_string(v, max_length=70, field_name="签名")


class ChangePassword(BaseModel):
    """修改密码请求 Schema（user_id 由 JWT 提供，不入请求体）"""

    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return Security.validate_password(v)


class SendChangeEmailOldCode(BaseModel):
    """发送修改邮箱旧邮箱验证码请求 Schema（user_id 由 JWT 提供）"""

    pass


class SendChangeEmailNewCode(BaseModel):
    """发送修改/绑定邮箱新邮箱验证码请求 Schema"""

    new_email: EmailStr
    # 是否允许邮箱已存在（绑定邮箱触发账号合并场景需允许，修改邮箱场景禁止）
    allow_existing: bool = False


class ChangeEmail(BaseModel):
    """修改邮箱请求 Schema（user_id 由 JWT 提供，不入请求体）"""

    old_code: str
    new_email: EmailStr
    new_code: str

    @field_validator("old_code")
    @classmethod
    def validate_old_code(cls, v: str) -> str:
        return Security.validate_code(v)

    @field_validator("new_code")
    @classmethod
    def validate_new_code(cls, v: str) -> str:
        return Security.validate_code(v)


class UpdateAvatar(BaseModel):
    """更新头像请求 Schema（user_id 由 JWT 提供，不入请求体）"""

    avatar_url: str

    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: str) -> str:
        return Security.validate_avatar_url(v)


class ScheduleDeletion(BaseModel):
    """计划删除账号请求 Schema（user_id 由 JWT 提供）"""

    pass


class WeChatLogin(BaseModel):
    """微信登录请求 Schema"""

    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("微信登录凭证 code 不能为空")
        return v.strip()


class BindWeChat(BaseModel):
    """绑定微信请求 Schema（绑定到当前登录用户，user_id 由 JWT 提供）"""

    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("微信登录凭证 code 不能为空")
        return v.strip()


class UpdateUsername(BaseModel):
    """更新用户名请求 Schema（user_id 由 JWT 提供，不入请求体）"""

    new_username: str

    @field_validator("new_username")
    @classmethod
    def validate_new_username(cls, v: str) -> str:
        return Security.validate_username(v)


class SetPassword(BaseModel):
    """设置密码请求 Schema（用于无密码用户首次设置密码，user_id 由 JWT 提供）"""

    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return Security.validate_password(v)


class BindEmail(BaseModel):
    """绑定邮箱请求 Schema（用于无邮箱用户首次绑定邮箱，user_id 由 JWT 提供）"""

    new_email: EmailStr
    new_code: str

    @field_validator("new_code")
    @classmethod
    def validate_new_code(cls, v: str) -> str:
        return Security.validate_code(v)


class BiometricLogin(BaseModel):
    """生物识别（指纹）登录请求 Schema"""

    token: str  # 前端本地解密出的生物识别登录凭证
    device_id: str  # 设备标识（与凭证绑定）

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("生物识别凭证不能为空")
        return v.strip()

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        v = v.strip() if v else ""
        if not v:
            raise ValueError("设备标识不能为空")
        if not _DEVICE_ID_RE.match(v):
            raise ValueError("设备标识格式不合法")
        return v


class BiometricRevoke(BaseModel):
    """撤销生物识别（指纹）登录凭证请求 Schema（单设备撤销）"""

    device_id: str  # 设备标识（与凭证绑定）

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        v = v.strip() if v else ""
        if not v:
            raise ValueError("设备标识不能为空")
        if not _DEVICE_ID_RE.match(v):
            raise ValueError("设备标识格式不合法")
        return v


class RefreshTokenReq(BaseModel):
    """刷新令牌有效期请求 Schema（device_id 可选，用于同步续期生物识别凭证）"""

    device_id: str | None = None

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str | None) -> str | None:
        return _validate_device_id(v)
