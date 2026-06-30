from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func

from ..core.database import Base


class UserMiniappAccount(Base):
    """用户-小程序绑定关系 ORM 模型（对应 wuzuniao_yonghu.user_miniapp_accounts 表）"""

    __tablename__ = "user_miniapp_accounts"
    __table_args__ = {"schema": "wuzuniao_yonghu"}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True, comment="关联 users.id")
    app_id = Column(String(64), nullable=False, comment="微信小程序 AppID")
    openid = Column(String(100), nullable=False, comment="该小程序下的 OpenID")
    session_key = Column(String(255), nullable=True, comment="会话密钥（临时存储，用于解密数据）")
    created_at = Column(DateTime, server_default=func.now())
