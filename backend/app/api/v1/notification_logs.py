from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...schemas.notification_log import MarkRead
from ...services.notification_log_service import NotificationLogService

router = APIRouter()


@router.get("/{user_id}/list")
async def list_notification_logs(
    user_id: int,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    limit: int = Query(20, ge=1, le=100, description="每页数量，1-100"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询用户站内信列表（分页）
    - 返回当前用户所有站内信（含计划名称/备注），未读卡片前端高亮显示
    - 返回 unread_count 用于通知按钮图标切换
    """
    service = NotificationLogService(db)
    data = await service.list_znx_by_user(user_id, page, limit)
    return {"code": 0, "msg": "success", "data": data}


@router.put("/read")
async def mark_as_read(payload: MarkRead, db: AsyncSession = Depends(get_db)):
    """
    标记站内信为已读（status 2 → 0）
    - 校验消息归属后更新状态
    - 已读记录重复标记不报错
    """
    service = NotificationLogService(db)
    try:
        log = await service.mark_as_read(payload.log_id, payload.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "已标记为已读",
        "data": {
            "id": log.id,
            "status": log.status,
            "is_unread": False,
        },
    }


@router.get("/{user_id}/unread-count")
async def get_unread_count(user_id: int, db: AsyncSession = Depends(get_db)):
    """查询用户未读站内信数量（用于通知图标实时切换）"""
    service = NotificationLogService(db)
    count = await service.count_unread(user_id)
    return {"code": 0, "msg": "success", "data": {"unread_count": count}}
