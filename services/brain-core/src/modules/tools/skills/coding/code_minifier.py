"""代码压缩器 — 去除注释和空白"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re


class MinifySchema(SkillSchema):
    code: str = Field(description="要压缩的代码")
    lang: str = Field(default="auto", description="语言: js/css/html/auto")


class CodeMinifierSkill(BaseSkill):
    name = "code_minifier"
    description = "代码压缩: 去除注释、空白、换行"
    category = "coding"
    args_schema = MinifySchema
    tags = ["压缩", "minify", "代码", "优化"]

    async def execute(self, **kwargs: Any) -> str:
        code = kwargs["code"]
        lang = kwargs.get("lang", "auto")
        orig_len = len(code)

        if lang == "auto":
            if "<" in code and ">" in code:
                lang = "html"
            elif "{" in code and "}" in code and (":" in code or "=" in code):
                lang = "js"
            else:
                lang = "js"

        result = code
        if lang in ("js", "auto"):
            # 去除单行注释
            result = re.sub(r'//.*$', '', result, flags=re.MULTILINE)
            # 去除多行注释
            result = re.sub(r'/\*[\s\S]*?\*/', '', result)
        elif lang == "css":
            result = re.sub(r'/\*[\s\S]*?\*/', '', result)
        elif lang == "html":
            result = re.sub(r'<!--[\s\S]*?-->', '', result)

        # 去除多余空白
        result = re.sub(r'[ \t]+', ' ', result)
        result = re.sub(r'\n\s*\n', '\n', result)
        # 去除行首尾空白
        lines = [l.strip() for l in result.split('\n') if l.strip()]
        result = ' '.join(lines)

        new_len = len(result)
        ratio = (1 - new_len / max(orig_len, 1)) * 100

        return (
            f"代码压缩 ({lang}):\n"
            f"  原始: {orig_len} 字符\n"
            f"  压缩: {new_len} 字符\n"
            f"  节省: {ratio:.1f}%\n\n"
            f"{result[:1000]}"
        )
