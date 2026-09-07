"""
端到端测试共享 fixtures
--------------------------------------------------------------------------
复用集成测试的数据库和客户端配置，提供完整业务流程的测试基础
（认证类旅程已迁 auth 服务仓库）
"""
# 复用集成测试的 fixtures
from tests.integration.backend.conftest import (  # noqa: F401
    auth_client,
    auth_token,
    client,
    db_session,
    test_user,
)
