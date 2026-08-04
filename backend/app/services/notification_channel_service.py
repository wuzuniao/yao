import json
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification_channel import NotificationChannel
from ..models.plan import PlanNotificationChannel
from ..schemas.notification_channel import (
    CHANNEL_TYPE_APP_PUSH,
    CHANNEL_TYPE_EMAIL,
    CHANNEL_TYPE_WECHAT,
    CHANNEL_TYPE_ZNX,
    AppPushChannelValue,
    AppPushDeviceToken,
    EmailChannelValue,
)
from ..utils.crypto import encrypt
from ..utils.logger import logger
from ..utils.timezone import now_shanghai


class NotificationChannelService:
    """
    通知渠道业务逻辑服务
    --------------------------------------------------------------------------
    - 站内信：注册时自动创建，channel_value=用户ID，不允许用户删除/修改
    - 邮件：用户主动配置，channel_value=JSON 字符串（含 SMTP 配置），可增删改
    - App 推送：App 端用户主动添加，每用户仅一行，channel_value=JSON（设备 token 数组）
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_user(self, user_id: int) -> list[NotificationChannel]:
        """查询用户的所有通知渠道"""
        result = await self.db.execute(
            select(NotificationChannel).where(NotificationChannel.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, channel_id: int) -> NotificationChannel | None:
        """根据ID查询渠道"""
        result = await self.db.execute(
            select(NotificationChannel).where(NotificationChannel.id == channel_id)
        )
        return result.scalar_one_or_none()

    async def ensure_znx_channel(self, user_id: int) -> NotificationChannel:
        """
        为用户创建/获取站内信通知渠道（注册时调用）
        - 若已存在则返回现有记录，否则创建新记录
        - channel_value = 用户ID（字符串形式）
        """
        result = await self.db.execute(
            select(NotificationChannel).where(
                NotificationChannel.user_id == user_id,
                NotificationChannel.channel_type == CHANNEL_TYPE_ZNX,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        channel = NotificationChannel(
            user_id=user_id,
            channel_type=CHANNEL_TYPE_ZNX,
            channel_value=str(user_id),
            enabled=True,
        )
        self.db.add(channel)
        await self.db.flush()
        return channel

    async def create_email_channel(
        self,
        user_id: int,
        smtp_host: str,
        smtp_port: int,
        email: str,
        password: str,
        enabled: bool = True,
    ) -> NotificationChannel:
        """
        创建邮件通知渠道
        - 同一用户同一邮箱地址只能配置一次
        - channel_value 以 JSON 字符串形式存储 SMTP 配置
        - enabled 控制是否启用
        """
        # 检查是否已存在相同邮箱地址的邮件渠道
        existing_channels = await self.list_by_user(user_id)
        for ch in existing_channels:
            if ch.channel_type != CHANNEL_TYPE_EMAIL:
                continue
            try:
                cfg = EmailChannelValue.model_validate_json(ch.channel_value)
                if cfg.email == email:
                    raise ValueError("该发件邮箱地址已配置")
            except ValueError as e:
                if "已配置" in str(e):
                    raise
                # 解析失败的旧记录忽略，继续创建
                logger.warning(f"用户 {user_id} 邮件渠道 {ch.id} JSON 解析失败：{e}")

        cfg = EmailChannelValue(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            email=email,
            password=encrypt(password),  # 客户端专用密码加密存储
        )
        channel = NotificationChannel(
            user_id=user_id,
            channel_type=CHANNEL_TYPE_EMAIL,
            channel_value=cfg.model_dump_json(),
            enabled=enabled,
        )
        self.db.add(channel)
        await self.db.commit()
        await self.db.refresh(channel)
        return channel

    async def update_email_channel(
        self,
        channel_id: int,
        user_id: int,
        smtp_host: str,
        smtp_port: int,
        email: str,
        password: str,
        enabled: bool = True,
    ) -> NotificationChannel:
        """
        更新邮件通知渠道配置（含 enabled 启用状态）
        - password 为空字符串时保留原密码（前端修改时不展示密码，仅用户重新输入才更新）
        - password 非空时加密后存储
        """
        channel = await self.get_by_id(channel_id)
        if not channel:
            raise ValueError("通知渠道不存在")
        if channel.user_id != user_id:
            raise ValueError("无权操作该通知渠道")
        if channel.channel_type != CHANNEL_TYPE_EMAIL:
            raise ValueError("仅邮件通知渠道支持修改")

        # password 为空时保留原加密密码
        if not password:
            old_cfg = self.parse_email_channel_value(channel.channel_value)
            stored_password = old_cfg.get("password", "") if old_cfg else ""
        else:
            stored_password = encrypt(password)

        cfg = EmailChannelValue(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            email=email,
            password=stored_password,
        )
        channel.channel_value = cfg.model_dump_json()
        channel.enabled = enabled
        channel.updated_at = now_shanghai()
        await self.db.commit()
        await self.db.refresh(channel)
        return channel

    async def update_wechat_enabled(
        self, channel_id: int, user_id: int, enabled: bool
    ) -> NotificationChannel:
        """更新微信通知渠道的启用状态（仅微信渠道支持，授权额度不变）"""
        channel = await self.get_by_id(channel_id)
        if not channel:
            raise ValueError("通知渠道不存在")
        if channel.user_id != user_id:
            raise ValueError("无权操作该通知渠道")
        if channel.channel_type != CHANNEL_TYPE_WECHAT:
            raise ValueError("仅微信通知渠道支持该操作")
        channel.enabled = enabled
        channel.updated_at = now_shanghai()
        await self.db.commit()
        await self.db.refresh(channel)
        return channel

    async def delete_channel(self, channel_id: int, user_id: int) -> None:
        """
        删除通知渠道
        - 站内信渠道不允许删除
        - 同步删除引用该渠道的计划-渠道关联（plan_notification_channels），
          不影响计划本身
        """
        channel = await self.get_by_id(channel_id)
        if not channel:
            raise ValueError("通知渠道不存在")
        if channel.user_id != user_id:
            raise ValueError("无权操作该通知渠道")
        if channel.channel_type == CHANNEL_TYPE_ZNX:
            raise ValueError("站内信通知方式不允许删除")
        # 先清理计划-渠道关联（plan_notification_channels.channel_id 无物理外键约束）
        await self.db.execute(
            delete(PlanNotificationChannel).where(
                PlanNotificationChannel.channel_id == channel_id
            )
        )
        await self.db.delete(channel)
        await self.db.commit()

    async def update_app_push_enabled(
        self, channel_id: int, user_id: int, enabled: bool
    ) -> NotificationChannel:
        """更新 App 推送通知渠道的启用状态（仅 App 推送渠道支持，不改动设备 token 数组）"""
        channel = await self.get_by_id(channel_id)
        if not channel:
            raise ValueError("通知渠道不存在")
        if channel.user_id != user_id:
            raise ValueError("无权操作该通知渠道")
        if channel.channel_type != CHANNEL_TYPE_APP_PUSH:
            raise ValueError("仅 App 推送通知渠道支持该操作")
        channel.enabled = enabled
        channel.updated_at = now_shanghai()
        await self.db.commit()
        await self.db.refresh(channel)
        return channel

    @staticmethod
    def parse_email_channel_value(channel_value: str) -> dict[str, Any] | None:
        """解析邮件渠道的 channel_value JSON 为字典（失败返回 None）"""
        try:
            return json.loads(channel_value)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # 微信订阅消息渠道（一次性订阅：授权额度制）
    # channel_value 结构：{"granted": int, "sent": int}
    #   granted：用户累计授权次数（每次 accept +1）
    #   sent：已成功下发次数（每次成功下发 +1）
    #   remaining = granted - sent 即剩余可下发次数
    # ------------------------------------------------------------------
    @staticmethod
    def parse_wechat_channel_value(channel_value: str) -> dict[str, int]:
        """解析微信渠道的 channel_value，返回 {granted, sent}（缺省为 0）"""
        try:
            data = json.loads(channel_value) if channel_value else {}
        except (json.JSONDecodeError, TypeError):
            data = {}
        return {
            "granted": int(data.get("granted", 0) or 0),
            "sent": int(data.get("sent", 0) or 0),
        }

    async def get_or_create_wechat_channel(self, user_id: int) -> NotificationChannel:
        """获取或创建微信通知渠道（创建时默认启用）"""
        result = await self.db.execute(
            select(NotificationChannel).where(
                NotificationChannel.user_id == user_id,
                NotificationChannel.channel_type == CHANNEL_TYPE_WECHAT,
            )
        )
        channel = result.scalar_one_or_none()
        if not channel:
            channel = NotificationChannel(
                user_id=user_id,
                channel_type=CHANNEL_TYPE_WECHAT,
                channel_value=json.dumps({"granted": 0, "sent": 0}, ensure_ascii=False),
                enabled=True,
            )
            self.db.add(channel)
            await self.db.commit()
            await self.db.refresh(channel)
        return channel

    async def grant_wechat(self, user_id: int) -> dict[str, Any]:
        """
        微信订阅授权回调：用户每同意一次授权即 +1 额度并启用该渠道。
        返回 {enabled, granted, sent, remaining} 供前端展示。
        """
        channel = await self.get_or_create_wechat_channel(user_id)
        channel.enabled = True
        quota = self.parse_wechat_channel_value(channel.channel_value)
        quota["granted"] += 1
        channel.channel_value = json.dumps(quota, ensure_ascii=False)
        channel.updated_at = now_shanghai()
        await self.db.commit()
        await self.db.refresh(channel)
        return {
            "enabled": True,
            "granted": quota["granted"],
            "sent": quota["sent"],
            "remaining": quota["granted"] - quota["sent"],
        }

    # ------------------------------------------------------------------
    # App 推送渠道（友盟+ U-Push）
    # 每用户仅一行（channel_type=CHANNEL_TYPE_APP_PUSH 即 'App推送'），多设备共存于 channel_value 数组中
    # channel_value 结构：
    #   {"device_tokens": [{"token": "...", "platform": "android|ios", "fail_count": 0}]}
    #   token：友盟 SDK 返回的设备唯一标识（device_token）
    #   platform：设备平台，决定派发时使用哪套友盟应用密钥
    #   fail_count：连续下发失败次数，成功即归零，累计满 3 次剔除该 token
    # ------------------------------------------------------------------
    @staticmethod
    def parse_app_push_channel_value(channel_value: str) -> AppPushChannelValue:
        """解析 App 推送渠道的 channel_value，非法数据返回空数组（不抛异常）"""
        try:
            return AppPushChannelValue.model_validate_json(channel_value or "{}")
        except Exception:
            return AppPushChannelValue()

    async def get_app_push_channel(self, user_id: int) -> NotificationChannel | None:
        """查询用户的 App 推送渠道（每用户至多一行，不存在返回 None）"""
        result = await self.db.execute(
            select(NotificationChannel).where(
                NotificationChannel.user_id == user_id,
                NotificationChannel.channel_type == CHANNEL_TYPE_APP_PUSH,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_app_push_token(
        self,
        user_id: int,
        device_token: str,
        platform: str,
        create_if_missing: bool = False,
    ) -> NotificationChannel | None:
        """
        上报 App 设备 token（通知方式页添加 / App 端打卡完成时刷新）

        - 渠道行不存在时：create_if_missing=True 才新建（通知方式页添加）；
          False 则直接返回 None（打卡上报仅刷新，不自动建行）
        - token 已存在：重置 fail_count=0，并更新 platform（设备重装换平台的兜底）
        - token 不存在：追加到数组末尾
        """
        channel = await self.get_app_push_channel(user_id)
        if not channel:
            if not create_if_missing:
                return None
            cfg = AppPushChannelValue(
                device_tokens=[
                    AppPushDeviceToken(token=device_token, platform=platform, fail_count=0)
                ]
            )
            channel = NotificationChannel(
                user_id=user_id,
                channel_type=CHANNEL_TYPE_APP_PUSH,
                channel_value=cfg.model_dump_json(),
                enabled=True,
            )
            self.db.add(channel)
            await self.db.commit()
            await self.db.refresh(channel)
            return channel

        cfg = self.parse_app_push_channel_value(channel.channel_value)
        for item in cfg.device_tokens:
            if item.token == device_token:
                item.fail_count = 0
                item.platform = platform  # type: ignore[assignment]
                break
        else:
            cfg.device_tokens.append(
                AppPushDeviceToken(token=device_token, platform=platform, fail_count=0)
            )
        channel.channel_value = cfg.model_dump_json()
        channel.updated_at = now_shanghai()
        await self.db.commit()
        await self.db.refresh(channel)
        return channel
