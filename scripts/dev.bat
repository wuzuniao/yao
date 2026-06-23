@echo off
echo 正在启动 FastAPI 后端（Windows 本地模式）...
start cmd /k "cd /d %~dp0..\backend && uvicorn app.main:app --reload --port 8000"
echo 后端已启动在 http://localhost:8000
echo.
echo 前端请在 HBuilder X 中点击运行，或执行 npm run dev:mp-weixin
pause
