"""代码格式化器 — 简单缩进格式化"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re


class CodeFormatSchema(SkillSchema):
    code: str = Field(description="要格式化的代码")
    lang: str = Field(default="auto", description="语言: json/html/auto")
    indent: int = Field(default=2, description="缩进空格数")


class CodeFormatterSkill(BaseSkill):
    name = "code_formatter"
    description = "代码格式化: JSON 美化、HTML 缩进、通用缩进修复"
    category = "coding"
    args_schema = CodeFormatSchema
    tags = ["格式化", "代码", "format", "缩进"]

    async def execute(self, **kwargs: Any) -> str:
        code = kwargs["code"].strip()
        lang = kwargs.get("lang", "auto")
        indent = int(kwargs.get("indent", 2))

        if lang == "auto":
            if code.startswith("{") or code.startswith("["):
                lang = "json"
            elif code.startswith("<"):
                lang = "html"
            else:
                lang = "generic"

        if lang == "json":
            import json
            try:
                obj = json.loads(code)
                formatted = json.dumps(obj, ensure_ascii=False, indent=indent)
                return f"JSON 格式化:\n{formatted}"
            except json.JSONDecodeError as e:
                return f"JSON 解析失败: {e}"

        if lang == "html":
            level = 0
            sp = " " * indent
            lines = []
            for token in re.split(r'(<[^>]+>)', code):
                token = token.strip()
                if not token:
                    continue
                if token.startswith("</"):
                    level = max(0, level - 1)
                    lines.append(sp * level + token)
                elif token.startswith("<") and not token.endswith("/>") and not token.startswith("<!"):
                    lines.append(sp * level + token)
                    if not any(token.startswith(f"<{t}") for t in ["br", "hr", "img", "input", "meta", "link"]):
                        level += 1
                else:
                    lines.append(sp * level + token)
            return f"HTML 格式化:\n" + "\n".join(lines)

        # generic: 规范化缩进
        lines = code.split("\n")
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                # 保留原始缩进比例
                leading = len(line) - len(line.lstrip())
                new_indent = (leading // max(indent, 1)) * indent
                result.append(" " * new_indent + stripped)
            else:
                result.append("")

        return f"代码格式化:\n" + "\n".join(result)
