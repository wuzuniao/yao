from sqlalchemy import Column, BigInteger, String, SmallInteger, DateTime, Date
from sqlalchemy.sql import func

from ..core.database import Base


class NotificationLog(Base):
    """
    通知发送记录 ORM 模型（对应 wuzuniao_yao.notification_logs 表）
    --------------------------------------------------------------------------
    记录每次系统触发的通知发送结果，用于追踪站内信/邮件的送达状态
    - status：0-成功（站内信已读），1-失败，2-未读（站内信待读）
    - 站内信发送时 status=2（未读），用户阅读后更新为 0（已读）
    - trigger_type：0-准时提醒，1-超时5分钟，2-超时30分钟，3-超时1小时（催办）
    - plan_time_id + trigger_type + notify_date + channel_id 组成去重键，避免同一天重复发送
    - 外键字段不设物理约束（应用层保证引用完整性），仅建索引
    """

    __tablename__ = "notification_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    plan_id = Column(BigInteger, nullable=False, index=True, comment="关联计划ID（checkin_plans.id）")
    channel_id = Column(BigInteger, nullable=False, index=True, comment="使用的渠道ID（notification_channels.id）")
    plan_time_id = Column(BigInteger, nullable=True, comment="触发该通知的提醒时间点ID（plan_notification_times.id，用于催办去重）")
    user_id = Column(BigInteger, nullable=False, index=True, comment="接收者用户ID（冗余，方便查询）")
    send_time = Column(DateTime, nullable=False, comment="发送时间（实际触发时间）")
    notify_date = Column(Date, nullable=True, comment="通知归属日期（提醒时间所在日，跨天催办去重用）")
    status = Column(SmallInteger, nullable=False, comment="发送状态：0-成功/已读，1-失败，2-未读")
    trigger_type = Column(SmallInteger, nullable=False, default=0, comment="触发类型：0-准时，1-超5分钟，2-超30分钟，3-超1小时")
    error_msg = Column(String(255), nullable=True, comment="失败时的错误信息")
