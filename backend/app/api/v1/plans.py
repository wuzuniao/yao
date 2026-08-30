from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.deps import get_current_user_id
from ...core.rate_limit import limit_authenticated
from ...schemas.plan import CreatePlan, UpdatePlan
from ...services.plan_service import PlanService

router = APIRouter()


def _plan_to_dict(plan) -> dict:
    """将 CheckinPlan 对象转换为响应字典（含时间点、重复规则、结束方式与关联渠道）"""
    return {
        "id": plan.id,
        "user_id": plan.user_id,
        "name": plan.name,
        "remark": plan.remark or "",
        "start_date": plan.start_date.isoformat() if plan.start_date else None,
        "end_date": plan.end_date.isoformat() if plan.end_date else None,
        "repeat_weekdays": plan.repeat_weekdays,
        "end_mode": plan.end_mode,
        "total_target_count": plan.total_target_count,
        "status": plan.status,
        "priority": plan.priority,
        "notification_times": [
            {
                "id": nt.id,
                "notification_time": nt.notification_time.strftime("%H:%M"),
                "followup_count": nt.followup_count,
                "followup_interval_min": nt.followup_interval_min,
            }
            for nt in (plan.notification_times or [])
        ],
        "channel_ids": [ch.channel_id for ch in (plan.channels or [])],
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


@router.get("/list", dependencies=[Depends(limit_authenticated)])
async def list_plans(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """查询当前登录用户的所有计划（user_id 来自 JWT）"""
    service = PlanService(db)
    plans = await service.list_by_user(user_id)
    return {
        "code": 0,
        "msg": "success",
        "data": [_plan_to_dict(p) for p in plans],
    }


@router.post("", dependencies=[Depends(limit_authenticated)])
async def create_plan(
    payload: CreatePlan,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建计划（user_id 来自 JWT，含通知时间点、重复规则、结束方式与关联渠道）"""
    service = PlanService(db)
    try:
        plan = await service.create_plan(
            user_id=user_id,
            name=payload.name,
            remark=payload.remark,
            start_date=payload.start_date,
            end_date=payload.effective_end_date,
            notification_times=payload.notification_times,
            channel_ids=payload.channel_ids,
            status=payload.status,
            priority=payload.priority,
            repeat_weekdays=payload.repeat_weekdays,
            end_mode=payload.end_mode,
            total_target_count=payload.total_target_count,
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


@router.delete("/{plan_id}", dependencies=[Depends(limit_authenticated)])
async def delete_plan(
    plan_id: int = Path(..., gt=0, description="计划ID，必须为正整数"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除计划（user_id 来自 JWT，按 plan_id 级联删除关联的打卡记录、通知记录、时间点与渠道关联，通知渠道保留）"""
    service = PlanService(db)
    try:
        await service.delete_plan(plan_id=plan_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"code": 0, "msg": "计划删除成功", "data": None}


@router.put("/{plan_id}", dependencies=[Depends(limit_authenticated)])
async def update_plan(
    plan_id: int = Path(..., gt=0, description="计划ID，必须为正整数"),
    payload: UpdatePlan = Body(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新计划（user_id 来自 JWT，含通知时间点、重复规则、结束方式与关联渠道）"""
    service = PlanService(db)
    try:
        plan = await service.update_plan(
            plan_id=plan_id,
            user_id=user_id,
            name=payload.name,
            remark=payload.remark,
            start_date=payload.start_date,
            end_date=payload.effective_end_date,
            notification_times=payload.notification_times,
            channel_ids=payload.channel_ids,
            status=payload.status,
            priority=payload.priority,
            repeat_weekdays=payload.repeat_weekdays,
            end_mode=payload.end_mode,
            total_target_count=payload.total_target_count,
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
