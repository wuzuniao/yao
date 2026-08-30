from datetime import date
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator

from ..core.security import Security
from ..models.plan import PLAN_END_DATE_SENTINEL


class NotificationTimeItem(BaseModel):
    """
    单个提醒时间点设置（时间 + 提醒次数/间隔）
    - time：每日提醒时刻，HH:MM 或 HH:MM:SS 格式
    - followup_count：提醒总次数（含准时那次）
      3=默认三段式（准时 → +10分钟 → +1小时或中点，间隔参数不生效）
      1=仅准时；2=准时 + 提醒时间+间隔 各一次（自定义等间隔）
    - followup_interval_min：自定义等间隔的间隔分钟（5-60，仅 followup_count=1/2 生效）
    """

    time: str
    followup_count: int = 3
    followup_interval_min: int = 10

    @field_validator("time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        # 校验 HH:MM 或 HH:MM:SS 格式
        parts = v.split(":")
        if len(parts) < 2 or len(parts) > 3:
            raise ValueError(f"时间格式不正确：{v}")
        # 仅非数字字符才算"格式不正确"，数字超范围才算"范围不正确"
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            raise ValueError(f"时间格式不正确：{v}")
        h, m = nums[0], nums[1]
        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError(f"时间范围不正确：{v}")
        # 校验秒数范围（HH:MM:SS 格式），缺失秒数视为 0
        if len(nums) == 3 and (nums[2] < 0 or nums[2] > 59):
            raise ValueError(f"时间范围不正确：{v}")
        return v

    @field_validator("followup_count")
    @classmethod
    def validate_followup_count(cls, v: int) -> int:
        if v not in (1, 2, 3):
            raise ValueError("提醒次数只能为 1、2、3")
        return v

    @field_validator("followup_interval_min")
    @classmethod
    def validate_followup_interval_min(cls, v: int) -> int:
        if v < 5 or v > 60:
            raise ValueError("提醒间隔范围 5-60 分钟")
        return v

    @model_validator(mode="after")
    def normalize_interval(self) -> "NotificationTimeItem":
        """默认三段式（count=3）不使用间隔参数，统一归位默认值 10，保证存量数据干净"""
        if self.followup_count == 3:
            self.followup_interval_min = 10
        return self


class CreatePlan(BaseModel):
    """
    创建计划请求 Schema
    - user_id 由 JWT 提供，不入请求体
    - 日期为起止日期范围（start_date / end_date）；end_date 按结束方式可选：
      end_mode=0（按日期）必填，end_mode=1/2 可缺省（服务端落 9999-12-31 哨兵值）
    - repeat_weekdays：重复星期位掩码，bit0=周一…bit6=周日（127=每天，31=工作日，96=周末）
    - end_mode：结束方式 0-按end_date / 1-按打卡总次数 / 2-长期不结束
    - notification_times 为对象数组（时间 + 提醒次数/间隔）
    - 通知方式为通知渠道ID数组
    - status：1-进行中，2-暂停，0-已结束（默认1-进行中）
    - priority：优先级，数字越小优先级越高（范围0-3，默认3）
    """

    name: str
    remark: str = ""
    start_date: date
    end_date: Optional[date] = None
    repeat_weekdays: int = 127
    end_mode: int = 0
    total_target_count: Optional[int] = None
    notification_times: List[NotificationTimeItem]
    channel_ids: List[int]  # 关联的通知渠道ID列表
    status: int = 1  # 默认进行中
    priority: int = 3  # 默认优先级3（数字越小优先级越高，范围0-3）

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

    @field_validator("repeat_weekdays")
    @classmethod
    def validate_repeat_weekdays(cls, v: int) -> int:
        if v < 1 or v > 127:
            raise ValueError("重复星期掩码范围 1-127")
        return v

    @field_validator("end_mode")
    @classmethod
    def validate_end_mode(cls, v: int) -> int:
        if v not in (0, 1, 2):
            raise ValueError("结束方式只能为 0、1、2")
        return v

    @field_validator("total_target_count")
    @classmethod
    def validate_total_target_count(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 9999):
            raise ValueError("目标打卡次数范围 1-9999")
        return v

    @model_validator(mode="after")
    def validate_end_mode_fields(self) -> "CreatePlan":
        """按结束方式校验关联字段：按日期须有 end_date，按次数须有 total_target_count"""
        if self.end_mode == 0:
            if self.end_date is None:
                raise ValueError("按日期结束时必须选择结束日期")
            if self.end_date < self.start_date:
                raise ValueError("结束日期不能早于开始日期")
        elif self.end_mode == 1:
            if self.total_target_count is None:
                raise ValueError("按打卡次数结束时必须填写目标次数")
        return self

    @field_validator("notification_times")
    @classmethod
    def validate_notification_times(cls, v: List[NotificationTimeItem]) -> List[NotificationTimeItem]:
        if not v:
            raise ValueError("至少设置一个通知时间")
        # 重复时间校验：相同时间会产生两个独立时间点（调度器防重键含 plan_time_id），
        # 各发一条导致重复提醒、匹配区间重叠——保存前拦截
        # 归一化为 (时,分,秒) 元组比较，覆盖 "08:00" 与 "08:00:00" 混写的同刻时间
        normalized = set()
        for item in v:
            parts = item.time.split(":")
            nums = [int(p) for p in parts] + [0] * (3 - len(parts))
            key = (nums[0], nums[1], nums[2])
            if key in normalized:
                raise ValueError("提醒时间不能重复")
            normalized.add(key)
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
        if v < 0 or v > 3:
            raise ValueError("优先级范围 0-3")
        return v

    @property
    def effective_end_date(self) -> date:
        """按结束方式推导实际落库的结束日期：end_mode=1/2 用哨兵值（调度查询零改动即永续）"""
        if self.end_mode != 0:
            return PLAN_END_DATE_SENTINEL
        return self.end_date  # type: ignore[return-value]  # end_mode=0 已由 model_validator 保证非空


class UpdatePlan(CreatePlan):
    """更新计划请求 Schema（复用 CreatePlan 全部字段校验，plan_id 由 URL 路径参数提供）"""
