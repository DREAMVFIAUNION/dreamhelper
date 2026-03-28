"""CodeReviewAgent — 代码审查专家

提供多维度代码审查：
- 代码质量（可读性/复杂度/命名）
- 安全漏洞（注入/XSS/硬编码密钥）
- 性能问题（N+1查询/内存泄漏）
- 可维护性（SOLID/DRY/耦合度）
"""

import json
from typing import Any

from ..base.base_agent import BaseAgent
from ..base.types import AgentStep, AgentStepType, AgentContext
from ...llm.llm_client import get_llm_client
from ...llm.types import LLMRequest
from ...tools.tool_registry import ToolRegistry


REVIEW_SYSTEM_PROMPT = """你是梦帮小助的「代码审查专家」。你以资深工程师的视角审查代码。

## 审查维度 (每项 1-5 分)
1. **正确性**: 逻辑是否正确, 边界情况是否覆盖
2. **安全性**: OWASP Top 10, 硬编码密钥, SQL 注入, XSS
3. **性能**: N+1 查询, 内存泄漏, 不必要的计算
4. **可读性**: 命名规范, 注释质量, 代码组织
5. **可维护性**: SOLID 原则, DRY, 耦合度, 测试覆盖

## 可用工具
{tools_description}

## 审查输出格式
最终回答时请使用以下结构:
- 📊 总体评分: X/5
- ✅ 优点: ...
- ⚠️ 问题: ... (按严重程度排序)
- 🔧 改进建议: ...
- 📝 代码示例: (具体修改建议)

## JSON 输出
{{"thought": "审查分析", "action": "工具名", "action_input": {{...}}}}
或: {{"thought": "...", "final_answer": "完整审查报告"}}"""


class CodeReviewAgent(BaseAgent):
    """Code Review Agent — 多维度代码审查"""

    def __init__(self):
        super().__init__(
            name="code_review_agent",
            description="代码审查专家，审查质量、安全、性能与可维护性"
        )

    async def think(self, user_input: str, context: AgentContext) -> AgentStep:
        tools = await ToolRegistry.get_dynamic_tool_schemas(query="code review grep file read")
        tools_desc = "\n".join(f"- **{t['name']}**: {t['description']}" for t in tools) if tools else "（无可用工具）"
        system = REVIEW_SYSTEM_PROMPT.format(tools_description=tools_desc)

        messages = [{"role": "system", "content": system}]
        for msg in context.history:
            messages.append(msg)
        messages.append({"role": "user", "content": user_input})

        client = get_llm_client()
        request = LLMRequest(messages=messages, temperature=0.3, max_tokens=4096, stream=False)
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
        messages = [{"role": "system", "content": "你是代码审查专家。请综合以上分析, 给出完整审查报告。"}]
        for msg in context.history:
            messages.append(msg)
        messages.append({"role": "user", "content": "请给出最终的代码审查报告, 包含评分、问题列表和改进建议。"})
        client = get_llm_client()
        request = LLMRequest(messages=messages, temperature=0.3, max_tokens=4096, stream=False)
        response = await client.complete(request)
        return AgentStep(type=AgentStepType.FINAL_ANSWER, content=response.content, is_final=True, final_answer=response.content)
