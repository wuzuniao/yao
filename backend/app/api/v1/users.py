from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.deps import get_current_user_id
from ...core.rate_limit import (
    limit_login,
    limit_register,
    limit_reset_password,
    limit_send_code,
)
from ...core.security import Security
from ...models.user import User as UserModel
from ...models.user_miniapp_account import UserMiniappAccount
from ...schemas.user import (
    BindEmail,
    BindWeChat,
    BiometricLogin,
    BiometricRevoke,
    ChangeEmail,
    ChangePassword,
    LoginUser,
    RefreshTokenReq,
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
from ...utils.logger import logger

router = APIRouter()


async def _is_wechat_bound(db: AsyncSession, user_id: int) -> bool:
    """查询指定用户是否已绑定微信小程序账号（前端据此判断能否接收微信通知）"""
    if db is None or not user_id:
        return False
    result = await db.execute(
        select(UserMiniappAccount.id).where(
            UserMiniappAccount.user_id == user_id
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _user_payload(db: AsyncSession, db_user) -> dict:
    """构造登录/注册等接口的响应数据（含 JWT access_token 与微信绑定状态）"""
    try:
        token = Security.generate_token(db_user.id, role=db_user.role)
    except ValueError as e:
        # JWT 配置异常时返回 500，避免静默失败
        raise HTTPException(status_code=500, detail=str(e))
    is_wechat_bound = await _is_wechat_bound(db, db_user.id)
    return {
        "id": db_user.id,
        "username": db_user.username or "",
        "signature": db_user.signature or "",
        "avatar_url": db_user.avatar_url or "",
        "email": db_user.email or "",
        "has_password": bool(db_user.password_hash),
        "status": db_user.status,
        "role": db_user.role,
        "is_wechat_bound": is_wechat_bound,
        "access_token": token,
    }


@router.post("/register", dependencies=[Depends(limit_register)])
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
        "data": await _user_payload(db, db_user),
    }


@router.post("/send-code", dependencies=[Depends(limit_send_code)])
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


@router.post("/login", dependencies=[Depends(limit_login)])
async def login(payload: LoginUser, db: AsyncSession = Depends(get_db)):
    """
    用户登录接口
    - 支持用户名或邮箱 + 密码登录
    - 返回用户信息（id、username、signature、avatar_url）和 JWT access_token
    - 若携带 device_id，额外下发生物识别登录凭证（biometric_token），供 App 端指纹一键登录
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
    data = await _user_payload(db, db_user)
    # 仅在 App 端传入 device_id 时下发指纹凭证（后端加密存储，前端二次加密存本地）
    if payload.device_id:
        try:
            data["biometric_token"] = await user_service.issue_biometric_token(
                db_user.id, payload.device_id
            )
        except ValueError:
            # device_id 非法时不影响主登录流程
            pass
    return {
        "code": 0,
        "msg": "登录成功",
        "data": data,
    }


@router.post("/send-reset-code", dependencies=[Depends(limit_send_code)])
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


@router.post("/reset-password", dependencies=[Depends(limit_reset_password)])
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
    data = await _user_payload(db, db_user)
    # 重置密码等同重新认证，若携带 device_id 则下发生物识别登录凭证
    if payload.device_id:
        try:
            data["biometric_token"] = await user_service.issue_biometric_token(
                db_user.id, payload.device_id
            )
        except ValueError:
            pass
    return {
        "code": 0,
        "msg": "密码重置成功",
        "data": data,
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


@router.post("/send-change-email-old-code", dependencies=[Depends(limit_send_code)])
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


@router.post("/send-change-email-new-code", dependencies=[Depends(limit_send_code)])
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


@router.post("/logout")
async def logout(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    退出登录接口（user_id 来自 JWT）
    - 设置 token_invalid_before 使当前 token 立即失效
    - 前端需同步清除本地存储的 access_token
    """
    user_service = User(db)
    try:
        await user_service.logout(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"code": 0, "msg": "退出成功", "data": None}


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
    """
    绑定邮箱接口（user_id 来自 JWT，用于无邮箱用户首次绑定邮箱）
    - 若邮箱已存在会触发账号合并，合并后主账号 user_id 可能变化，因此返回新的 JWT access_token
    """
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
        "data": await _user_payload(db, db_user),
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
    is_wechat_bound = await _is_wechat_bound(db, user_id)
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
            "is_wechat_bound": is_wechat_bound,
        },
    }


