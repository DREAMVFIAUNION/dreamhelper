"""BrowserAgent 测试"""

import pytest
from src.modules.agents.implementations.browser_agent import BrowserAgent, HAS_PLAYWRIGHT
from src.modules.agents.agent_router import route_by_keywords, list_agents


def test_browser_agent_init():
    agent = BrowserAgent()
    assert agent.name == "browser_agent"
    assert "浏览器" in agent.description


def test_browser_agent_in_agent_list():
    agents = list_agents()
    names = [a["name"] for a in agents]
    assert "browser_agent" in names


def test_agent_count_with_browser():
    agents = list_agents()
    assert len(agents) == 6  # react, code, writing, analysis, plan_execute, browser


def test_route_keywords_browser():
    assert route_by_keywords("帮我截图这个网页") == "browser_agent"
    assert route_by_keywords("打开网页 https://example.com") == "browser_agent"
    assert route_by_keywords("抓取网页内容") == "browser_agent"
    assert route_by_keywords("提取网页文本") == "browser_agent"


def test_route_keywords_not_browser():
    # 普通对话不应该路由到 browser
    assert route_by_keywords("你好") is None
    assert route_by_keywords("写一段Python代码") == "code_agent"


def test_has_playwright_flag():
    # HAS_PLAYWRIGHT 应该是布尔值
    assert isinstance(HAS_PLAYWRIGHT, bool)
