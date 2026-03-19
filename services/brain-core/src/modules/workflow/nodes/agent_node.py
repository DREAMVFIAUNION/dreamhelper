"""Agent 节点 — 调用内置 + DB 动态 Agent（Phase 8: 完整闭环）"""

from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class AgentNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="agent",
            name="AI Agent",
            description="调用专业 Agent（内置 + 自定义），支持自动路由或指定 Agent",
            category="ai",
            icon="Bot",
            color="#8B5CF6",
            inputs=["input"],
            outputs=["output"],
            config_schema={
                "agent": {
                    "type": "select", "label": "Agent 类型", "default": "auto",
                    "options": ["auto", "code_agent", "writing_agent", "analysis_agent",
                                "react_agent", "browser_agent", "plan_execute_agent"],
                    "description": "选择 auto 时根据消息内容自动路由；也可输入 DB 中的自定义 Agent 名称",
                },
                "message": {
                    "type": "textarea", "label": "消息",
                    "default": "{{input}}", "placeholder": "使用 {{input}} 引用上游数据",
                },
                "session_id": {"type": "string", "label": "会话 ID", "default": ""},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        from ...agents import agent_router
        from ...agents.base.types import AgentContext, AgentStep
        import json
        import uuid

        agent_type = config.get("agent", "auto")
        msg_template = config.get("message", "{{input}}")
        session_id = config.get("session_id") or f"wf-{uuid.uuid4().hex[:8]}"

        # 注入上游数据
        input_text = ""
        if input_data.items:
            input_text = json.dumps(input_data.items, ensure_ascii=False, default=str)
        message = msg_template.replace("{{input}}", input_text)

        if agent_type == "auto":
            agent_type, agent = await agent_router.route(message)
        else:
            agent = agent_router.get_agent(agent_type)

        if not agent:
            raise ValueError(f"Agent '{agent_type}' 不存在")

        ctx = AgentContext(
            session_id=session_id,
            user_id="workflow",
            agent_id=agent_type,
        )

        steps: list[AgentStep] = []
        final_answer = ""
        async for step in agent.run(message, ctx):
            steps.append(step)
            if step.is_final and step.final_answer:
                final_answer = step.final_answer

        return NodeData(
            items=[{"agent": agent_type, "answer": final_answer}],
            metadata={"agent": agent_type, "steps": len(steps)},
        )
