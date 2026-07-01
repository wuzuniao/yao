import json
from datetime import datetime
from typing import Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification_channel import NotificationChannel
from ..schemas.notification_channel import (
    CHANNEL_TYPE_EMAIL,
    CHANNEL_TYPE_ZNX,
    EmailChannelValue,
)
from ..utils.crypto import encrypt, decrypt
from ..utils.logger import logger
from ..utils.timezone import now_shanghai


class NotificationChannelService:
    """
    通知渠道业务逻辑服务
    --------------------------------------------------------------------------
    - 站内信：注册时自动创建，channel_value=用户ID，不允许用户删除/修改
    - 邮件：用户主动配置，channel_value=JSON 字符串（含 SMTP 配置），可增删改
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

    async def delete_channel(self, channel_id: int, user_id: int) -> None:
        """
        删除通知渠道
        - 站内信渠道不允许删除
        """
        channel = await self.get_by_id(channel_id)
        if not channel:
            raise ValueError("通知渠道不存在")
        if channel.user_id != user_id:
            raise ValueError("无权操作该通知渠道")
        if channel.channel_type == CHANNEL_TYPE_ZNX:
            raise ValueError("站内信通知方式不允许删除")
        await self.db.delete(channel)
        await self.db.commit()

    @staticmethod
    def parse_email_channel_value(channel_value: str) -> dict[str, Any] | None:
        """解析邮件渠道的 channel_value JSON 为字典（失败返回 None）"""
        try:
            return json.loads(channel_value)
        except Exception:
            return None
