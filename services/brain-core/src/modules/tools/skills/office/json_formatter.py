"""JSON 格式化技能 — 美化/压缩/校验 JSON"""

import json
from typing import Any

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class JsonFormatSchema(SkillSchema):
    text: str = Field(description="JSON 文本")
    action: str = Field(default="format", description="操作: 'format'(美化), 'minify'(压缩), 'validate'(校验)")
    indent: int = Field(default=2, description="缩进空格数 (action=format)")


class JsonFormatterSkill(BaseSkill):
    name = "json_formatter"
    description = "JSON 工具：美化格式化、压缩、校验 JSON 文本"
    category = "office"
    args_schema = JsonFormatSchema
    tags = ["JSON", "格式化", "校验", "format"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs.get("text", "").strip()
        action = kwargs.get("action", "format")
        indent = max(1, min(8, int(kwargs.get("indent", 2))))

        if not text:
            return "请输入 JSON 文本"

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            return f"JSON 校验失败:\n  错误: {e.msg}\n  位置: 第 {e.lineno} 行, 第 {e.colno} 列"

        if action == "validate":
            obj_type = type(parsed).__name__
            if isinstance(parsed, dict):
                info = f"对象，{len(parsed)} 个键"
            elif isinstance(parsed, list):
                info = f"数组，{len(parsed)} 个元素"
            else:
                info = f"类型: {obj_type}"
            return f"JSON 校验通过!\n  类型: {info}\n  大小: {len(text)} 字符"

        elif action == "minify":
            minified = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
            saved = len(text) - len(minified)
            return f"压缩结果 (节省 {saved} 字符):\n{minified}"

        else:  # format
            formatted = json.dumps(parsed, ensure_ascii=False, indent=indent)
            return f"格式化结果:\n{formatted}"
