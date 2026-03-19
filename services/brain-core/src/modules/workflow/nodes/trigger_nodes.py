"""触发器节点 — Manual / Cron / Webhook / Event"""

from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class ManualTriggerNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="trigger_manual",
            name="手动触发",
            description="手动点击执行工作流",
            category="trigger",
            icon="Play",
            color="#FF2D55",
            inputs=[],
            outputs=["output"],
            config_schema={},
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        return NodeData.single({"trigger": "manual", "timestamp": __import__("time").time()})


class CronTriggerNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="trigger_cron",
            name="定时触发",
            description="按 Cron 表达式定时执行",
            category="trigger",
            icon="Clock",
            color="#FF2D55",
            inputs=[],
            outputs=["output"],
            config_schema={
                "cron": {"type": "string", "label": "Cron 表达式", "default": "0 9 * * *", "placeholder": "分 时 日 月 周"},
                "timezone": {"type": "string", "label": "时区", "default": "Asia/Shanghai"},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        return NodeData.single({
            "trigger": "cron",
            "cron": config.get("cron", ""),
            "timestamp": __import__("time").time(),
        })


class WebhookTriggerNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="trigger_webhook",
            name="Webhook 触发",
            description="通过 HTTP Webhook 触发执行",
            category="trigger",
            icon="Webhook",
            color="#FF2D55",
            inputs=[],
            outputs=["output"],
            config_schema={
                "path": {"type": "string", "label": "Webhook 路径", "default": "", "placeholder": "my-webhook"},
                "method": {"type": "select", "label": "HTTP 方法", "default": "POST", "options": ["GET", "POST", "PUT"]},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        # Webhook 触发时，input_data 已包含 HTTP 请求数据
        if input_data.items:
            return input_data
        return NodeData.single({"trigger": "webhook", "path": config.get("path", "")})


class EventTriggerNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="trigger_event",
            name="事件触发",
            description="监听系统事件（新消息、用户登录等）",
            category="trigger",
            icon="Zap",
            color="#FF2D55",
            inputs=[],
            outputs=["output"],
            config_schema={
                "event": {"type": "select", "label": "事件类型", "default": "message.created",
                          "options": ["message.created", "user.login", "session.created", "custom"]},
                "filter": {"type": "string", "label": "过滤条件 (JSON)", "default": "{}"},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        if input_data.items:
            return input_data
        return NodeData.single({"trigger": "event", "event": config.get("event", "")})
