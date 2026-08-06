"""友盟+ U-Push 服务：App 端离线推送（Android 厂商通道 / iOS APNs）。

说明：
- 友盟推送采用 HTTP + 签名方式调用：
  sign = MD5(请求方法 + 请求URL + 请求Body + App Master Secret)，全部大写拼接后取 32 位小写。
- Android 与 iOS 在友盟控制台是两个独立应用，各有一套 AppKey / App Master Secret，
  故按设备平台选择对应密钥，payload 结构也不同（Android=display_type，iOS=aps）。
- 采用 unicast（单播）按 device_token 定向下发，一次请求对应一个设备。
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import httpx

from ..core.config import settings
from ..utils.logger import logger

# 友盟推送接口地址（签名参与计算的 URL 必须与实际请求 URL 完全一致）
_SEND_URL = "http://msg.umeng.com/api/send"


class UmengPushError(Exception):
    """友盟推送失败异常（含错误码与描述，供调用方记录日志）"""


class UmengService:
    """友盟+ U-Push 接口封装（单播推送）"""

    @staticmethod
    def _get_credentials(platform: str) -> tuple[str, str]:
        """按设备平台取对应的 AppKey 与 App Master Secret，未配置则抛异常"""
        if platform == "ios":
            app_key = settings.UMENG_IOS_APP_KEY
            master_secret = settings.UMENG_IOS_MASTER_SECRET
        elif platform == "harmony":
            app_key = settings.UMENG_HARMONY_APP_KEY
            master_secret = settings.UMENG_HARMONY_MASTER_SECRET
        else:
            app_key = settings.UMENG_ANDROID_APP_KEY
            master_secret = settings.UMENG_ANDROID_MASTER_SECRET
        if not app_key or not master_secret:
            raise UmengPushError(f"友盟 {platform} 推送密钥未配置")
        return app_key, master_secret

    @staticmethod
    def _build_payload(platform: str, title: str, content: str, extra: dict[str, str]) -> dict[str, Any]:
        """构造不同平台的 payload 段（Android / Harmony 通知栏消息 / iOS APNs 消息）

        鸿蒙在友盟为独立应用但复用同一 unicast 接口，payload 与 Android 同源
        （均为 display_type=notification + body），故共用同一分支，仅密钥区分。
        """
        if platform == "ios":
            return {
                "aps": {
                    "alert": {"title": title, "body": content},
                    "sound": "default",
                    "badge": 1,
                },
                **extra,
            }
        return {
            "display_type": "notification",
            "body": {
                "ticker": title,
                "title": title,
                "text": content,
                "after_open": "go_app",  # 点击后打开应用，跳转由前端 click 事件处理
                "play_vibrate": "true",
                "play_sound": "true",
            },
            "extra": extra,
        }

    @classmethod
    def _sign(cls, url: str, body: str, master_secret: str) -> str:
        """计算友盟请求签名：MD5(POST + URL + Body + MasterSecret)"""
        raw = f"POST{url}{body}{master_secret}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    @classmethod
    async def send(
        cls,
        device_token: str,
        title: str,
        content: str,
        platform: str = "android",
        extra: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        向单个设备下发推送通知。

        :param device_token: 友盟 SDK 返回的设备唯一标识
        :param title: 通知标题
        :param content: 通知正文
        :param platform: 设备平台（android / ios / harmony），决定使用哪套密钥与 payload 结构
        :param extra: 附加字段（如 page 跳转路径），随通知透传给客户端
        :return: 友盟接口原始响应
        :raises UmengPushError: 密钥未配置、网络异常或友盟返回非 SUCCESS 时抛出
        """
        app_key, master_secret = cls._get_credentials(platform)
        payload = cls._build_payload(platform, title, content, extra or {})
        body_dict: dict[str, Any] = {
            "appkey": app_key,
            "timestamp": str(int(time.time() * 1000)),
            "type": "unicast",
            "device_tokens": device_token,
            "payload": payload,
            "production_mode": "true" if settings.UMENG_PRODUCTION_MODE else "false",
        }
        # 签名基于 Body 原文，故序列化结果必须与实际发送内容逐字节一致
        body = json.dumps(body_dict, ensure_ascii=False, separators=(",", ":"))
        sign = cls._sign(_SEND_URL, body, master_secret)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{_SEND_URL}?sign={sign}",
                    content=body.encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
                result = resp.json()
        except Exception as e:
            raise UmengPushError(f"友盟推送请求异常：{e}") from e

        if result.get("ret") != "SUCCESS":
            data = result.get("data", {}) or {}
            msg = f"{data.get('error_code', '')} {data.get('error_msg', result)}".strip()
            logger.warning(f"友盟推送失败 platform={platform} token={device_token[:8]}*** {msg}")
            raise UmengPushError(f"友盟推送失败：{msg}")
        return result
