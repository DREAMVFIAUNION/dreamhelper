"""JSON 转 CSV — 展平嵌套 JSON 为 CSV"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import json


def _flatten(obj: Any, prefix: str = "") -> dict:
    """递归展平嵌套字典"""
    items: dict = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            items.update(_flatten(v, new_key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            items.update(_flatten(v, f"{prefix}[{i}]"))
    else:
        items[prefix] = obj
    return items


class JsonCsvSchema(SkillSchema):
    data: str = Field(description="JSON 数据 (对象或数组)")


class JsonToCsvSkill(BaseSkill):
    name = "json_to_csv"
    description = "将 JSON 数据展平并转换为 CSV 格式"
    category = "document"
    args_schema = JsonCsvSchema
    tags = ["JSON", "CSV", "转换", "展平"]

    async def execute(self, **kwargs: Any) -> str:
        data = kwargs["data"].strip()
        try:
            obj = json.loads(data)
        except json.JSONDecodeError as e:
            return f"JSON 解析失败: {e}"

        if isinstance(obj, dict):
            rows = [obj]
        elif isinstance(obj, list):
            rows = obj
        else:
            return "JSON 必须是对象或数组"

        flat_rows = [_flatten(r) for r in rows]
        all_keys = []
        seen = set()
        for row in flat_rows:
            for k in row:
                if k not in seen:
                    all_keys.append(k)
                    seen.add(k)

        lines = [",".join(all_keys)]
        for row in flat_rows:
            vals = [str(row.get(k, "")) for k in all_keys]
            lines.append(",".join(f'"{v}"' if "," in str(v) else str(v) for v in vals))

        csv_text = "\n".join(lines)
        return f"CSV 转换结果 ({len(flat_rows)} 行, {len(all_keys)} 列):\n{csv_text}"
