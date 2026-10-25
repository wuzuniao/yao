"""
共享 httpx.AsyncClient（进程级连接复用）
--------------------------------------------------------------------------
auth / 微信 / 友盟外呼共用一个客户端实例：TCP+TLS 连接按 host 池化复用，
避免每次外呼重建连接的握手开销（2026-10-25 性能优化；调度器每分钟批量
派发微信/App 推送时收益明显——此前每条通知一次完整 TLS 握手）。

- 默认超时 10 秒（与原各调用点逐请求传的 timeout=10 一致）
- 懒初始化：首次调用时创建；被关闭后（如测试收尾）下次调用自动重建
- main.py lifespan 收尾统一 aclose
"""

from __future__ import annotations

import httpx

# 外呼默认超时（秒）
HTTP_TIMEOUT_SECONDS: float = 10.0

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """获取共享 AsyncClient（懒初始化；已关闭时自动重建）"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS)
    return _client


async def close_http_client() -> None:
    """关闭共享客户端（main.py lifespan 收尾调用；幂等）"""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
