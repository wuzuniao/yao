from sqlalchemy import Column, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

from ..core.database import Base


class CheckinRecord(Base):
    """
    用户打卡记录 ORM 模型（对应 wuzuniao_yao.checkin_records 表）
    --------------------------------------------------------------------------
    存储用户每次实际打卡的操作记录
    - 允许重复打卡（同一计划同一时间点可多次打卡）
    """

    __tablename__ = "checkin_records"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True, comment="打卡用户ID")
    plan_id = Column(BigInteger, ForeignKey("checkin_plans.id"), nullable=False, index=True, comment="所属计划ID")
    plan_time_id = Column(BigInteger, ForeignKey("plan_notification_times.id"), nullable=False, index=True, comment="对应的通知时间点ID")
    actual_time = Column(DateTime, nullable=False, comment="实际打卡时间")

    plan = relationship("CheckinPlan", backref=backref("checkin_records", passive_deletes=True))
