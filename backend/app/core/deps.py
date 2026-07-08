"""
FastAPI 依赖：JWT 认证依赖
--------------------------------------------------------------------------
提供 `get_current_user_id` 依赖函数，受保护接口通过 `Depends(get_current_user_id)`
获取当前登录用户ID，无需从请求体或 URL 路径传 user_id。

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

from fastapi import Header, HTTPException

from .security import Security


async def get_current_user_id(authorization: str | None = Header(default=None)) -> int:
    """
    从请求头 Authorization 解析 JWT，返回当前登录用户ID
    :param authorization: 请求头 Authorization 字段，格式 "Bearer <token>"
    :return: 当前用户ID
    :raises HTTPException: 401 未携带 token / token 无效 / token 已过期
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
    return user_id
