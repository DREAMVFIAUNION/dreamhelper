"""条件分支节点 — if/else/switch 逻辑"""

from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class ConditionNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="condition",
            name="条件分支",
            description="根据条件判断走不同路径（if/else）",
            category="logic",
            icon="GitBranch",
            color="#06B6D4",
            inputs=["input"],
            outputs=["true", "false"],
            config_schema={
                "field": {"type": "string", "label": "判断字段", "default": "", "placeholder": "items[0].status"},
                "operator": {
                    "type": "select", "label": "运算符", "default": "==",
                    "options": ["==", "!=", ">", "<", ">=", "<=", "contains", "not_contains", "is_empty", "is_not_empty"],
                },
                "value": {"type": "string", "label": "比较值", "default": ""},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        field_path = config.get("field", "")
        operator = config.get("operator", "==")
        compare_value = config.get("value", "")

        # 从 input_data 中提取字段值
        actual_value = self._resolve_field(input_data, field_path)

        result = self._evaluate(actual_value, operator, compare_value)

        return NodeData(
            items=input_data.items if input_data.items else [{}],
            metadata={
                **input_data.metadata,
                "_condition_result": result,
                "_condition_field": field_path,
                "_condition_operator": operator,
            },
        )

    def _resolve_field(self, data: NodeData, field_path: str) -> Any:
        """从 NodeData 中解析字段路径，如 items[0].status"""
        if not field_path:
            return data.items[0] if data.items else None

        obj: Any = {"items": data.items, "metadata": data.metadata}
        for part in field_path.replace("[", ".").replace("]", "").split("."):
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

    def _evaluate(self, actual: Any, operator: str, expected: str) -> bool:
        if operator == "is_empty":
            return actual is None or actual == "" or actual == [] or actual == {}
        if operator == "is_not_empty":
            return not (actual is None or actual == "" or actual == [] or actual == {})

        # 类型转换尝试
        if actual is not None:
            try:
                if isinstance(actual, (int, float)):
                    expected_val: Any = float(expected)
                else:
                    expected_val = expected
            except ValueError:
                expected_val = expected
        else:
            expected_val = expected

        actual_str = str(actual) if actual is not None else ""

        if operator == "==":
            return str(actual) == str(expected) or actual == expected_val
        elif operator == "!=":
            return str(actual) != str(expected) and actual != expected_val
        elif operator == "contains":
            return str(expected) in actual_str
        elif operator == "not_contains":
            return str(expected) not in actual_str
        elif operator in (">", "<", ">=", "<="):
            try:
                a, b = float(actual), float(expected)
                if operator == ">": return a > b
                if operator == "<": return a < b
                if operator == ">=": return a >= b
                if operator == "<=": return a <= b
            except (TypeError, ValueError):
                return False
        return False
