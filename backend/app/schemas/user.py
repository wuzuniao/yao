from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from ..core.security import Security


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


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


class SendResetCode(BaseModel):
    """发送密码找回验证码请求 Schema"""

    email: EmailStr


class ResetPassword(BaseModel):
    """重置密码请求 Schema"""

    email: EmailStr
    code: str
    new_password: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return Security.validate_code(v)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return Security.validate_password(v)


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
        v = Security.sanitize_string(v, max_length=500, field_name="头像地址")
        if not v:
            raise ValueError("头像地址不能为空")
        return v


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
