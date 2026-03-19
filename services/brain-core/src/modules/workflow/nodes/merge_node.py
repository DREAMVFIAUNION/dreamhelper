"""合并节点 — 将多个上游分支的数据合并为一个输出

配置:
- mode: "concat" (拼接所有items) | "zip" (按索引配对) | "object" (按来源键合并为对象)
- deduplicate: 是否去重
"""

from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class MergeNode(BaseNode):
    """合并节点 — 汇聚多个分支的数据"""

    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="merge",
            name="合并",
            description="将多个分支的数据合并为单个输出，支持拼接、配对、对象合并",
            category="logic",
            icon="GitMerge",
            color="#06B6D4",
            inputs=["input_a", "input_b"],
            outputs=["output"],
            config_schema={
                "mode": {
                    "type": "select",
                    "options": ["concat", "zip", "object"],
                    "default": "concat",
                    "description": "合并模式: concat=拼接, zip=配对, object=按键合并",
                },
                "deduplicate": {"type": "boolean", "default": False, "description": "是否去重"},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        mode = config.get("mode", "concat")
        deduplicate = config.get("deduplicate", False)

        items = input_data.items

        if mode == "concat":
            result = list(items)
        elif mode == "zip":
            # 将items按_source分组后配对
            half = len(items) // 2
            group_a = items[:half] if half > 0 else items
            group_b = items[half:] if half > 0 else []
            result = []
            for i in range(max(len(group_a), len(group_b))):
                merged = {}
                if i < len(group_a):
                    merged["a"] = group_a[i]
                if i < len(group_b):
                    merged["b"] = group_b[i]
                result.append(merged)
        elif mode == "object":
            # 所有items合并为一个大对象
            merged_obj: dict[str, Any] = {}
            for item in items:
                merged_obj.update(item)
            result = [merged_obj]
        else:
            result = list(items)

        # 去重（基于JSON序列化）
        if deduplicate and result:
            import json
            seen: set[str] = set()
            unique = []
            for item in result:
                key = json.dumps(item, sort_keys=True, default=str)
                if key not in seen:
                    seen.add(key)
                    unique.append(item)
            result = unique

        return NodeData(
            items=result,
            metadata={"merge_mode": mode, "item_count": len(result)},
        )
