from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...schemas.plan import CreatePlan, UpdatePlan
from ...services.plan_service import PlanService

router = APIRouter()


def _plan_to_dict(plan) -> dict:
    """将 CheckinPlan 对象转换为响应字典（含时间点和关联渠道）"""
    return {
        "id": plan.id,
        "user_id": plan.user_id,
        "name": plan.name,
        "remark": plan.remark or "",
        "start_date": plan.start_date.isoformat() if plan.start_date else None,
        "end_date": plan.end_date.isoformat() if plan.end_date else None,
        "status": plan.status,
        "priority": plan.priority,
        "notification_times": [
            {"id": nt.id, "notification_time": nt.notification_time.strftime("%H:%M")}
            for nt in (plan.notification_times or [])
        ],
        "channel_ids": [ch.channel_id for ch in (plan.channels or [])],
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


@router.get("/{user_id}/list")
async def list_plans(user_id: int, db: AsyncSession = Depends(get_db)):
    """查询用户的所有计划"""
    service = PlanService(db)
    plans = await service.list_by_user(user_id)
    return {
        "code": 0,
        "msg": "success",
        "data": [_plan_to_dict(p) for p in plans],
    }


@router.post("")
async def create_plan(payload: CreatePlan, db: AsyncSession = Depends(get_db)):
    """创建计划（含通知时间点和关联渠道）"""
    service = PlanService(db)
    try:
        plan = await service.create_plan(
            user_id=payload.user_id,
            name=payload.name,
            remark=payload.remark,
            start_date=payload.start_date,
            end_date=payload.end_date,
            notification_times=payload.notification_times,
            channel_ids=payload.channel_ids,
            status=payload.status,
            priority=payload.priority,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # 重新查询以加载关联关系
    plan = await service.get_by_id(plan.id)
    return {
        "code": 0,
        "msg": "计划创建成功",
        "data": _plan_to_dict(plan),
    }


@router.delete("/{plan_id}")
async def delete_plan(plan_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    """删除计划（同时删除关联的时间点和渠道）"""
    service = PlanService(db)
    try:
        await service.delete_plan(plan_id=plan_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"code": 0, "msg": "计划删除成功", "data": None}


@router.put("/{plan_id}")
async def update_plan(plan_id: int, payload: UpdatePlan, db: AsyncSession = Depends(get_db)):
    """更新计划（含通知时间点和关联渠道）"""
    service = PlanService(db)
    try:
        plan = await service.update_plan(
            plan_id=plan_id,
            user_id=payload.user_id,
            name=payload.name,
            remark=payload.remark,
            start_date=payload.start_date,
            end_date=payload.end_date,
            notification_times=payload.notification_times,
            channel_ids=payload.channel_ids,
            status=payload.status,
            priority=payload.priority,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # 重新查询以加载关联关系
    plan = await service.get_by_id(plan.id)
    return {
        "code": 0,
        "msg": "计划更新成功",
        "data": _plan_to_dict(plan),
    }
