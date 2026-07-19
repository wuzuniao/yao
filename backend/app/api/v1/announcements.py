from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.deps import get_current_admin
from ...schemas.announcement import AnnouncementCreate, AnnouncementUpdate
from ...services.announcement_service import AnnouncementService

router = APIRouter()


def _announcement_to_dict(announcement) -> dict:
    """将 Announcement 对象转换为响应字典"""
    return {
        "id": announcement.id,
        "title": announcement.title,
        "content": announcement.content,
        "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
        "updated_at": announcement.updated_at.isoformat() if announcement.updated_at else None,
    }


@router.get("")
async def list_announcements(
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """查询全部公告（仅管理员）"""
    service = AnnouncementService(db)
    announcements = await service.list_all()
    return {
        "code": 0,
        "msg": "success",
        "data": [_announcement_to_dict(a) for a in announcements],
    }


@router.post("")
async def publish_announcement(
    payload: AnnouncementCreate,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """发布公告（仅管理员）"""
    service = AnnouncementService(db)
    try:
        announcement = await service.publish(title=payload.title, content=payload.content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "公告发布成功",
        "data": _announcement_to_dict(announcement),
    }


@router.put("/{announcement_id}")
async def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新公告（仅管理员）"""
    service = AnnouncementService(db)
    try:
        announcement = await service.update(
            announcement_id=announcement_id,
            title=payload.title,
            content=payload.content,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "公告更新成功",
        "data": _announcement_to_dict(announcement),
    }


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: int,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除公告（仅管理员）"""
    service = AnnouncementService(db)
    try:
        await service.delete(announcement_id=announcement_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"code": 0, "msg": "公告删除成功", "data": None}
