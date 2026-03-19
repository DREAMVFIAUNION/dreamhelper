"""pytest 全局配置 — brain-core 冒烟测试基础设施"""

import os
import sys
import pytest

# 确保 src 在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def sample_context():
    from src.modules.agents.base.types import AgentContext
    return AgentContext(
        session_id="test-session",
        user_id="test-user",
        agent_id="test-agent",
    )


@pytest.fixture
def anyio_backend():
    return "asyncio"
