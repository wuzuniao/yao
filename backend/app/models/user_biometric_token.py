from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func

from ..core.database import Base


class UserBiometricToken(Base):
    """用户生物识别登录凭证 ORM 模型（对应 wuzuniao_yonghu.user_biometric_tokens 表）"""

    __tablename__ = "user_biometric_tokens"
    __table_args__ = {"schema": "wuzuniao_yonghu"}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True, comment="关联 users.id")
    token = Column(String(64), nullable=False, unique=True, comment="生物识别凭证（高熵随机串）")
    device_id = Column(String(64), nullable=False, comment="设备标识（前端首次登录生成的 UUID）")
    expire_at = Column(DateTime, nullable=False, comment="过期时间（默认 31 天）")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
