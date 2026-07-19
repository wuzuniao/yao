from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.deps import get_current_user_id
from ...core.security import Security
from ...schemas.user import (
    BindEmail,
    ChangeEmail,
    ChangePassword,
    LoginUser,
    RegisterUser,
    ResetPassword,
    ScheduleDeletion,
    SendChangeEmailNewCode,
    SendChangeEmailOldCode,
    SendCode,
    SendResetCode,
    SetPassword,
    UpdateAvatar,
    UpdateSignature,
    UpdateUsername,
    WeChatLogin,
)
from ...services.user_service import User

router = APIRouter()


def _user_payload(db_user) -> dict:
    """构造登录/注册等接口的响应数据（含 JWT access_token）"""
    try:
        token = Security.generate_token(db_user.id, role=db_user.role)
    except ValueError as e:
        # JWT 配置异常时返回 500，避免静默失败
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "id": db_user.id,
        "username": db_user.username or "",
        "signature": db_user.signature or "",
        "avatar_url": db_user.avatar_url or "",
        "email": db_user.email or "",
        "has_password": bool(db_user.password_hash),
        "status": db_user.status,
        "role": db_user.role,
        "access_token": token,
    }


@router.post("/register")
async def register(payload: RegisterUser, db: AsyncSession = Depends(get_db)):
    """
    用户注册接口
    - 校验由 Pydantic Schema（字段规则）+ User 业务类（验证码/唯一性）共同完成
    - 验证码后端二次校验通过后才允许入库
    - 注册成功后签发 JWT，前端可直接登录态
    """
    user_service = User(db)
    try:
        db_user = await user_service.register(
            username=payload.username,
            password=payload.password,
            email=payload.email,
            code=payload.code,
        )
    except ValueError as e:
        # 业务校验失败（验证码/唯一性等）
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # 邮件发送等运行时异常
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "code": 0,
        "msg": "注册成功",
        "data": _user_payload(db_user),
    }


@router.post("/send-code")
async def send_code(payload: SendCode, db: AsyncSession = Depends(get_db)):
    """
    发送注册验证码接口
    - 将用户填写的邮箱作为收件人，调用 Email 类发送验证邮件
    """
    user_service = User(db)
    try:
        await user_service.send_code(payload.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"code": 0, "msg": "验证码已发送", "data": None}


@router.post("/login")
async def login(payload: LoginUser, db: AsyncSession = Depends(get_db)):
    """
    用户登录接口
    - 支持用户名或邮箱 + 密码登录
    - 返回用户信息（id、username、signature、avatar_url）和 JWT access_token
    """
    user_service = User(db)
    try:
        db_user = await user_service.login(
            username=payload.username,
            password=payload.password,
        )
    except ValueError as e:
        # 业务校验失败（用户不存在/密码错误）
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "登录成功",
        "data": _user_payload(db_user),
    }


@router.post("/send-reset-code")
async def send_reset_code(payload: SendResetCode, db: AsyncSession = Depends(get_db)):
    """
    发送密码找回验证码接口
    - 仅允许已注册邮箱
    """
    user_service = User(db)
    try:
        await user_service.send_reset_code(payload.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"code": 0, "msg": "验证码已发送", "data": None}


@router.post("/reset-password")
async def reset_password(payload: ResetPassword, db: AsyncSession = Depends(get_db)):
    """
    重置密码接口
    - 验证验证码后更新密码
    - 重置成功后签发 JWT，用户无需再次登录
    """
    user_service = User(db)
    try:
        db_user = await user_service.reset_password(
            email=payload.email,
            code=payload.code,
            new_password=payload.new_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "code": 0,
        "msg": "密码重置成功",
        "data": _user_payload(db_user),
    }


