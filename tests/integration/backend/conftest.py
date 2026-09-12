"""
集成测试共享 fixtures
--------------------------------------------------------------------------
- 使用测试业务数据库 wuzuniao_yao_test（可用 TEST_DATABASE_URL 环境变量覆盖连接地址）
- 用户库已归 auth 服务：测试用户不再写用户表，直接分配虚拟 user_id 并以
  测试 RSA 私钥签发 access_token（密钥见 tests/rsa_keys.py，根 conftest 已注入 JWKS）
- 复用 app 自身的 database.py 基础，使用 NullPool 避免跨事件循环连接失效
- 每个测试后自动清理数据（TRUNCATE 所有表）
- 提供已认证的测试客户端
"""
import os
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.models.announcement import Announcement  # noqa: F401
from app.models.checkin_record import CheckinRecord  # noqa: F401
from app.models.merge_task import MergeSyncTask  # noqa: F401
from app.models.notification_channel import NotificationChannel  # noqa: F401
from app.models.notification_log import NotificationLog  # noqa: F401
from app.models.plan import CheckinPlan, PlanNotificationChannel, PlanNotificationTime  # noqa: F401
from tests import rsa_keys

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "mysql+asyncmy://root:root@127.0.0.1:3306/wuzuniao_yao_test?charset=utf8mb4",
)

# 测试专用引擎（NullPool 不缓存连接，避免跨事件循环的连接失效问题）
_test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"init_command": "SET time_zone='+08:00'"},
)

_tables_created = False

# 测试用户虚拟 ID（业务表 user_id 无外键约束，无需真实用户行）
TEST_USER_ID = 10001


async def _ensure_tables():
    """确保所有表已创建（仅执行一次）"""
    global _tables_created
    if not _tables_created:
        async with _test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _tables_created = True


async def _truncate_all():
    """清空所有表数据（每个测试后执行）"""
    async with _test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def db_session():
    """每个测试独立的数据库会话（测试后自动清理数据）"""
    await _ensure_tables()
    async with AsyncSession(_test_engine, expire_on_commit=False) as session:
        yield session
        await session.close()
    await _truncate_all()


@pytest.fixture
async def client(db_session):
    """测试客户端（覆盖 get_db 依赖，使用测试数据库会话）"""
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    """
    测试用户（虚拟对象）+ 站内信通知渠道（业务库行）
    - 用户库已归 auth 服务：不再创建用户表行，业务表仅以 user_id 关联（无外键约束）
    - 令牌由 rsa_keys 以测试私钥签发（auth_token fixture）
    - 站内信渠道在此创建（与拆分前 fixture 行为一致，供既有测试直接查询；
      运行时渠道已由 NotificationChannelService.list_by_user 懒创建）
    """
    from app.services.notification_channel_service import NotificationChannelService

    user = SimpleNamespace(
        id=TEST_USER_ID,
        username="测试用户",
        email="test@example.com",
        status=1,
        role=0,
    )
    await NotificationChannelService(db_session).ensure_znx_channel(user.id)
    return user


@pytest.fixture
def auth_token(test_user):
    """生成测试用户的 RS256 access_token（测试私钥签发，claims 与 auth 服务一致）"""
    return rsa_keys.sign_token(test_user.id, role=test_user.role)


@pytest.fixture
async def auth_client(client, auth_token):
    """带认证头的测试客户端"""
    client.headers["Authorization"] = f"Bearer {auth_token}"
    return client


@pytest.fixture
async def bypass_auth(client):
    """
    绕过认证，直接返回 user_id=999999（不存在的用户）
    - 新版认证依赖不查库（本地 RS256 验签 + 撤销比对），无需绕过 DB 校验；
      本 fixture 保留用于直达 service 层测试"用户不存在/无归属数据"分支
    - 依赖 client fixture（已覆盖 get_db），仅额外覆盖 get_current_user_id
    """
    from app.core.deps import get_current_user_id
    from app.main import app

    app.dependency_overrides[get_current_user_id] = lambda: 999999
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)
