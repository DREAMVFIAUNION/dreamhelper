"""延时节点 — 等待指定时间后继续"""

import asyncio
from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class DelayNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="delay",
            name="延时等待",
            description="等待指定秒数后继续执行下游节点",
            category="logic",
            icon="Timer",
            color="#06B6D4",
            inputs=["input"],
            outputs=["output"],
            config_schema={
                "seconds": {"type": "number", "label": "等待秒数", "default": 5, "min": 1, "max": 3600},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        seconds = min(max(int(config.get("seconds", 5)), 1), 3600)
        await asyncio.sleep(seconds)
        return input_data
