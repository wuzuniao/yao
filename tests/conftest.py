"""
测试根配置文件
--------------------------------------------------------------------------
- 将 backend/ 目录与项目根目录加入 Python 路径，使测试可导入 app 与 tests.* 模块
- 设置测试环境变量（在 app 模块导入前生效，覆盖 .env 配置）
- 生成测试专用 RSA 密钥并注入 auth_client 内存缓存（RS256 本地验签不依赖 auth 服务）
- 提供跨测试类型的共享 fixture
"""
import base64
import os
import sys
from pathlib import Path

import pytest

# === 1. 将 backend/ 与项目根目录加入 Python 路径 ===
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent / "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)
_ROOT_DIR = str(Path(__file__).resolve().parent.parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

# === 2. 设置测试环境变量（必须在导入 app 之前生效）===
# 测试业务数据库（独立于开发库，避免数据污染；用户库已归 auth 服务，不再涉及）
os.environ.setdefault(
    "DATABASE_URL",
    "mysql+asyncmy://root:root@127.0.0.1:3306/wuzuniao_yao_test?charset=utf8mb4",
)
# auth 服务测试配置：
# - AUTH_BASE_URL 指向不可达地址：测试不真实调用 auth（email/openid/撤销/删除上报/合并确认均 mock 或不触发）
# - AUTH_ISSUER 与 tests/rsa_keys.py 的 TEST_ISSUER 一致（RS256 验签 issuer 校验）
# - AUTH_SERVICE_TOKEN 用于服务间调用头；AUTH_CLIENT_ID 用于删除上报体
os.environ.setdefault("AUTH_BASE_URL", "http://127.0.0.1:9")
os.environ.setdefault("AUTH_ISSUER", "http://test-auth")
os.environ.setdefault("AUTH_SERVICE_TOKEN", "test-service-token")
os.environ.setdefault("AUTH_CLIENT_ID", "yao")
# 测试用 AES-256 加密密钥（base64 编码的 32 字节）
os.environ.setdefault(
    "ENCRYPTION_SECRET_KEY",
    base64.b64encode(b"0" * 32).decode(),
)

# === 3. 注入测试 JWKS（在任何 app 模块验签前完成）===
# auth_client._jwks_keys 为进程内存缓存；注入测试公钥后 get_public_key(kid) 直接命中，
# verify_access_token 全程零网络调用（未知 kid 的重拉会因 AUTH_BASE_URL 不可达而失败回退）
from app.core import auth_client as _auth_client  # noqa: E402
from tests import rsa_keys as _rsa_keys  # noqa: E402


def _inject_test_jwks() -> None:
    """将测试公钥注入 auth_client 内存缓存"""
    _auth_client._jwks_keys[_rsa_keys.KID] = _rsa_keys.PUBLIC_KEY_OBJ


_inject_test_jwks()


# === 4. 跨测试类型的共享 fixture ===


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """每个测试前清空限流器状态，确保测试间互不影响（限流器为进程内字典，默认跨测试共享）"""
    from app.core.rate_limit import _rate_store
    _rate_store.clear()


@pytest.fixture(autouse=True)
def reset_auth_client_state():
    """
    每个测试前重置 auth_client 进程内状态（撤销缓存/水位/信息缓存），
    并重新注入测试 JWKS（reset_for_tests 会清空密钥缓存）
    """
    _auth_client.reset_for_tests()
    _inject_test_jwks()
    yield
