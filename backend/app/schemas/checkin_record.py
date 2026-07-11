from datetime import datetime
from pydantic import BaseModel, field_validator

from ..core.security import Security


class CreateCheckin(BaseModel):
    """
    打卡请求 Schema
    - user_id 由 JWT 提供，不入请求体
    - plan_id：所属计划ID
    - plan_time_id：对应的通知时间点ID
    - actual_time：实际打卡时间（ISO 格式字符串，如 2026-07-01T08:30:00）
    """

    plan_id: int
    plan_time_id: int
    actual_time: str

    @field_validator("plan_id")
    @classmethod
    def validate_plan_id(cls, v: int) -> int:
        return Security.validate_positive_int(v, "计划ID")

    @field_validator("plan_time_id")
    @classmethod
    def validate_plan_time_id(cls, v: int) -> int:
        return Security.validate_positive_int(v, "时间点ID")

    @field_validator("actual_time")
    @classmethod
    def validate_actual_time(cls, v: str) -> str:
        if not v:
            raise ValueError("打卡时间不能为空")
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("打卡时间格式不正确，应为 ISO 格式")
        return v
