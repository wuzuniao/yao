import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


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


# 用户名：仅允许中文、英文及数字字符
_USERNAME_RE = re.compile(r"^[\u4e00-\u9fa5a-zA-Z0-9]+$")
# 验证码：6 位数字
_CODE_RE = re.compile(r"^\d{6}$")


class RegisterUser(BaseModel):
    """注册请求 Schema（后端输入校验）"""

    username: str
    password: str
    email: EmailStr
    code: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v:
            raise ValueError("用户名不能为空")
        if len(v) < 2 or len(v) > 15:
            raise ValueError("用户名长度需为 2-15 个字符")
        if not _USERNAME_RE.match(v):
            raise ValueError("用户名仅允许中文、英文及数字字符")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 20:
            raise ValueError("密码长度需为 8-20 位")
        categories = 0
        if re.search(r"[a-z]", v):
            categories += 1
        if re.search(r"[A-Z]", v):
            categories += 1
        if re.search(r"[0-9]", v):
            categories += 1
        if re.search(r"[^a-zA-Z0-9]", v):
            categories += 1
        if categories < 3:
            raise ValueError("密码需包含大小写字母、数字、特殊符号中的至少三种")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not _CODE_RE.match(v):
            raise ValueError("验证码为 6 位数字")
        return v


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
        if not v:
            raise ValueError("请输入用户名或邮箱")
        return v

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
        if not _CODE_RE.match(v):
            raise ValueError("验证码为 6 位数字")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 20:
            raise ValueError("密码长度需为 8-20 位")
        categories = 0
        if re.search(r"[a-z]", v):
            categories += 1
        if re.search(r"[A-Z]", v):
            categories += 1
        if re.search(r"[0-9]", v):
            categories += 1
        if re.search(r"[^a-zA-Z0-9]", v):
            categories += 1
        if categories < 3:
            raise ValueError("密码需包含大小写字母、数字、特殊符号中的至少三种")
        return v


class UpdateSignature(BaseModel):
    """更新签名请求 Schema"""

    user_id: int
    signature: str

    @field_validator("signature")
    @classmethod
    def validate_signature(cls, v: str) -> str:
        if len(v) > 70:
            raise ValueError("签名长度不能超过 70 个字符")
        return v


class ChangePassword(BaseModel):
    """修改密码请求 Schema"""

    user_id: int
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 20:
            raise ValueError("密码长度需为 8-20 位")
        categories = 0
        if re.search(r"[a-z]", v):
            categories += 1
        if re.search(r"[A-Z]", v):
            categories += 1
        if re.search(r"[0-9]", v):
            categories += 1
        if re.search(r"[^a-zA-Z0-9]", v):
            categories += 1
        if categories < 3:
            raise ValueError("密码需包含大小写字母、数字、特殊符号中的至少三种")
        return v


class SendChangeEmailOldCode(BaseModel):
    """发送修改邮箱旧邮箱验证码请求 Schema"""

    user_id: int


class SendChangeEmailNewCode(BaseModel):
    """发送修改/绑定邮箱新邮箱验证码请求 Schema"""

    new_email: EmailStr
    # 是否允许邮箱已存在（绑定邮箱触发账号合并场景需允许，修改邮箱场景禁止）
    allow_existing: bool = False


class ChangeEmail(BaseModel):
    """修改邮箱请求 Schema"""

    user_id: int
    old_code: str
    new_email: EmailStr
    new_code: str

    @field_validator("old_code")
    @classmethod
    def validate_old_code(cls, v: str) -> str:
        if not _CODE_RE.match(v):
            raise ValueError("旧邮箱验证码为 6 位数字")
        return v

    @field_validator("new_code")
    @classmethod
    def validate_new_code(cls, v: str) -> str:
        if not _CODE_RE.match(v):
            raise ValueError("新邮箱验证码为 6 位数字")
        return v


class UpdateAvatar(BaseModel):
    """更新头像请求 Schema"""

    user_id: int
    avatar_url: str

    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: str) -> str:
        if not v:
            raise ValueError("头像地址不能为空")
        if len(v) > 500:
            raise ValueError("头像地址长度不能超过 500 个字符")
        return v


class ScheduleDeletion(BaseModel):
    """计划删除账号请求 Schema"""

    user_id: int


class WeChatLogin(BaseModel):
    """微信登录请求 Schema"""

    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v:
            raise ValueError("微信登录凭证 code 不能为空")
        return v


class UpdateUsername(BaseModel):
    """更新用户名请求 Schema"""

    user_id: int
    new_username: str

    @field_validator("new_username")
    @classmethod
    def validate_new_username(cls, v: str) -> str:
        if not v:
            raise ValueError("用户名不能为空")
        if len(v) < 2 or len(v) > 15:
            raise ValueError("用户名长度需为 2-15 个字符")
        if not _USERNAME_RE.match(v):
            raise ValueError("用户名仅允许中文、英文及数字字符")
        return v


class SetPassword(BaseModel):
    """设置密码请求 Schema（用于无密码用户首次设置密码）"""

    user_id: int
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 20:
            raise ValueError("密码长度需为 8-20 位")
        categories = 0
        if re.search(r"[a-z]", v):
            categories += 1
        if re.search(r"[A-Z]", v):
            categories += 1
        if re.search(r"[0-9]", v):
            categories += 1
        if re.search(r"[^a-zA-Z0-9]", v):
            categories += 1
        if categories < 3:
            raise ValueError("密码需包含大小写字母、数字、特殊符号中的至少三种")
        return v


class BindEmail(BaseModel):
    """绑定邮箱请求 Schema（用于无邮箱用户首次绑定邮箱）"""

    user_id: int
    new_email: EmailStr
    new_code: str

    @field_validator("new_code")
    @classmethod
    def validate_new_code(cls, v: str) -> str:
        if not _CODE_RE.match(v):
            raise ValueError("邮箱验证码为 6 位数字")
        return v
