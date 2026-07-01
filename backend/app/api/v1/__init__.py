from fastapi import APIRouter

from .users import router as users_router
from .notification_channels import router as notification_channels_router
from .plans import router as plans_router
from .checkins import router as checkins_router
from .notification_logs import router as notification_logs_router

router = APIRouter()
router.include_router(users_router, prefix="/users", tags=["用户"])
router.include_router(notification_channels_router, prefix="/notification-channels", tags=["通知渠道"])
router.include_router(plans_router, prefix="/plans", tags=["计划"])
router.include_router(checkins_router, prefix="/checkins", tags=["打卡记录"])
router.include_router(notification_logs_router, prefix="/notification-logs", tags=["站内信"])
