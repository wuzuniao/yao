from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.config import settings
from .core.http import close_http_client
from .api import v1
from .services.scheduler_service import SchedulerService
from .utils.logger import logger

# 全局定时任务调度服务实例
_scheduler = SchedulerService()


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover
    # 启动全部后台定时任务循环（账号删除上报/计划关闭/通知派发）
    await _scheduler.start_all()
    yield
    # 应用关闭时停止全部后台任务（先停任务再关共享 HTTP 客户端，避免在途外呼用到已关闭连接）
    await _scheduler.stop_all()
    await close_http_client()


# 文档端点应用层关闭：生产由 nginx 404 拦截，此处纵深防御——容器内网与
# 误暴露端口场景下接口文档同样不可达（2026-10-25 安全加固）
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

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


# ===== 全局异常处理器：所有错误统一返回 {"code", "msg", "data"}（code 取 HTTP 状态码，非 0 即错误） =====


def _error_response(status_code: int, msg: str, headers: dict[str, str] | None = None) -> JSONResponse:
    """构造统一错误响应体"""
    return JSONResponse(
        status_code=status_code,
        content={"code": status_code, "msg": msg, "data": None},
        headers=headers,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """业务/框架异常（HTTPException）→ 统一格式，保留原状态码与响应头（如 401 的 WWW-Authenticate）"""
    msg = exc.detail if isinstance(exc.detail, str) and exc.detail else "请求处理失败"
    return _error_response(exc.status_code, msg, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求参数校验失败（Pydantic）→ 422 统一格式，msg 拼接全部校验错误文案"""
    msgs: list[str] = []
    for err in exc.errors():
        m = str(err.get("msg") or "")
        # 去掉 Pydantic v2 包装自定义 ValueError 的英文前缀，保留 Schema 内的中文校验文案
        if m.startswith("Value error, "):
            m = m[len("Value error, "):]
        if m:
            msgs.append(m)
    msg = "；".join(dict.fromkeys(msgs)) or "请求参数校验失败"
    return _error_response(422, msg)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """未处理异常兜底 → 500 统一格式（msg 不泄露内部细节，堆栈仅写日志）"""
    logger.exception("未处理异常 %s %s", request.method, request.url.path)
    return _error_response(500, "服务器内部错误，请稍后重试")


@app.get("/")
async def root():
    return {"message": "Welcome to My Project API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
