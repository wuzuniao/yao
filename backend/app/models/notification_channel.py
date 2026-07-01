from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from ..core.database import Base


class NotificationChannel(Base):
    """
    用户通知渠道配置 ORM 模型（对应 wuzuniao_yao.notification_channels 表）
    --------------------------------------------------------------------------
    存储规范：
      - 站内信：channel_type='站内信'，channel_value=用户ID（字符串形式）
      - 邮件：channel_type='邮件'，channel_value=JSON 字符串（含 smtp_host/smtp_port/email/password）
    """

    __tablename__ = "notification_channels"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True, comment="所属用户ID（关联 users.id）")
    channel_type = Column(String(20), nullable=False, comment="通知类型（站内信、邮件）")
    channel_value = Column(Text, nullable=False, comment="通知值（站内信存用户ID；邮件存 JSON 配置）")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
