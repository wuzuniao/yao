"""
进程内字典限流器（滑动窗口算法）
--------------------------------------------------------------------------
- 适用于单进程部署，多进程部署需迁移至 Redis
- 按 客户端 IP + 接口路径 维度计数，窗口内超过阈值返回 429
- 仅对未鉴权接口生效（登录/注册/发送验证码等匿名接口）
- 已鉴权接口的滥用由 JWT 用户身份约束，可按需扩展为 IP+user_id 维度

用法：
    from .rate_limit import limit_login, limit_send_code

    @router.post("/login", dependencies=[Depends(limit_login)])
    async def login(...): ...
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, Awaitable

from fastapi import HTTPException, Request

# 进程内存储：key -> [timestamp, ...]
# 说明：未做持久化与过期清理，依赖惰性清理（每次访问时移除窗口外记录）
_rate_store: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    """获取客户端真实 IP（优先取 X-Forwarded-For 首段，回退到连接对端地址）"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _make_limiter(
    max_count: int, window_seconds: int
) -> Callable[[Request], Awaitable[None]]:
    """
    生成限流依赖函数
    :param max_count: 窗口内允许的最大请求数
    :param window_seconds: 窗口大小（秒）
    :return: FastAPI 依赖函数，超限抛 429
    """

    async def _dep(request: Request) -> None:
        ip = _client_ip(request)
        key = f"{ip}:{request.url.path}"
        now = time.time()
        # 惰性清理：仅保留窗口内的记录
        history = [t for t in _rate_store[key] if t > now - window_seconds]
        if len(history) >= max_count:
            raise HTTPException(
                status_code=429,
                detail=f"请求过于频繁，请 {window_seconds} 秒后重试",
            )
        history.append(now)
        _rate_store[key] = history

    return _dep


# 预定义常用限流策略（按接口语义命名，便于在路由处直接引用）
# 登录/微信登录：5 次/分钟（防止密码爆破）
limit_login = _make_limiter(max_count=5, window_seconds=60)
# 注册：3 次/分钟（防止垃圾注册）
limit_register = _make_limiter(max_count=3, window_seconds=60)
# 发送验证码（所有用途）：3 次/分钟（防止邮件轰炸与成本消耗）
limit_send_code = _make_limiter(max_count=3, window_seconds=60)
# 重置密码：3 次/分钟（防止验证码爆破）
limit_reset_password = _make_limiter(max_count=3, window_seconds=60)
