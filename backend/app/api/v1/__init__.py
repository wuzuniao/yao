from fastapi import APIRouter

from .notification_channels import router as notification_channels_router
from .plans import router as plans_router
from .checkins import router as checkins_router
from .notification_logs import router as notification_logs_router

router = APIRouter()
router.include_router(notification_channels_router, prefix="/notification-channels", tags=["通知渠道"])
router.include_router(plans_router, prefix="/plans", tags=["计划"])
router.include_router(checkins_router, prefix="/checkins", tags=["打卡记录"])
router.include_router(notification_logs_router, prefix="/notification-logs", tags=["站内信"])
# 公告接口已随「公告管理迁移 auth」（2026-10-02）下线：公告内容与已读状态
# 收口 auth 库，前端直连 auth /api/v1/announcements/* 查询，本服务不再承载
