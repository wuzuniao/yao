from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...schemas.checkin_record import CreateCheckin
from ...services.checkin_service import CheckinService
from ...utils.timezone import SHANGHAI_TZ

router = APIRouter()


def _record_to_dict(record) -> dict:
    """将 CheckinRecord 对象转换为响应字典"""
    return {
        "id": record.id,
        "user_id": record.user_id,
        "plan_id": record.plan_id,
        "plan_time_id": record.plan_time_id,
        "actual_time": record.actual_time.isoformat() if record.actual_time else None,
    }


@router.post("")
async def create_checkin(payload: CreateCheckin, db: AsyncSession = Depends(get_db)):
    """
    创建打卡记录
    - 同一天同一计划同一时间点只能打卡一次
    """
    service = CheckinService(db)
    try:
        actual_time = datetime.fromisoformat(payload.actual_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="打卡时间格式不正确")
    # 确保写入数据库的是 naive Shanghai datetime（无 tzinfo）
    # 前端应发送无时区后缀的本地时间字符串（如 2026-07-02T14:30:00）
    # 若前端误传带时区的字符串（如 ...Z 或 ...+08:00），转换为上海时间后去除时区标记
    if actual_time.tzinfo is not None:
        actual_time = actual_time.astimezone(SHANGHAI_TZ).replace(tzinfo=None)
    try:
        record = await service.create_checkin(
            user_id=payload.user_id,
            plan_id=payload.plan_id,
            plan_time_id=payload.plan_time_id,
            actual_time=actual_time,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "打卡成功",
        "data": _record_to_dict(record),
    }


@router.get("/{user_id}/today")
async def list_today_checkins(user_id: int, db: AsyncSession = Depends(get_db)):
    """查询用户今日所有打卡记录"""
    service = CheckinService(db)
    records = await service.list_today_by_user(user_id)
    return {
        "code": 0,
        "msg": "success",
        "data": [_record_to_dict(r) for r in records],
    }


@router.get("/{user_id}/today/{plan_id}")
async def list_today_checkins_by_plan(
    user_id: int, plan_id: int, db: AsyncSession = Depends(get_db)
):
    """查询用户今日某计划的打卡记录（返回已打卡的时间点ID列表）"""
    service = CheckinService(db)
    records = await service.list_today_by_plan(user_id, plan_id)
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "checked_time_ids": [r.plan_time_id for r in records],
            "records": [_record_to_dict(r) for r in records],
        },
    }


@router.get("/{user_id}/month")
async def list_month_checkins(
    user_id: int,
    year: int = Query(..., description="年份，如 2026"),
    month: int = Query(..., ge=1, le=12, description="月份，1-12"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询用户某月有打卡记录的日期列表
    - 用于日历小绿点标识
    - 返回 checked_days：当月有打卡记录的日期（day of month）列表
    """
    service = CheckinService(db)
    checked_days = await service.list_by_month(user_id, year, month)
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "checked_days": checked_days,
        },
    }


@router.get("/{user_id}/day")
async def list_day_checkins(
    user_id: int,
    date: str = Query(..., description="日期，格式 YYYY-MM-DD，如 2026-06-15"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询用户某天的打卡详情（含计划提醒时间）
    - 返回当天所有进行中计划的提醒时间及打卡状态
    - 已打卡：checked=true + actual_time
    - 未打卡：checked=false，actual_time=null
    """
    service = CheckinService(db)
    try:
        day_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式不正确，应为 YYYY-MM-DD")
    detail = await service.list_day_detail(user_id, day_date)
    return {
        "code": 0,
        "msg": "success",
        "data": detail,
    }
