from pydantic import BaseModel


# 通知发送状态常量（与 notification_logs.status 字段对应）
LOG_STATUS_SUCCESS = 0  # 成功（站内信：已读）
LOG_STATUS_FAILED = 1   # 失败（邮件发送失败等）
LOG_STATUS_UNREAD = 2   # 未读（站内信：待读，高亮显示）

# 触发类型常量（与 notification_logs.trigger_type 字段对应）
TRIGGER_ON_TIME = 0      # 准时提醒（到达提醒时间即触发）
TRIGGER_OFFSET_5MIN = 1  # 超时5分钟催办（提醒时间过5分钟仍未打卡）
TRIGGER_OFFSET_30MIN = 2 # 超时30分钟催办
TRIGGER_OFFSET_1HOUR = 3 # 超时1小时催办

# 催办偏移量（分钟）与触发类型映射，用于派发循环遍历
FOLLOWUP_OFFSETS: list[tuple[int, int]] = [
    (TRIGGER_OFFSET_5MIN, 5),
    (TRIGGER_OFFSET_30MIN, 30),
    (TRIGGER_OFFSET_1HOUR, 60),
]

# 触发类型对应的中文描述（邮件正文用）
TRIGGER_DESC: dict[int, str] = {
    TRIGGER_ON_TIME: "到了打卡时间",
    TRIGGER_OFFSET_5MIN: "已超过打卡时间5分钟",
    TRIGGER_OFFSET_30MIN: "已超过打卡时间30分钟",
    TRIGGER_OFFSET_1HOUR: "已超过打卡时间1小时",
}


class MarkRead(BaseModel):
    """标记站内信为已读请求 Schema"""

    log_id: int
    user_id: int
