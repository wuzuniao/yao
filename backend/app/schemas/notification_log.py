from pydantic import BaseModel, field_validator

from ..core.security import Security


# 通知发送状态常量（与 notification_logs.status 字段对应）
LOG_STATUS_SUCCESS = 0  # 成功（站内信：已读）
LOG_STATUS_FAILED = 1   # 失败（邮件发送失败等）
LOG_STATUS_UNREAD = 2   # 未读（站内信：待读，高亮显示）

# 触发类型常量（与 notification_logs.trigger_type 字段对应）
TRIGGER_ON_TIME = 0                    # 准时提醒（到达提醒时间即触发）
TRIGGER_OFFSET_10MIN = 1               # 超时10分钟催办
TRIGGER_OFFSET_1HOUR_OR_MIDPOINT = 2   # 1小时或中点催办（择先到达者）

# 催办档位1固定偏移（分钟）；档位2为动态计算，无固定偏移
FOLLOWUP_OFFSET_10MIN: int = 10

# 触发类型对应的中文描述（邮件正文用）
TRIGGER_DESC: dict[int, str] = {
    TRIGGER_ON_TIME: "到了打卡时间",
    TRIGGER_OFFSET_10MIN: "已超过打卡时间10分钟",
    TRIGGER_OFFSET_1HOUR_OR_MIDPOINT: "已超过打卡时间较久",
}


class MarkRead(BaseModel):
    """标记站内信为已读请求 Schema（user_id 由 JWT 提供，不入请求体）"""

    log_id: int

    @field_validator("log_id")
    @classmethod
    def validate_log_id(cls, v: int) -> int:
        return Security.validate_positive_int(v, "消息ID")
