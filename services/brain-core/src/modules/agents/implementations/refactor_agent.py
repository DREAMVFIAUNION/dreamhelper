"""RefactorAgent — 重构清理专家"""

import json
from typing import Any
from ..base.base_agent import BaseAgent
from ..base.types import AgentStep, AgentStepType, AgentContext
from ...llm.llm_client import get_llm_client
from ...llm.types import LLMRequest
from ...tools.tool_registry import ToolRegistry

REFACTOR_PROMPT = """你是梦帮小助的「重构专家」, 擅长识别代码坏味道并提供安全重构方案。

## 重构范围
- 死代码清理 (未引用的函数/变量/import)
- 重复代码提取 (DRY 原则)
- 复杂度降低 (拆分大函数, 简化条件)
- 命名优化 (语义化命名)
- 抽象改进 (接口/协议/基类)
- 依赖倒置 (解耦具体实现)

## 安全守则
- 每次只做一种类型的重构
- 重构前确认有测试覆盖
- 保持向后兼容 (除非明确要求 breaking change)

## 可用工具
{tools_description}

## 输出
{{"thought": "重构分析", "action": "工具名", "action_input": {{...}}}}
或: {{"thought": "...", "final_answer": "重构方案 + diff 示例"}}"""


class RefactorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="refactor_agent", description="重构清理专家，识别坏味道并提供安全重构方案")

    async def think(self, user_input: str, context: AgentContext) -> AgentStep:
        tools = await ToolRegistry.get_dynamic_tool_schemas(query="refactor code grep file edit")
        tools_desc = "\n".join(f"- **{t['name']}**: {t['description']}" for t in tools) if tools else "（无）"
        system = REFACTOR_PROMPT.format(tools_description=tools_desc)
        messages = [{"role": "system", "content": system}] + list(context.history) + [{"role": "user", "content": user_input}]
        client = get_llm_client()
        response = await client.complete(LLMRequest(messages=messages, temperature=0.4, max_tokens=4096, stream=False))
        raw = response.content.strip()
        try:
            parsed = json.loads(raw) if raw.startswith("{") else json.loads(raw[raw.index("{"):raw.rindex("}")+1])
        except (json.JSONDecodeError, ValueError):
            return AgentStep(type=AgentStepType.FINAL_ANSWER, content=raw, is_final=True, final_answer=raw)
        if "final_answer" in parsed:
            return AgentStep(type=AgentStepType.FINAL_ANSWER, content=parsed.get("thought",""), is_final=True, final_answer=parsed["final_answer"])
        if parsed.get("action"):
            return AgentStep(type=AgentStepType.TOOL_CALL, content=parsed.get("thought",""), tool_name=parsed["action"], tool_input=parsed.get("action_input",{}))
        return AgentStep(type=AgentStepType.FINAL_ANSWER, content=raw, is_final=True, final_answer=raw)

    async def act(self, tool_name: str, tool_input: dict[str, Any], context: AgentContext) -> AgentStep:
        try:
            result = await ToolRegistry.execute(tool_name, **tool_input)
            return AgentStep(type=AgentStepType.OBSERVATION, content=result, tool_name=tool_name, tool_output=result)
        except Exception as e:
            return AgentStep(type=AgentStepType.ERROR, content=f"工具 {tool_name} 执行失败: {e}", tool_name=tool_name)

    async def synthesize(self, user_input: str, context: AgentContext) -> AgentStep:
        messages = [{"role": "system", "content": "综合分析, 给出完整重构方案。"}] + list(context.history)
        client = get_llm_client()
        response = await client.complete(LLMRequest(messages=messages, temperature=0.4, max_tokens=4096, stream=False))
        return AgentStep(type=AgentStepType.FINAL_ANSWER, content=response.content, is_final=True, final_answer=response.content)
