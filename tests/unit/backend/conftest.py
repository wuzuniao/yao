"""
单元测试共享 fixtures
--------------------------------------------------------------------------
- mock_db: 模拟 AsyncSession，不连接真实数据库
- mock_email: 模拟 Email 服务，不发送真实邮件
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_db():
    """模拟异步数据库会话"""
    db = AsyncMock()
    # scalar_one_or_none 默认返回 None（表示未找到）
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.execute.return_value.scalars.return_value.all.return_value = []
    return db


@pytest.fixture
def mock_email():
    """模拟 Email 服务，避免发送真实邮件"""
    with patch("app.services.user_service.Email") as mock:
        instance = mock.return_value
        instance.send_verification_code = MagicMock(return_value=None)
        yield mock
