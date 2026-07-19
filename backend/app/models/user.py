from sqlalchemy import Column, BigInteger, String, DateTime, SmallInteger
from sqlalchemy.sql import func

from ..core.database import Base


class User(Base):
    """用户主表 ORM 模型（对应 wuzuniao_yonghu.users 表）"""

    __tablename__ = "users"
    # 用户表位于独立的用户库 wuzuniao_yonghu，业务库 wuzuniao_yao 通过跨库查询访问
    __table_args__ = {"schema": "wuzuniao_yonghu"}

    id = Column(BigInteger, primary_key=True, index=True)
    # 用户名长度限制：基于 settings.vue 资料卡文本区（约191px，28px字体）可视字符约9个 × 1.5 ≈ 15
    username = Column(String(15), unique=True, index=True, nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    # 签名长度限制：基于 settings.vue 资料卡3行文本区（约191px，16px字体）可视字符约46个 × 1.5 ≈ 70
    signature = Column(String(70), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    # status：1-正常，0-待删除（用户确认删除后置0，后台任务24小时后清理）
    status = Column(SmallInteger, nullable=False, default=1, comment="状态：1-正常，0-待删除（后台任务24小时后清理）")
    # role：0-普通用户（默认），7-管理员
    role = Column(SmallInteger, nullable=False, default=0, comment="角色：0-普通用户，7-管理员")
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
