from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# connect_args：每个连接建立时执行 SET time_zone='+08:00'，确保 CURRENT_TIMESTAMP 等函数返回上海时间
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"init_command": "SET time_zone='+08:00'"},
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():  # pragma: no cover
    # 测试中通过 dependency_overrides 替代，生产环境由 FastAPI 调用
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
