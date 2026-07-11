"""
集成测试共享 fixtures
--------------------------------------------------------------------------
- 使用测试数据库 wuzuniao_yao_test（由根 conftest.py 设置 DATABASE_URL 环境变量）
- 复用 app 自身的 database.py 引擎，使用 NullPool 避免跨事件循环连接失效
- 每个测试后自动清理数据（TRUNCATE 所有表）
- 自动 mock Email 服务，避免发送真实邮件
- 提供已认证的测试客户端
"""
from unittest.mock import patch, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.security import Security
from app.models.checkin_record import CheckinRecord  # noqa: F401
from app.models.notification_channel import NotificationChannel
from app.models.notification_log import NotificationLog  # noqa: F401
from app.models.plan import CheckinPlan, PlanNotificationChannel, PlanNotificationTime  # noqa: F401
from app.models.user import User as UserModel
from app.models.user_miniapp_account import UserMiniappAccount  # noqa: F401

TEST_DATABASE_URL = (
    "mysql+asyncmy://root:root@127.0.0.1:3306/wuzuniao_yao_test?charset=utf8mb4"
)

# 测试专用引擎（NullPool 不缓存连接，避免跨事件循环的连接失效问题）
_test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"init_command": "SET time_zone='+08:00'"},
)

_tables_created = False


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


@pytest.fixture(autouse=True)
def mock_email_service():
    """自动 mock Email 服务，避免发送真实邮件"""
    with patch("app.services.user_service.Email") as mock:
        instance = mock.return_value
        instance.send_verification_code = MagicMock(return_value=None)
        yield mock


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
    """创建测试用户并返回用户对象"""
    user = UserModel(
        username="测试用户",
        email="test@example.com",
        password_hash=Security.hash_password("Test1234!"),
        avatar_url="hei",
        signature="测试签名",
        status=1,
    )
    db_session.add(user)
    await db_session.flush()
    # 自动创建站内信通知渠道（与注册流程一致）
    channel = NotificationChannel(
        user_id=user.id,
        channel_type="站内信",
        channel_value=str(user.id),
        enabled=True,
    )
    db_session.add(channel)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """生成测试用户的 JWT token"""
    return Security.generate_token(test_user.id)


@pytest.fixture
async def auth_client(client, auth_token):
    """带认证头的测试客户端"""
    client.headers["Authorization"] = f"Bearer {auth_token}"
    return client
