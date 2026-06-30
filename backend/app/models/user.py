from sqlalchemy import Column, BigInteger, String, DateTime, SmallInteger
from sqlalchemy.sql import func

from ..core.database import Base


class User(Base):
    """用户主表 ORM 模型（对应 wuzuniao_yonghu.users 表）"""

    __tablename__ = "users"
    # 用户表位于独立的用户库 wuzuniao_yonghu，业务库 wuzuniao_yao 通过跨库查询访问
    __table_args__ = {"schema": "wuzuniao_yonghu"}

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    signature = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    status = Column(SmallInteger, nullable=False, default=1)
    last_login_at = Column(DateTime, nullable=True)
    deletion_scheduled_at = Column(DateTime, nullable=True, comment="账号注销计划时间（24小时后自动删除）")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
