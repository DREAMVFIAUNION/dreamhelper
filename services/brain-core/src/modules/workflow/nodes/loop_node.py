"""循环节点 — 对输入数据列表逐项执行子操作

配置:
- max_iterations: 最大循环次数 (防止无限循环)
- item_key: 从输入数据中取列表的键名
- output_mode: "collect" (收集所有结果) | "last" (仅保留最后一个)
"""

from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class LoopNode(BaseNode):
    """循环节点 — 对列表中的每个元素逐项处理"""

    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="loop",
            name="循环",
            description="对列表数据逐项处理，支持最大迭代次数限制",
            category="logic",
            icon="Repeat",
            color="#8B5CF6",
            inputs=["input"],
            outputs=["item", "done"],
            config_schema={
                "max_iterations": {"type": "number", "default": 100, "description": "最大循环次数"},
                "item_key": {"type": "string", "default": "items", "description": "输入数据中列表字段名"},
                "output_mode": {"type": "select", "options": ["collect", "last"], "default": "collect"},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        max_iter = config.get("max_iterations", 100)
        item_key = config.get("item_key", "items")
        output_mode = config.get("output_mode", "collect")

        # 从输入中提取列表
        items_list = []
        for item in input_data.items:
            if item_key in item:
                val = item[item_key]
                if isinstance(val, list):
                    items_list.extend(val)
                else:
                    items_list.append(val)
            else:
                items_list.append(item)

        # 限制最大迭代次数
        items_list = items_list[:max_iter]

        # 输出: 将每个元素包装为独立的 NodeData item
        output_items = []
        for i, elem in enumerate(items_list):
            if isinstance(elem, dict):
                output_items.append({**elem, "_loop_index": i, "_loop_total": len(items_list)})
            else:
                output_items.append({"value": elem, "_loop_index": i, "_loop_total": len(items_list)})

        if output_mode == "last" and output_items:
            output_items = [output_items[-1]]

        return NodeData(
            items=output_items,
            metadata={
                "loop_count": len(items_list),
                "output_mode": output_mode,
            },
        )
