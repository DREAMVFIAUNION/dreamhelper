"""JSON 校验器 — 校验 JSON 格式并提供详细错误信息"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import json


class JsonValidatorSchema(SkillSchema):
    data: str = Field(description="要校验的 JSON 文本")


class JsonValidatorSkill(BaseSkill):
    name = "json_validator"
    description = "校验 JSON 格式，提供详细错误信息和统计"
    category = "coding"
    args_schema = JsonValidatorSchema
    tags = ["JSON", "校验", "validate", "格式"]

    async def execute(self, **kwargs: Any) -> str:
        data = kwargs["data"].strip()
        if not data:
            return "JSON 数据为空"

        try:
            obj = json.loads(data)
        except json.JSONDecodeError as e:
            return (
                f"JSON 校验失败 ✗\n"
                f"  错误: {e.msg}\n"
                f"  位置: 行 {e.lineno}, 列 {e.colno}\n"
                f"  上下文: ...{data[max(0, e.pos-20):e.pos+20]}..."
            )

        def _stats(o: Any, depth: int = 0) -> dict:
            s = {"keys": 0, "arrays": 0, "strings": 0, "numbers": 0, "booleans": 0, "nulls": 0, "max_depth": depth}
            if isinstance(o, dict):
                s["keys"] += len(o)
                for v in o.values():
                    child = _stats(v, depth + 1)
                    for k in child:
                        if k == "max_depth":
                            s[k] = max(s[k], child[k])
                        else:
                            s[k] += child[k]
            elif isinstance(o, list):
                s["arrays"] += 1
                for item in o:
                    child = _stats(item, depth + 1)
                    for k in child:
                        if k == "max_depth":
                            s[k] = max(s[k], child[k])
                        else:
                            s[k] += child[k]
            elif isinstance(o, str):
                s["strings"] += 1
            elif isinstance(o, (int, float)):
                s["numbers"] += 1
            elif isinstance(o, bool):
                s["booleans"] += 1
            elif o is None:
                s["nulls"] += 1
            return s

        stats = _stats(obj)
        root_type = type(obj).__name__

        return (
            f"JSON 校验通过 ✓\n"
            f"  根类型: {root_type}\n"
            f"  键数: {stats['keys']}\n"
            f"  字符串: {stats['strings']} | 数字: {stats['numbers']}\n"
            f"  布尔: {stats['booleans']} | 空值: {stats['nulls']}\n"
            f"  数组: {stats['arrays']} | 最大深度: {stats['max_depth']}\n"
            f"  大小: {len(data)} 字符"
        )
