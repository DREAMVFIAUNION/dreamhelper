"""PlanExecuteAgent 测试"""

import pytest
from src.modules.agents.implementations.plan_execute_agent import PlanExecuteAgent
from src.modules.agents.agent_router import route_by_keywords, list_agents


def test_plan_execute_agent_init():
    agent = PlanExecuteAgent()
    assert agent.name == "plan_execute_agent"
    assert "规划" in agent.description


def test_plan_execute_agent_parse_plan_valid():
    agent = PlanExecuteAgent()
    response = '''这是计划:
```json
[
  {"step": 1, "action": "搜索信息", "tool": "search", "tool_input": {"query": "test"}},
  {"step": 2, "action": "综合回答", "tool": null, "tool_input": null}
]
```'''
    plan = agent._parse_plan(response)
    assert len(plan) == 2
    assert plan[0]["step"] == 1
    assert plan[0]["tool"] == "search"
    assert plan[1]["tool"] is None


def test_plan_execute_agent_parse_plan_invalid():
    agent = PlanExecuteAgent()
    plan = agent._parse_plan("这不是JSON格式")
    assert plan == []


def test_plan_execute_agent_parse_plan_empty_array():
    agent = PlanExecuteAgent()
    plan = agent._parse_plan("[]")
    assert plan == []


def test_plan_execute_agent_parse_tool_call_valid():
    agent = PlanExecuteAgent()
    response = '我需要调用工具: {"tool": "calculator", "input": {"expression": "2+3"}}'
    result = agent._parse_tool_call(response)
    assert result is not None
    assert result["tool"] == "calculator"
    assert result["input"]["expression"] == "2+3"


def test_plan_execute_agent_parse_tool_call_none():
    agent = PlanExecuteAgent()
    result = agent._parse_tool_call("这不需要工具，直接回答")
    assert result is None


def test_plan_execute_agent_parse_tool_call_invalid_json():
    agent = PlanExecuteAgent()
    result = agent._parse_tool_call('{"broken json')
    assert result is None


# ── Router Integration ──

def test_route_keywords_plan_execute():
    assert route_by_keywords("帮我制定计划") == "plan_execute_agent"
    assert route_by_keywords("请帮我规划一下") == "plan_execute_agent"
    assert route_by_keywords("分步执行这个任务") == "plan_execute_agent"


def test_plan_execute_in_agent_list():
    agents = list_agents()
    names = [a["name"] for a in agents]
    assert "plan_execute_agent" in names


def test_agent_count():
    agents = list_agents()
    assert len(agents) == 6  # react, code, writing, analysis, plan_execute, browser
