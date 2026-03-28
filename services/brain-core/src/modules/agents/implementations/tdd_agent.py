"""TDDAgent — 测试驱动开发专家

实现 RED → GREEN → REFACTOR 循环：
1. 先写失败的测试用例
2. 编写最少代码让测试通过
3. 重构代码保持测试绿色
"""

import json
from typing import Any

from ..base.base_agent import BaseAgent
from ..base.types import AgentStep, AgentStepType, AgentContext
from ...llm.llm_client import get_llm_client
from ...llm.types import LLMRequest
from ...tools.tool_registry import ToolRegistry


TDD_SYSTEM_PROMPT = """你是梦帮小助的「TDD 测试驱动开发专家」。你严格遵循 TDD 方法论：

## TDD 循环 (RED → GREEN → REFACTOR)
1. **RED**: 先编写一个会失败的测试用例, 明确定义期望行为
2. **GREEN**: 编写最少量的代码让测试通过
3. **REFACTOR**: 在测试保持绿色的前提下重构代码

## 可用工具
{tools_description}

## 工作流程
- 分析需求 → 定义接口 → 编写测试 → 实现代码 → 运行测试 → 重构
- 目标: 80%+ 测试覆盖率
- 每次只做一个小步, 确保每步都有测试保障

## 输出格式
{{"thought": "TDD 阶段分析", "action": "工具名", "action_input": {{...}}}}
或: {{"thought": "...", "final_answer": "给用户的完整 TDD 方案"}}"""


class TDDAgent(BaseAgent):
    """TDD Agent — 测试驱动开发循环"""

    def __init__(self):
        super().__init__(
            name="tdd_agent",
            description="测试驱动开发专家，遵循 RED→GREEN→REFACTOR 循环"
        )

    async def think(self, user_input: str, context: AgentContext) -> AgentStep:
        tools = await ToolRegistry.get_dynamic_tool_schemas(query=user_input)
        tools_desc = "\n".join(f"- **{t['name']}**: {t['description']}" for t in tools) if tools else "（无可用工具）"
        system = TDD_SYSTEM_PROMPT.format(tools_description=tools_desc)

        messages = [{"role": "system", "content": system}]
        for msg in context.history:
            messages.append(msg)
        messages.append({"role": "user", "content": user_input})

        client = get_llm_client()
        request = LLMRequest(messages=messages, temperature=0.5, max_tokens=4096, stream=False)
        response = await client.complete(request)
        raw = response.content.strip()

        try:
            parsed = json.loads(raw) if raw.startswith("{") else json.loads(raw[raw.index("{"):raw.rindex("}")+1])
        except (json.JSONDecodeError, ValueError):
            return AgentStep(type=AgentStepType.FINAL_ANSWER, content=raw, is_final=True, final_answer=raw)

        if "final_answer" in parsed:
            return AgentStep(type=AgentStepType.FINAL_ANSWER, content=parsed.get("thought", ""), is_final=True, final_answer=parsed["final_answer"])
        action = parsed.get("action", "")
        if action:
            return AgentStep(type=AgentStepType.TOOL_CALL, content=parsed.get("thought", ""), tool_name=action, tool_input=parsed.get("action_input", {}))
        return AgentStep(type=AgentStepType.FINAL_ANSWER, content=raw, is_final=True, final_answer=raw)

    async def act(self, tool_name: str, tool_input: dict[str, Any], context: AgentContext) -> AgentStep:
        try:
            result = await ToolRegistry.execute(tool_name, **tool_input)
            return AgentStep(type=AgentStepType.OBSERVATION, content=result, tool_name=tool_name, tool_output=result)
        except Exception as e:
            return AgentStep(type=AgentStepType.ERROR, content=f"工具 {tool_name} 执行失败: {e}", tool_name=tool_name)

    async def synthesize(self, user_input: str, context: AgentContext) -> AgentStep:
        messages = [{"role": "system", "content": "你是 TDD 专家。综合以上步骤, 给出完整的 TDD 实施方案。"}]
        for msg in context.history:
            messages.append(msg)
        messages.append({"role": "user", "content": "请总结 TDD 循环结果, 包括覆盖率和下一步建议。"})
        client = get_llm_client()
        request = LLMRequest(messages=messages, temperature=0.5, max_tokens=4096, stream=False)
        response = await client.complete(request)
        return AgentStep(type=AgentStepType.FINAL_ANSWER, content=response.content, is_final=True, final_answer=response.content)
