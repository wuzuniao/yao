"""
测试根配置文件
--------------------------------------------------------------------------
- 将 backend/ 目录加入 Python 路径，使测试可导入 app 模块
- 设置测试环境变量（在 app 模块导入前生效，覆盖 .env 配置）
- 提供跨测试类型的共享 fixture
"""
import base64
import os
import sys
from pathlib import Path

# === 1. 将 backend/ 目录加入 Python 路径 ===
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent / "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# === 2. 设置测试环境变量（必须在导入 app 之前生效）===
# 测试数据库（独立于开发库，避免数据污染）
os.environ.setdefault(
    "DATABASE_URL",
    "mysql+asyncmy://root:root@127.0.0.1:3306/wuzuniao_yao_test?charset=utf8mb4",
)
# 测试用 JWT 密钥（仅测试环境使用）
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-testing-only")
# 测试用 AES-256 加密密钥（base64 编码的 32 字节）
os.environ.setdefault(
    "ENCRYPTION_SECRET_KEY",
    base64.b64encode(b"0" * 32).decode(),
)
# 禁用 SMTP 和微信小程序配置（测试中 mock 这些外部服务）
os.environ.setdefault("SMTP_HOST", "smtp.test.com")
os.environ.setdefault("SMTP_PORT", "465")
os.environ.setdefault("SMTP_USER", "test@test.com")
os.environ.setdefault("SMTP_PASSWORD", "test-password")
