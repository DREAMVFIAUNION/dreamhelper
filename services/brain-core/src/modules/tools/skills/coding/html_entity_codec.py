"""HTML 实体编解码 — 转义/反转义 HTML 特殊字符"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import html


class HtmlEntitySchema(SkillSchema):
    text: str = Field(description="要编码或解码的文本")
    mode: str = Field(default="auto", description="encode=编码, decode=解码, auto=自动判断")


class HtmlEntityCodecSkill(BaseSkill):
    name = "html_entity_codec"
    description = "HTML 实体编码与解码 (如 &amp; ↔ &)"
    category = "coding"
    args_schema = HtmlEntitySchema
    tags = ["HTML", "实体", "编码", "解码", "entity"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs["text"]
        mode = kwargs.get("mode", "auto")

        if mode == "auto":
            mode = "decode" if "&" in text and ";" in text else "encode"

        if mode == "encode":
            result = html.escape(text, quote=True)
            return f"HTML 编码:\n  原文: {text}\n  结果: {result}"
        else:
            result = html.unescape(text)
            return f"HTML 解码:\n  原文: {text}\n  结果: {result}"
