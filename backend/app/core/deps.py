"""
FastAPI 依赖：JWT 认证依赖
--------------------------------------------------------------------------
提供 `get_current_user_id` 与 `get_current_admin` 依赖函数，受保护接口通过
`Depends(get_current_user_id)` 获取当前登录用户ID。

安全校验：
1. JWT 签名与过期校验（Security.verify_token）
2. 用户存在性校验（数据库查询，防止账号被删除后 token 仍可用）
3. 用户状态校验（status=1 正常，0 待删除的账号禁止操作）
4. token 失效校验（token_invalid_before：改密码/重置密码/退出登录后，旧 token 立即失效）

用法：
    from fastapi import Depends
    from .core.deps import get_current_user_id

    @router.put("/change-password")
    async def change_password(
        payload: ChangePassword,
        user_id: int = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ):
        ...
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User as UserModel
from .database import get_db
from .security import Security


async def _authenticate_and_validate(
    authorization: str | None, db: AsyncSession, require_admin: bool
) -> int:
    """
    解析 JWT 并校验用户状态与 token 失效时间
    :param authorization: 请求头 Authorization 字段
    :param db: 数据库会话
    :param require_admin: 是否要求管理员角色
    :return: 当前用户ID
    :raises HTTPException: 401 未登录/无效/过期/失效；403 非管理员
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录，请先登录")
    # 校验 Bearer 前缀（RFC 6750）
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="认证凭证格式不正确")
    token = parts[1].strip()
    try:
        payload = Security.verify_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="登录凭证格式不正确")
    if user_id <= 0:
        raise HTTPException(status_code=401, detail="登录凭证无效")

    # 查库校验用户存在性、状态、token 失效时间
    # 仅查询必要字段，避免加载完整 ORM 对象
    result = await db.execute(
        select(UserModel.id, UserModel.status, UserModel.role, UserModel.token_invalid_before).where(
            UserModel.id == user_id
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=401, detail="用户不存在，请重新登录")
    if row.status != 1:
        raise HTTPException(status_code=401, detail="账号已停用，请联系管理员")

    # 校验 token 是否在 token_invalid_before 之前签发
    # iat 是 token 签发时间的 Unix 时间戳，token_invalid_before 是数据库的 DATETIME
    if row.token_invalid_before is not None:
        iat = payload.get("iat", 0)
        # 数据库存储的是上海时区 naive datetime，需显式附加时区后转换为 Unix 时间戳
        invalid_before_ts = _datetime_to_timestamp(row.token_invalid_before)
        if iat < invalid_before_ts:
            raise HTTPException(status_code=401, detail="登录已失效，请重新登录")

    if require_admin and row.role != 7:
        raise HTTPException(status_code=403, detail="无管理员权限")

    return user_id


def _datetime_to_timestamp(dt) -> float:
    """
    将数据库返回的 naive datetime（视为上海时区）转换为 Unix 时间戳
    - 数据库连接已通过 init_command 设置 time_zone='+08:00'，返回的 naive datetime 为上海时区
    - 显式附加上海时区后转换为 Unix 时间戳，避免依赖系统本地时区
    """
    from ..utils.timezone import SHANGHAI_TZ
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=SHANGHAI_TZ)
    return dt.timestamp()


async def get_current_user_id(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> int:
    """
    从请求头 Authorization 解析 JWT，校验用户状态后返回当前登录用户ID
    :param authorization: 请求头 Authorization 字段，格式 "Bearer <token>"
    :param db: 数据库会话（用于校验用户存在性、状态、token 失效时间）
    :return: 当前用户ID
    :raises HTTPException: 401 未携带 token / token 无效 / token 已过期 / 用户已停用 / token 已失效
    """
    return await _authenticate_and_validate(authorization, db, require_admin=False)


async def get_current_admin(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> int:
    """
    从请求头 Authorization 解析 JWT，校验管理员角色（role=7）
    :param authorization: 请求头 Authorization 字段，格式 "Bearer <token>"
    :param db: 数据库会话
    :return: 当前管理员用户ID
    :raises HTTPException: 401 未携带/无效/过期 token；403 非管理员
    """
    return await _authenticate_and_validate(authorization, db, require_admin=True)
