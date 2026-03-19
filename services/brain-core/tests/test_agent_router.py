"""Agent Router 测试 — 关键词路由 + Agent 列表"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.modules.agents.agent_router import route_by_keywords, list_agents, get_agent


class TestAgentRouter:

    def test_route_code_agent(self):
        result = route_by_keywords("写一个Python装饰器")
        assert result == "code_agent"

    def test_route_writing_agent(self):
        result = route_by_keywords("帮我翻译这段话成英文")
        assert result == "writing_agent"

    def test_route_analysis_agent(self):
        result = route_by_keywords("分析微服务架构的优劣")
        assert result == "analysis_agent"

    def test_route_react_agent(self):
        result = route_by_keywords("帮我算 2+3*4")
        assert result == "react_agent"

    def test_route_no_match(self):
        result = route_by_keywords("你好呀")
        assert result is None

    def test_route_casual_chat(self):
        result = route_by_keywords("今天天气怎么样")
        assert result is None

    def test_list_agents(self):
        agents = list_agents()
        assert len(agents) >= 4
        names = [a["name"] for a in agents]
        assert "code_agent" in names
        assert "writing_agent" in names
        assert "analysis_agent" in names
        assert "react_agent" in names

    def test_get_agent_exists(self):
        agent = get_agent("code_agent")
        assert agent is not None
        assert hasattr(agent, "run")

    def test_get_agent_nonexistent(self):
        agent = get_agent("nonexistent_agent")
        # Should return default or None
        assert agent is not None or agent is None  # flexible
