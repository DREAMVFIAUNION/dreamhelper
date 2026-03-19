"""YAML 处理器 — YAML ↔ JSON 互转 + 校验"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import json


class YamlSchema(SkillSchema):
    data: str = Field(description="YAML 或 JSON 文本")
    operation: str = Field(default="to_json", description="操作: to_json(转JSON)/validate(校验)/to_yaml(从JSON转YAML)")


def _simple_yaml_parse(text: str) -> dict:
    """极简 YAML 解析 (仅支持 key: value 单层)"""
    result = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ": " in line:
            key, val = line.split(": ", 1)
            key = key.strip().strip('"').strip("'")
            val = val.strip().strip('"').strip("'")
            if val.lower() == "true":
                result[key] = True
            elif val.lower() == "false":
                result[key] = False
            elif val.lower() == "null" or val == "~":
                result[key] = None
            else:
                try:
                    result[key] = int(val)
                except ValueError:
                    try:
                        result[key] = float(val)
                    except ValueError:
                        result[key] = val
    return result


def _dict_to_yaml(d: dict, indent: int = 0) -> str:
    lines = []
    prefix = "  " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            lines.append(f"{prefix}{k}:")
            lines.append(_dict_to_yaml(v, indent + 1))
        elif isinstance(v, list):
            lines.append(f"{prefix}{k}:")
            for item in v:
                lines.append(f"{prefix}  - {item}")
        elif isinstance(v, bool):
            lines.append(f"{prefix}{k}: {'true' if v else 'false'}")
        elif v is None:
            lines.append(f"{prefix}{k}: null")
        else:
            lines.append(f"{prefix}{k}: {v}")
    return "\n".join(lines)


class YamlProcessorSkill(BaseSkill):
    name = "yaml_processor"
    description = "YAML/JSON 互转和校验"
    category = "office"
    args_schema = YamlSchema
    tags = ["YAML", "JSON", "转换", "配置"]

    async def execute(self, **kwargs: Any) -> str:
        data = kwargs["data"].strip()
        op = kwargs.get("operation", "to_json")

        if op == "to_json":
            parsed = _simple_yaml_parse(data)
            if not parsed:
                return "解析失败: 无法解析 YAML (仅支持简单 key: value 格式)"
            return f"YAML → JSON:\n{json.dumps(parsed, ensure_ascii=False, indent=2)}"

        elif op == "to_yaml":
            try:
                obj = json.loads(data)
            except json.JSONDecodeError as e:
                return f"JSON 解析失败: {e}"
            if not isinstance(obj, dict):
                return "仅支持 JSON 对象转 YAML"
            return f"JSON → YAML:\n{_dict_to_yaml(obj)}"

        elif op == "validate":
            try:
                obj = json.loads(data)
                return f"JSON 校验通过 ✓\n类型: {type(obj).__name__}\n{json.dumps(obj, ensure_ascii=False, indent=2)[:500]}"
            except json.JSONDecodeError:
                parsed = _simple_yaml_parse(data)
                if parsed:
                    return f"YAML 校验通过 ✓\n键数: {len(parsed)}"
                return "校验失败: 非有效 JSON 或 YAML"

        return "不支持的操作: to_json/to_yaml/validate"
