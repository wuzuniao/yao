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
    # 启动全部后台定时任务循环（账号删除上报/计划关闭/通知派发）
    await _scheduler.start_all()
    yield
    # 应用关闭时停止全部后台任务
    await _scheduler.stop_all()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # 本地开发源放行（任意 localhost/127.0.0.1 端口）：H5 开发服务器端口不固定
    # （HBuilderX 默认 8080、Vite 5173 等），逐一登记易漏；生产页面源均为域名不受影响
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(v1.router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to My Project API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
