"""
单元测试共享 fixtures
--------------------------------------------------------------------------
- mock_db: 模拟 AsyncSession，不连接真实数据库
"""
import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_db():
    """模拟异步数据库会话"""
    db = AsyncMock()
    # scalar_one_or_none 默认返回 None（表示未找到）
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.execute.return_value.scalars.return_value.all.return_value = []
    return db
