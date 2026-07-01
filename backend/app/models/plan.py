from sqlalchemy import Column, BigInteger, String, Integer, Date, SmallInteger, DateTime, Time, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class CheckinPlan(Base):
    """
    打卡计划主表 ORM 模型（对应 wuzuniao_yao.checkin_plans 表）
    --------------------------------------------------------------------------
    用户创建的每个打卡/通知计划，包含日期范围、状态等
    """

    __tablename__ = "checkin_plans"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True, comment="创建者用户ID")
    name = Column(String(100), nullable=False, comment="计划名称")
    remark = Column(String(255), nullable=True, comment="备注/描述")
    start_date = Column(Date, nullable=False, comment="开始日期")
    end_date = Column(Date, nullable=False, comment="结束日期")
    status = Column(SmallInteger, nullable=False, default=1, comment="状态：1-进行中，2-暂停，0-已结束")
    priority = Column(Integer, nullable=False, default=3, comment="优先级：数字越小优先级越高（范围0-7，默认3）")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联关系：通知时间点列表、关联通知渠道列表
    notification_times = relationship("PlanNotificationTime", back_populates="plan", cascade="all, delete-orphan")
    channels = relationship("PlanNotificationChannel", back_populates="plan", cascade="all, delete-orphan")


class PlanNotificationTime(Base):
    """
    每日通知时间点表 ORM 模型（对应 wuzuniao_yao.plan_notification_times 表）
    --------------------------------------------------------------------------
    每个计划可设置多个通知时刻（如 08:00、20:00）
    """

    __tablename__ = "plan_notification_times"

    id = Column(BigInteger, primary_key=True, index=True)
    plan_id = Column(BigInteger, ForeignKey("checkin_plans.id"), nullable=False, index=True, comment="所属计划ID")
    notification_time = Column(Time, nullable=False, comment="每日通知时刻（HH:MM:SS）")
    created_at = Column(DateTime, server_default=func.now())

    plan = relationship("CheckinPlan", back_populates="notification_times")


class PlanNotificationChannel(Base):
    """
    计划-通知渠道关联表 ORM 模型（对应 wuzuniao_yao.plan_notification_channels 表）
    --------------------------------------------------------------------------
    多对多关联：一个计划可绑定多个渠道，一个渠道可用于多个计划
    """

    __tablename__ = "plan_notification_channels"

    id = Column(BigInteger, primary_key=True, index=True)
    plan_id = Column(BigInteger, ForeignKey("checkin_plans.id"), nullable=False, index=True, comment="计划ID")
    channel_id = Column(BigInteger, nullable=False, index=True, comment="渠道ID")
    created_at = Column(DateTime, server_default=func.now())

    plan = relationship("CheckinPlan", back_populates="channels")
