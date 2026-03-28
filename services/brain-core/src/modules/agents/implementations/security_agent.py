"""SecurityAgent — 安全审计专家

提供 OWASP Top 10 审计、依赖漏洞扫描、配置安全检查。
"""

import json
from typing import Any
from ..base.base_agent import BaseAgent
from ..base.types import AgentStep, AgentStepType, AgentContext
from ...llm.llm_client import get_llm_client
from ...llm.types import LLMRequest
from ...tools.tool_registry import ToolRegistry

SECURITY_SYSTEM_PROMPT = """你是梦帮小助的「安全审计专家」, 专精于应用安全分析。

## 审计清单 (OWASP Top 10 + 常见风险)
1. A01: 访问控制失效 — 越权访问、IDOR
2. A02: 加密失败 — 弱加密、明文传输、硬编码密钥
3. A03: 注入 — SQL/NoSQL/OS/LDAP 注入
4. A04: 不安全设计 — 业务逻辑缺陷
5. A05: 安全配置错误 — 默认凭证、调试模式暴露
6. A06: 脆弱组件 — 已知漏洞依赖
7. A07: 身份认证失败 — 弱密码策略、会话管理
8. A08: 数据完整性失败 — 反序列化、供应链
9. A09: 安全日志不足 — 缺乏审计追踪
10. A10: SSRF — 服务端请求伪造

## 可用工具
{tools_description}

## 输出
{{"thought": "安全分析", "action": "工具名", "action_input": {{...}}}}
或: {{"thought": "...", "final_answer": "安全审计报告（按风险等级排序: 🔴Critical → 🟠High → 🟡Medium → 🟢Low）"}}"""


class SecurityAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="security_agent", description="安全审计专家，OWASP Top 10 + 依赖漏洞扫描")

    async def think(self, user_input: str, context: AgentContext) -> AgentStep:
        tools = await ToolRegistry.get_dynamic_tool_schemas(query="security scan grep file")
        tools_desc = "\n".join(f"- **{t['name']}**: {t['description']}" for t in tools) if tools else "（无可用工具）"
        system = SECURITY_SYSTEM_PROMPT.format(tools_description=tools_desc)
        messages = [{"role": "system", "content": system}] + list(context.history) + [{"role": "user", "content": user_input}]
        client = get_llm_client()
        response = await client.complete(LLMRequest(messages=messages, temperature=0.2, max_tokens=4096, stream=False))
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
        messages = [{"role": "system", "content": "你是安全专家。综合分析, 给出安全审计报告。"}] + list(context.history)
        messages.append({"role": "user", "content": "请给出完整安全审计报告, 按风险等级排序。"})
        client = get_llm_client()
        response = await client.complete(LLMRequest(messages=messages, temperature=0.2, max_tokens=4096, stream=False))
        return AgentStep(type=AgentStepType.FINAL_ANSWER, content=response.content, is_final=True, final_answer=response.content)
