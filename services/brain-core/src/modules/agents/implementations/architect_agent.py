"""ArchitectAgent — 系统架构设计专家

利用双脑融合（左脑逻辑分析 + 右脑创意发散）进行架构决策。
"""

import json
from typing import Any
from ..base.base_agent import BaseAgent
from ..base.types import AgentStep, AgentStepType, AgentContext
from ...llm.llm_client import get_llm_client
from ...llm.types import LLMRequest
from ...tools.tool_registry import ToolRegistry

ARCHITECT_SYSTEM_PROMPT = """你是梦帮小助的「系统架构师」, 擅长从全局视角设计系统架构。

## 架构决策框架
1. **需求分析**: 功能需求 + 非功能需求(性能/可用性/安全/可扩展)
2. **技术选型**: 权衡利弊, 给出推荐方案 + 备选方案
3. **架构图**: 用文字描述组件关系(可使用 Mermaid 语法)
4. **风险评估**: 识别技术风险点和缓解措施
5. **实施路径**: 分阶段实施计划

## 架构原则
- KISS (保持简单)
- YAGNI (不过度设计)
- 关注分离 (Separation of Concerns)
- 12-Factor App 原则
- CAP 定理权衡

## 可用工具
{tools_description}

## 输出
{{"thought": "架构分析", "action": "工具名", "action_input": {{...}}}}
或: {{"thought": "...", "final_answer": "完整架构方案"}}"""


class ArchitectAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="architect_agent", description="系统架构设计专家，提供技术选型、架构图和实施路径")

    async def think(self, user_input: str, context: AgentContext) -> AgentStep:
        tools = await ToolRegistry.get_dynamic_tool_schemas(query="architecture design file read")
        tools_desc = "\n".join(f"- **{t['name']}**: {t['description']}" for t in tools) if tools else "（无可用工具）"
        system = ARCHITECT_SYSTEM_PROMPT.format(tools_description=tools_desc)
        messages = [{"role": "system", "content": system}] + list(context.history) + [{"role": "user", "content": user_input}]
        client = get_llm_client()
        response = await client.complete(LLMRequest(messages=messages, temperature=0.6, max_tokens=4096, stream=False))
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
        messages = [{"role": "system", "content": "你是架构师。给出完整架构方案。"}] + list(context.history)
        messages.append({"role": "user", "content": "请综合给出完整架构设计方案, 包括架构图描述和实施路径。"})
        client = get_llm_client()
        response = await client.complete(LLMRequest(messages=messages, temperature=0.6, max_tokens=4096, stream=False))
        return AgentStep(type=AgentStepType.FINAL_ANSWER, content=response.content, is_final=True, final_answer=response.content)