@router.put("/update-signature")
async def update_signature(
    payload: UpdateSignature,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新用户签名接口（user_id 来自 JWT）"""
    user_service = User(db)
    try:
        db_user = await user_service.update_signature(
            user_id=user_id,
            signature=payload.signature,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "签名更新成功",
        "data": {
            "id": db_user.id,
            "username": db_user.username,
            "signature": db_user.signature or "",
        },
    }


@router.put("/change-password")
async def change_password(
    payload: ChangePassword,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """修改密码接口（user_id 来自 JWT，验证旧密码后更新新密码）"""
    user_service = User(db)
    try:
        db_user = await user_service.change_password(
            user_id=user_id,
            old_password=payload.old_password,
            new_password=payload.new_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "code": 0,
        "msg": "密码修改成功",
        "data": {
            "id": db_user.id,
            "username": db_user.username,
        },
    }


@router.post("/send-change-email-old-code")
async def send_change_email_old_code(
    payload: SendChangeEmailOldCode,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """发送修改邮箱的旧邮箱验证码接口（user_id 来自 JWT）"""
    user_service = User(db)
    try:
        await user_service.send_change_email_old_code(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"code": 0, "msg": "验证码已发送", "data": None}


@router.post("/send-change-email-new-code")
async def send_change_email_new_code(
    payload: SendChangeEmailNewCode,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """发送修改邮箱的新邮箱验证码接口（user_id 来自 JWT，用于记录操作上下文）"""
    user_service = User(db)
    try:
        await user_service.send_change_email_new_code(payload.new_email, payload.allow_existing)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"code": 0, "msg": "验证码已发送", "data": None}


@router.put("/change-email")
async def change_email(
    payload: ChangeEmail,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """修改邮箱接口（user_id 来自 JWT，验证旧邮箱验证码和新邮箱验证码后更新）"""
    user_service = User(db)
    try:
        db_user = await user_service.change_email(
            user_id=user_id,
            old_code=payload.old_code,
            new_email=payload.new_email,
            new_code=payload.new_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "code": 0,
        "msg": "邮箱修改成功",
        "data": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
        },
    }


@router.put("/update-avatar")
async def update_avatar(
    payload: UpdateAvatar,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新用户头像接口（user_id 来自 JWT）"""
    user_service = User(db)
    try:
        db_user = await user_service.update_avatar(
            user_id=user_id,
            avatar_url=payload.avatar_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "头像更新成功",
        "data": {
            "id": db_user.id,
            "username": db_user.username,
            "avatar_url": db_user.avatar_url or "",
        },
    }


@router.post("/schedule-deletion")
async def schedule_deletion(
    payload: ScheduleDeletion,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """计划删除账号接口（user_id 来自 JWT，将 status 置为 0，后台任务在24小时后自动清理）"""
    user_service = User(db)
    try:
        db_user = await user_service.schedule_deletion(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "账号将在24小时后自动删除，且无法恢复，请保留个人数据",
        "data": {
            "id": db_user.id,
            "status": db_user.status,
        },
    }


@router.post("/cancel-deletion")
async def cancel_deletion(
    payload: ScheduleDeletion,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """取消账号删除接口（user_id 来自 JWT）"""
    user_service = User(db)
    try:
        db_user = await user_service.cancel_deletion(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "账号删除已取消",
        "data": {
            "id": db_user.id,
            "status": db_user.status,
        },
    }


@router.put("/update-username")
async def update_username(
    payload: UpdateUsername,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新用户名接口（user_id 来自 JWT，含用户名唯一性校验）"""
    user_service = User(db)
    try:
        db_user = await user_service.update_username(
            user_id=user_id,
            new_username=payload.new_username,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "用户名修改成功",
        "data": {
            "id": db_user.id,
            "username": db_user.username or "",
        },
    }


@router.put("/set-password")
async def set_password(
    payload: SetPassword,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """设置密码接口（user_id 来自 JWT，用于无密码用户首次设置密码）"""
    user_service = User(db)
    try:
        db_user = await user_service.set_password(
            user_id=user_id,
            new_password=payload.new_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "密码设置成功",
        "data": {
            "id": db_user.id,
            "username": db_user.username or "",
        },
    }


@router.put("/bind-email")
async def bind_email(
    payload: BindEmail,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """绑定邮箱接口（user_id 来自 JWT，用于无邮箱用户首次绑定邮箱）"""
    user_service = User(db)
    try:
        db_user = await user_service.bind_email(
            user_id=user_id,
            new_email=payload.new_email,
            new_code=payload.new_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "邮箱绑定成功",
        "data": {
            "id": db_user.id,
            "username": db_user.username or "",
            "signature": db_user.signature or "",
            "avatar_url": db_user.avatar_url or "",
            "email": db_user.email or "",
            "has_password": bool(db_user.password_hash),
            "status": db_user.status,
        },
    }


@router.get("/info")
async def get_user_info(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前登录用户信息接口（user_id 来自 JWT）
    - 用于前端验证账号是否存在（如账号删除后状态同步）
    - 若账号已被删除，get_current_user_id 仍可通过 token 解析出 user_id，
      此处查询数据库返回 404，前端据此清除本地状态
    """
    user_service = User(db)
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "id": user.id,
            "username": user.username or "",
            "signature": user.signature or "",
            "avatar_url": user.avatar_url or "",
            "email": user.email or "",
            "has_password": bool(user.password_hash),
            "status": user.status,
            "role": user.role,
        },
    }


@router.post("/wechat-login")
async def wechat_login(payload: WeChatLogin, db: AsyncSession = Depends(get_db)):
    """
    微信一键登录接口
    - 接收前端 wx.login() 获取的 code
    - 调用微信 jscode2session 接口换取 openid 和 session_key
    - 查找或创建用户，session_key 安全存储于后端（不下发到前端）
    - 返回用户信息（id、username、signature、avatar_url）和 JWT access_token
    """
    user_service = User(db)
    try:
        db_user = await user_service.wechat_login(payload.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"微信登录服务异常：{e}")
    return {
        "code": 0,
        "msg": "登录成功",
        "data": _user_payload(db_user),
    }
