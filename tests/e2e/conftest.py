"""
端到端测试共享 fixtures
--------------------------------------------------------------------------
复用集成测试的数据库和客户端配置，提供完整用户流程的测试基础
"""
# 复用集成测试的 fixtures
from tests.integration.backend.conftest import (  # noqa: F401
    auth_client,
    auth_token,
    client,
    db_session,
    mock_email_service,
    test_user,
)
