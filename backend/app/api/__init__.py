from fastapi import APIRouter
from .v1 import router as v1_router

router = APIRouter()
# main.py 已通过 API_V1_STR 添加 /api/v1 前缀，此处不再重复添加 /v1
router.include_router(v1_router, tags=["v1"])
