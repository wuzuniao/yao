from datetime import date
from typing import List

from pydantic import BaseModel, field_validator

from ..core.security import Security


class CreatePlan(BaseModel):
    """
    创建计划请求 Schema
    - user_id 由 JWT 提供，不入请求体
    - 日期为起止日期范围（start_date / end_date）
    - 时间为单个时间数组（支持多个通知时间点）
    - 通知方式为通知渠道ID数组
    - status：1-进行中，2-暂停，0-已结束（默认1-进行中）
    - priority：优先级，数字越小优先级越高（范围0-7，默认3）
    """

    name: str
    remark: str = ""
    start_date: date
    end_date: date
    notification_times: List[str]  # ["08:00", "20:00"] HH:MM 格式
    channel_ids: List[int]  # 关联的通知渠道ID列表
    status: int = 1  # 默认进行中
    priority: int = 3  # 默认优先级3（数字越小优先级越高，范围0-7）

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = Security.sanitize_string(v, max_length=100, field_name="计划名称")
        if not v:
            raise ValueError("计划名称不能为空")
        return v

    @field_validator("remark")
    @classmethod
    def validate_remark(cls, v: str) -> str:
        return Security.sanitize_string(v, max_length=255, field_name="备注")

    @field_validator("notification_times")
    @classmethod
    def validate_notification_times(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("至少设置一个通知时间")
        for t in v:
            # 校验 HH:MM 或 HH:MM:SS 格式
            parts = t.split(":")
            if len(parts) < 2 or len(parts) > 3:
                raise ValueError(f"时间格式不正确：{t}")
            try:
                h, m = int(parts[0]), int(parts[1])
                if h < 0 or h > 23 or m < 0 or m > 59:
                    raise ValueError(f"时间范围不正确：{t}")
            except ValueError:
                raise ValueError(f"时间格式不正确：{t}")
        return v

    @field_validator("channel_ids")
    @classmethod
    def validate_channel_ids(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError("至少选择一个通知方式")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: int) -> int:
        if v not in (0, 1, 2):
            raise ValueError("任务状态值只能为 0、1、2")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        if v < 0 or v > 7:
            raise ValueError("优先级范围 0-7")
        return v


class UpdatePlan(CreatePlan):
    """更新计划请求 Schema（复用 CreatePlan 全部字段校验，plan_id 由 URL 路径参数提供）"""
