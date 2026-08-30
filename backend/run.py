"""后端启动脚本：兼容从任意工作目录运行（IDE 可能以项目根目录为 CWD 启动本文件）。"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)  # uvicorn 的 "app.main:app" 导入字符串依赖 CWD 为 backend 目录

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
