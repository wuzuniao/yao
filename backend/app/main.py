from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api import v1
from .services.scheduler_service import SchedulerService

# 全局定时任务调度服务实例
_scheduler = SchedulerService()


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover
    # 启动全部后台定时任务循环（账号清理/计划关闭/通知派发）
    await _scheduler.start_all()
    yield
    # 应用关闭时停止全部后台任务
    await _scheduler.stop_all()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1.router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to My Project API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