@router.post("/wechat-login", dependencies=[Depends(limit_login)])
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
        # 详细异常记录到日志，前端仅返回通用提示（避免泄露内部信息）
        logger.exception(f"微信登录服务异常：{e}")
        raise HTTPException(status_code=500, detail="微信登录服务异常，请稍后重试")
    return {
        "code": 0,
        "msg": "登录成功",
        "data": await _user_payload(db, db_user),
    }


@router.post("/bind-wechat")
async def bind_wechat(
    payload: BindWeChat,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    绑定微信到当前用户接口
    - 供已注册但未微信登录的用户，在通知页主动绑定微信以接收订阅消息
    - 接收前端 wx.login() 获取的 code，换取 openid 后关联到当前登录用户
    - 若该 openid 已被其他账号绑定，则返回错误
    - 成功后写入 user_miniapp_accounts，使微信通知可正常下发
    """
    user_service = User(db)
    try:
        db_user = await user_service.bind_wechat(user_id, payload.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 详细异常记录到日志，前端仅返回通用提示（避免泄露内部信息）
        logger.exception(f"微信绑定失败：{e}")
        raise HTTPException(status_code=500, detail="微信绑定服务异常，请稍后重试")
    return {
        "code": 0,
        "msg": "微信绑定成功",
        "data": await _user_payload(db, db_user),
    }


@router.post("/refresh-token")
async def refresh_token(
    payload: RefreshTokenReq,
    authorization: str = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    刷新访问令牌有效期（静默续期，不要求重新登录）
    - 复用 get_current_user_id 的校验逻辑（签名/过期/用户状态/token_invalid_before）
    - 通过校验后用同一 user_id 重新签发一个有效期为 JWT_EXPIRE_DAYS 的新 token
    - 若携带 device_id，同步顺延该设备的生物识别登录凭证有效期
    - 不引入 refresh_token 概念，保持与现有 JWT 体系一致
    """
    user_id = await get_current_user_id(authorization=authorization, db=db)
    # 重新查用户对象以拿到 role（与 _user_payload 一致）
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=401, detail="用户不存在，请重新登录")
    try:
        new_token = Security.generate_token(db_user.id, role=db_user.role)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    # 同步续期生物识别登录凭证（已登录续期时一并更新有效期）
    if payload.device_id:
        await User(db).refresh_biometric_token(user_id, payload.device_id)
    return {
        "code": 0,
        "msg": "令牌已刷新",
        "data": {"access_token": new_token},
    }


@router.post("/biometric-login", dependencies=[Depends(limit_login)])
async def biometric_login(payload: BiometricLogin, db: AsyncSession = Depends(get_db)):
    """
    生物识别（指纹）登录接口
    - 前端凭本地加密存储的生物识别凭证 + 设备标识调用
    - 后端校验 token 有效（未过期）+ device_id 匹配后签发 JWT
    - SOTER 指纹验证由 App 端系统层完成（未通过验证前端拿不到签名），后端聚焦凭证与设备绑定校验
    - 返回的 JWT 与原登录流程一致，前端进入首页
    """
    user_service = User(db)
    db_user = await user_service.verify_biometric_token(payload.token, payload.device_id)
    if not db_user:
        raise HTTPException(status_code=401, detail="指纹登录凭证无效或已失效，请使用账号密码登录")
    if db_user.status not in (0, 1):
        raise HTTPException(status_code=401, detail="账号已停用，请联系管理员")
    return {
        "code": 0,
        "msg": "登录成功",
        "data": await _user_payload(db, db_user),
    }


@router.post("/biometric-revoke")
async def biometric_revoke(
    payload: BiometricRevoke,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    撤销当前用户当前设备的生物识别登录凭证（单设备撤销）
    - 用户在个人信息页关闭指纹登录时调用，立即作废服务端凭证
    - 关闭后本设备无法再使用指纹一键登录，需重新账号密码登录下发新凭证
    """
    await User(db).revoke_biometric_token(user_id, payload.device_id)
    return {"code": 0, "msg": "已关闭指纹登录"}
