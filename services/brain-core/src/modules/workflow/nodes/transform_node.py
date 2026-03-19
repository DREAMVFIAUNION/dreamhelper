"""数据转换节点 — JSON 映射、模板渲染、数据提取"""

from typing import Any
import json

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class TransformNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="transform",
            name="数据转换",
            description="JSON 映射、模板渲染、字段提取",
            category="logic",
            icon="Shuffle",
            color="#06B6D4",
            inputs=["input"],
            outputs=["output"],
            config_schema={
                "mode": {
                    "type": "select", "label": "模式", "default": "template",
                    "options": ["template", "jq", "pick_fields"],
                },
                "template": {
                    "type": "textarea", "label": "模板 / 表达式",
                    "default": "", "placeholder": "模板模式: {{items[0].content}}\npick_fields: field1,field2",
                },
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        mode = config.get("mode", "template")
        template = config.get("template", "")

        if mode == "template":
            return self._template_mode(input_data, template)
        elif mode == "pick_fields":
            return self._pick_fields_mode(input_data, template)
        else:
            # jq 模式 — 简单实现
            return self._template_mode(input_data, template)

    def _template_mode(self, data: NodeData, template: str) -> NodeData:
        """简单模板替换: {{items[0].key}} → value"""
        result = template
        context = {"items": data.items, "metadata": data.metadata}

        import re
        for match in re.finditer(r"\{\{(.+?)\}\}", template):
            path = match.group(1).strip()
            value = self._resolve(context, path)
            result = result.replace(match.group(0), str(value) if value is not None else "")

        try:
            parsed = json.loads(result)
            if isinstance(parsed, list):
                return NodeData(items=parsed)
            return NodeData.single(parsed)
        except (json.JSONDecodeError, TypeError):
            return NodeData.single({"result": result})

    def _pick_fields_mode(self, data: NodeData, fields_str: str) -> NodeData:
        """提取指定字段"""
        fields = [f.strip() for f in fields_str.split(",") if f.strip()]
        items = []
        for item in data.items:
            picked = {k: item.get(k) for k in fields if k in item}
            items.append(picked)
        return NodeData(items=items)

    def _resolve(self, obj: Any, path: str) -> Any:
        for part in path.replace("[", ".").replace("]", "").split("."):
            if not part:
                continue
            if isinstance(obj, dict):
                obj = obj.get(part)
            elif isinstance(obj, (list, tuple)):
                try:
                    obj = obj[int(part)]
                except (IndexError, ValueError):
                    return None
            else:
                return None
        return obj
