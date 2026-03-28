"""DocAgent — 文档生成与同步专家"""

import json
from typing import Any
from ..base.base_agent import BaseAgent
from ..base.types import AgentStep, AgentStepType, AgentContext
from ...llm.llm_client import get_llm_client
from ...llm.types import LLMRequest
from ...tools.tool_registry import ToolRegistry

DOC_PROMPT = """你是梦帮小助的「文档专家」, 擅长生成清晰、专业、有温度的技术文档。

## 文档类型
1. **API 文档**: 端点、参数、响应、示例
2. **README**: 项目概述、快速开始、安装指南
3. **变更日志**: 版本号、改动摘要、破坏性变更
4. **架构文档**: 组件关系、数据流、部署图
5. **用户指南**: 功能说明、最佳实践、FAQ

## 写作风格
- 技术准确但不晦涩
- 善用代码示例和图表
- 包含「为什么」而不只是「怎么做」
- 适当使用 emoji 让文档更友好

## 可用工具
{tools_description}

## 输出
{{"thought": "文档分析", "action": "工具名", "action_input": {{...}}}}
或: {{"thought": "...", "final_answer": "完整文档内容"}}"""


class DocAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="doc_agent", description="文档生成与同步专家，生成清晰专业有温度的技术文档")

    async def think(self, user_input: str, context: AgentContext) -> AgentStep:
        tools = await ToolRegistry.get_dynamic_tool_schemas(query="documentation file read write")
        tools_desc = "\n".join(f"- **{t['name']}**: {t['description']}" for t in tools) if tools else "（无）"
        system = DOC_PROMPT.format(tools_description=tools_desc)
        messages = [{"role": "system", "content": system}] + list(context.history) + [{"role": "user", "content": user_input}]
        client = get_llm_client()
        response = await client.complete(LLMRequest(messages=messages, temperature=0.7, max_tokens=4096, stream=False))
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
        messages = [{"role": "system", "content": "综合信息, 生成完整文档。"}] + list(context.history)
        client = get_llm_client()
        response = await client.complete(LLMRequest(messages=messages, temperature=0.7, max_tokens=4096, stream=False))
        return AgentStep(type=AgentStepType.FINAL_ANSWER, content=response.content, is_final=True, final_answer=response.content)
