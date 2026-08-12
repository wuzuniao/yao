from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.deps import get_current_admin, get_current_user_id
from ...core.rate_limit import limit_authenticated
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


@router.get("", dependencies=[Depends(limit_authenticated)])
async def list_announcements(
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """查询全部公告（仅管理员）；排除 id=1 的公共模板"""
    service = AnnouncementService(db)
    announcements = await service.list_all()
    return {
        "code": 0,
        "msg": "success",
        "data": [_announcement_to_dict(a) for a in announcements],
    }


@router.get("/recent", dependencies=[Depends(limit_authenticated)])
async def list_recent_announcements(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """查询最近 7 天内发布的公告（普通用户），按创建时间倒序；排除 id=1 公共模板"""
    service = AnnouncementService(db)
    announcements = await service.list_recent(days=7)
    return {
        "code": 0,
        "msg": "success",
        "data": [_announcement_to_dict(a) for a in announcements],
    }


@router.get("/template", dependencies=[Depends(limit_authenticated)])
async def get_announcement_template(
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """查询公共公告模板（id=1），管理员用于发布表单预填充与模板编辑"""
    service = AnnouncementService(db)
    template = await service.get_template()
    if not template:
        raise HTTPException(status_code=404, detail="公告模板不存在")
    return {
        "code": 0,
        "msg": "success",
        "data": _announcement_to_dict(template),
    }


@router.post("", dependencies=[Depends(limit_authenticated)])
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


@router.put("/{announcement_id}", dependencies=[Depends(limit_authenticated)])
async def update_announcement(
    announcement_id: int = Path(..., gt=0, description="公告ID，必须为正整数"),
    payload: AnnouncementUpdate = Body(...),
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新公告（仅管理员）；更新 id=1 的公共模板时若记录不存在则自动创建"""
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


@router.delete("/{announcement_id}", dependencies=[Depends(limit_authenticated)])
async def delete_announcement(
    announcement_id: int = Path(..., gt=0, description="公告ID，必须为正整数"),
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
