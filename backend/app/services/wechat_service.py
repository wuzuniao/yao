"""微信服务：access_token 缓存与订阅消息下发。

说明：
- 微信「一次性订阅消息」需用户在小程序内主动授权（wx.requestSubscribeMessage），
  服务端凭 access_token 调用 subscribe/send 下发，一次授权对应一条消息。
- access_token 有效期 7200 秒，模块级缓存避免频繁拉取。
"""
import asyncio
import time

import httpx

from ..core.config import settings
from ..utils.logger import logger

# 微信接口地址
_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
_SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/subscribe/send"

# access_token 缓存（单进程共享，提前 5 分钟过期避免边界失效）
_token_cache: dict = {"access_token": "", "expire_at": 0.0}
_token_lock = asyncio.Lock()

# 微信订阅消息常见错误码
ERRCODE_NO_PERMISSION = 43101  # 用户拒绝或未授权（额度已失效）
ERRCODE_INVALID_TOKEN = 40001
ERRCODE_EXPIRED_TOKEN = 42001


class WeChatService:
    """微信开放平台接口封装（订阅消息）"""

    @classmethod
    async def get_access_token(cls) -> str:
        """获取并缓存 access_token，临近过期自动刷新。"""
        async with _token_lock:
            if _token_cache["access_token"] and time.time() < _token_cache["expire_at"]:
                return _token_cache["access_token"]
            params = {
                "grant_type": "client_credential",
                "appid": settings.WX_APPID,
                "secret": settings.WX_APP_SECRET,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(_TOKEN_URL, params=params, timeout=10)
                data = resp.json()
            if data.get("errcode", 0) != 0:
                raise RuntimeError(
                    f"获取微信 access_token 失败：{data.get('errcode')} {data.get('errmsg', '未知错误')}"
                )
            _token_cache["access_token"] = data["access_token"]
            _token_cache["expire_at"] = time.time() + data.get("expires_in", 7200) - 300
            return _token_cache["access_token"]

    @classmethod
    async def send_subscribe_message(
        cls, openid: str, template_id: str, data: dict, page: str | None = None
    ) -> dict:
        """发送订阅消息，返回微信接口原始响应（含 errcode/errmsg）。

        :param openid: 接收者 openid
        :param template_id: 订阅消息模板 ID
        :param data: 模板字段，形如 {"thing4": {"value": "打卡提醒"}}
        :param page: 点击后跳转的小程序页面路径
        """
        token = await cls.get_access_token()
        payload: dict = {"touser": openid, "template_id": template_id, "data": data}
        if page:
            payload["page"] = page
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _SEND_URL, params={"access_token": token}, json=payload, timeout=10
            )
            result = resp.json()
        if result.get("errcode", 0) != 0:
            logger.warning(
                f"微信订阅消息发送失败 openid={openid} "
                f"errcode={result.get('errcode')} errmsg={result.get('errmsg')}"
            )
        return result
