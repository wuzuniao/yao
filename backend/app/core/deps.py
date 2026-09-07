"""
FastAPI 依赖：认证依赖
--------------------------------------------------------------------------
提供 `get_current_user_id` 与 `get_current_admin` 依赖函数，受保护接口通过
`Depends(get_current_user_id)` 获取当前登录用户ID。

拆分说明（用户模块独立为 auth 服务后）：
- access_token 由 auth 服务以 RS256 签发，本服务持公钥本地验签（零逐请求网络调用）；
- 用户库已不可达，本依赖不再查库——用户状态与令牌撤销经 auth 的撤销增量同步
  （后台每 REVOCATION_SYNC_INTERVAL_SECONDS 秒拉取一次）本地比对 iat 实现，
  撤销生效窗口 ≈ 同步间隔（默认 5 分钟）；
- role 取自令牌 claims（auth 签发时写入）。

安全校验：
1. RS256 签名 + issuer + 过期校验（Security.verify_access_token，本地公钥验签）
2. 令牌撤销本地比对（auth_client.is_revoked：iat < 该用户最新撤销时刻 → 401）
3. 管理员角色校验（claims.role == 7）

用法：
    from fastapi import Depends
    from .core.deps import get_current_user_id

    @router.put("/change-password")
    async def change_password(
        payload: SomeSchema,
        user_id: int = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ):
        ...
"""
from __future__ import annotations

from fastapi import Header, HTTPException

from . import auth_client
from .security import Security


async def _authenticate_and_validate(
    authorization: str | None, require_admin: bool
) -> int:
    """
    解析 access_token 并完成本地校验
    :param authorization: 请求头 Authorization 字段
    :param require_admin: 是否要求管理员角色
    :return: 当前用户ID
    :raises HTTPException: 401 未登录/无效/过期/已撤销；403 非管理员
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录，请先登录")
    # 校验 Bearer 前缀（RFC 6750）
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="认证凭证格式不正确")
    token = parts[1].strip()
    try:
        payload = await Security.verify_access_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="登录凭证格式不正确")
    if user_id <= 0:
        raise HTTPException(status_code=401, detail="登录凭证无效")

    # 令牌撤销本地比对（数据源为后台增量同步，每请求零网络调用）
    if auth_client.is_revoked(user_id, payload.get("iat", 0)):
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")

    # 管理员角色（auth 签发时写入 role 声明：0-普通用户，7-管理员）
    if require_admin and payload.get("role") != 7:
        raise HTTPException(status_code=403, detail="无管理员权限")

    return user_id


async def get_current_user_id(
    authorization: str | None = Header(default=None),
) -> int:
    """
    从请求头 Authorization 解析 access_token，本地验签后返回当前登录用户ID
    :param authorization: 请求头 Authorization 字段，格式 "Bearer <access_token>"
    :return: 当前用户ID
    :raises HTTPException: 401 未携带 token / token 无效 / token 已过期 / token 已撤销
    """
    return await _authenticate_and_validate(authorization, require_admin=False)


async def get_current_admin(
    authorization: str | None = Header(default=None),
) -> int:
    """
    从请求头 Authorization 解析 access_token，校验管理员角色（claims.role==7）
    :param authorization: 请求头 Authorization 字段，格式 "Bearer <access_token>"
    :return: 当前管理员用户ID
    :raises HTTPException: 401 未携带/无效/过期/已撤销 token；403 非管理员
    """
    return await _authenticate_and_validate(authorization, require_admin=True)
