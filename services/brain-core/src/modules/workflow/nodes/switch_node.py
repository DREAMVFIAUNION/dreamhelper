"""多路分支节点 — 根据表达式值路由到不同输出端口

配置:
- field: 要检查的字段名
- cases: 匹配规则列表 [{value: "...", output: "case_0"}, ...]
- default_output: 默认输出端口名
"""

from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class SwitchNode(BaseNode):
    """多路分支节点 — 基于字段值路由到不同输出"""

    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="switch",
            name="多路分支",
            description="根据字段值路由到不同分支，支持多个case和默认分支",
            category="logic",
            icon="GitBranch",
            color="#F59E0B",
            inputs=["input"],
            outputs=["case_0", "case_1", "case_2", "default"],
            config_schema={
                "field": {"type": "string", "default": "type", "description": "要检查的字段名"},
                "cases": {
                    "type": "array",
                    "description": "匹配规则列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string", "description": "匹配值"},
                            "operator": {
                                "type": "select",
                                "options": ["equals", "contains", "gt", "lt", "regex"],
                                "default": "equals",
                            },
                        },
                    },
                },
                "default_output": {"type": "string", "default": "default"},
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        field_name = config.get("field", "type")
        cases = config.get("cases", [])
        default_output = config.get("default_output", "default")

        # 从输入数据中获取字段值
        field_value = None
        for item in input_data.items:
            if field_name in item:
                field_value = item[field_name]
                break

        # 也检查 metadata
        if field_value is None:
            field_value = input_data.metadata.get(field_name)

        # 匹配 case
        matched_output = default_output
        matched_index = -1

        for i, case in enumerate(cases):
            case_value = case.get("value", "")
            operator = case.get("operator", "equals")

            if self._match(field_value, case_value, operator):
                matched_output = f"case_{i}"
                matched_index = i
                break

        return NodeData(
            items=input_data.items,
            metadata={
                **input_data.metadata,
                "_branch": matched_output,
                "_switch_field": field_name,
                "_switch_value": str(field_value),
                "_matched_case": matched_index,
            },
        )

    @staticmethod
    def _match(field_value: Any, case_value: str, operator: str) -> bool:
        """执行匹配操作"""
        if field_value is None:
            return False

        str_val = str(field_value)

        if operator == "equals":
            return str_val == case_value
        elif operator == "contains":
            return case_value in str_val
        elif operator == "gt":
            try:
                return float(field_value) > float(case_value)
            except (ValueError, TypeError):
                return False
        elif operator == "lt":
            try:
                return float(field_value) < float(case_value)
            except (ValueError, TypeError):
                return False
        elif operator == "regex":
            import re
            try:
                return bool(re.search(case_value, str_val))
            except re.error:
                return False

        return str_val == case_value
