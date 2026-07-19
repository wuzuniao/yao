from sqlalchemy import Column, BigInteger, String, Text, DateTime
from sqlalchemy.sql import func

from ..core.database import Base


class Announcement(Base):
    """
    全站公告表 ORM 模型（对应 wuzuniao_yao.announcements 表）
    --------------------------------------------------------------------------
    每条公告一行，由管理员发布；用户侧投递后续实现
    """

    __tablename__ = "announcements"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="公告标题")
    content = Column(Text, nullable=False, comment="公告内容")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
