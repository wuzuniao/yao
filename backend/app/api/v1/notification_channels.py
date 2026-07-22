from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.deps import get_current_user_id
from ...schemas.notification_channel import (
    CHANNEL_TYPE_EMAIL,
    CHANNEL_TYPE_WECHAT,
    CreateEmailChannel,
    DeleteChannel,
    UpdateEmailChannel,
)
from ...services.notification_channel_service import NotificationChannelService

router = APIRouter()


def _channel_to_dict(channel) -> dict:
    """将 NotificationChannel 对象转换为响应字典（邮件渠道解析 JSON，密码字段返回空值）"""
    item = {
        "id": channel.id,
        "user_id": channel.user_id,
        "channel_type": channel.channel_type,
        "channel_value": channel.channel_value,
        "enabled": bool(channel.enabled),
        "created_at": channel.created_at.isoformat() if channel.created_at else None,
        "updated_at": channel.updated_at.isoformat() if channel.updated_at else None,
    }
    # 邮件类型解析 JSON 配置，前端直接使用
    # 注意：password 字段始终返回空字符串，不暴露解密内容，仅允许用户重新输入
    if channel.channel_type == CHANNEL_TYPE_EMAIL:
        cfg = NotificationChannelService.parse_email_channel_value(channel.channel_value)
        if cfg:
            cfg["password"] = ""
            item["email_config"] = cfg
    elif channel.channel_type == CHANNEL_TYPE_WECHAT:
        # 返回授权额度信息，前端据此展示「剩余可下发次数」与授权状态
        quota = NotificationChannelService.parse_wechat_channel_value(channel.channel_value)
        item["wechat_quota"] = quota
        item["remaining"] = quota["granted"] - quota["sent"]
    return item


@router.get("/list")
async def list_channels(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """查询当前登录用户的所有通知渠道（user_id 来自 JWT）"""
    service = NotificationChannelService(db)
    channels = await service.list_by_user(user_id)
    return {
        "code": 0,
        "msg": "success",
        "data": [_channel_to_dict(ch) for ch in channels],
    }


@router.post("/email")
async def create_email_channel(
    payload: CreateEmailChannel,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建邮件通知渠道（user_id 来自 JWT，站内信在用户注册时自动创建，不允许用户主动添加）"""
    service = NotificationChannelService(db)
    try:
        channel = await service.create_email_channel(
            user_id=user_id,
            smtp_host=payload.smtp_host,
            smtp_port=payload.smtp_port,
            email=payload.email,
            password=payload.password,
            enabled=payload.enabled,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "邮件通知方式添加成功",
        "data": _channel_to_dict(channel),
    }


@router.put("/email")
async def update_email_channel(
    payload: UpdateEmailChannel,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新邮件通知渠道配置（user_id 来自 JWT）"""
    service = NotificationChannelService(db)
    try:
        channel = await service.update_email_channel(
            channel_id=payload.channel_id,
            user_id=user_id,
            smtp_host=payload.smtp_host,
            smtp_port=payload.smtp_port,
            email=payload.email,
            password=payload.password,
            enabled=payload.enabled,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "code": 0,
        "msg": "邮件通知方式更新成功",
        "data": _channel_to_dict(channel),
    }


@router.delete("")
async def delete_channel(
    payload: DeleteChannel,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除通知渠道（user_id 来自 JWT，站内信不允许删除）"""
    service = NotificationChannelService(db)
    try:
        await service.delete_channel(channel_id=payload.channel_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"code": 0, "msg": "通知方式删除成功", "data": None}


@router.post("/wechat/grant")
async def grant_wechat_channel(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    微信订阅消息授权回调：用户在小程序内每同意一次授权（wx.requestSubscribeMessage 返回 accept）
    即 +1 下发额度，并启用微信渠道。返回 {enabled, granted, sent, remaining} 供前端展示。
    """
    service = NotificationChannelService(db)
    info = await service.grant_wechat(user_id)
    return {"code": 0, "msg": "微信订阅授权成功", "data": info}
