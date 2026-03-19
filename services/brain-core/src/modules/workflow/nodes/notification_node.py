"""通知节点 — 通过 Redis PubSub 推送通知到前端"""

from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class NotificationNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="notification",
            name="发送通知",
            description="向用户推送通知消息（通过 WebSocket）",
            category="output",
            icon="Bell",
            color="#10B981",
            inputs=["input"],
            outputs=["output"],
            config_schema={
                "title": {"type": "string", "label": "标题", "default": "工作流通知"},
                "message_template": {
                    "type": "textarea", "label": "消息模板",
                    "default": "{{input}}", "placeholder": "使用 {{input}} 引用上游数据",
                },
                "channel": {
                    "type": "select", "label": "通知渠道", "default": "websocket",
                    "options": ["websocket", "log"],
                },
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        import json

        title = config.get("title", "工作流通知")
        msg_template = config.get("message_template", "{{input}}")
        channel = config.get("channel", "websocket")

        input_text = ""
        if input_data.items:
            input_text = json.dumps(input_data.items, ensure_ascii=False, default=str)
        message = msg_template.replace("{{input}}", input_text)

        if channel == "websocket":
            try:
                import redis.asyncio as aioredis
                from ....common.config import settings
                r = aioredis.from_url(settings.REDIS_URL)
                await r.publish("notification:push", json.dumps({
                    "userId": input_data.metadata.get("_user_id", "system"),
                    "event": "workflow:notification",
                    "payload": {"title": title, "message": message},
                }))
                await r.aclose()
            except Exception:
                pass  # 降级为静默

        return NodeData(
            items=[{"notified": True, "title": title, "message": message}],
            metadata=input_data.metadata,
        )
