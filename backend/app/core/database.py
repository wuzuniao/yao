from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# connect_args：每个连接建立时执行 SET time_zone='+08:00'，确保 CURRENT_TIMESTAMP 等函数返回上海时间
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"init_command": "SET time_zone='+08:00'"},
    # 连接池稳定性配置：pre_ping 借出前探活防止拿到已被 MariaDB 关闭的失效连接
    # （对应 MariaDB 日志中的 Aborted connection）；recycle 主动回收长连接。
    # recycle 取 1800：pre_ping 已兜底连接失效探活，过短的回收周期只会徒增
    # 重建连接（TCP+握手+时区初始化）的开销，30 分钟回收足以覆盖中间设备/NAT 的空闲超时
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
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
