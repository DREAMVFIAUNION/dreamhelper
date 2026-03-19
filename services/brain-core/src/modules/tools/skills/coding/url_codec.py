"""URL 编解码技能"""

from typing import Any
from urllib.parse import quote, unquote, urlparse, parse_qs

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class UrlCodecSchema(SkillSchema):
    action: str = Field(description="操作: 'encode'(编码), 'decode'(解码), 'parse'(解析URL)")
    text: str = Field(description="要编码/解码的文本或 URL")


class UrlCodecSkill(BaseSkill):
    name = "url_codec"
    description = "URL 编码/解码/解析工具"
    category = "coding"
    args_schema = UrlCodecSchema
    tags = ["URL", "编码", "解码", "uri", "percent"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "encode")
        text = kwargs.get("text", "")
        if not text:
            return "请输入文本"

        if action == "encode":
            return f"URL 编码结果:\n{quote(text, safe='')}"

        elif action == "decode":
            return f"URL 解码结果:\n{unquote(text)}"

        elif action == "parse":
            try:
                parsed = urlparse(text)
                params = parse_qs(parsed.query)
                lines = [
                    f"URL 解析结果:",
                    f"  协议: {parsed.scheme or '(无)'}",
                    f"  域名: {parsed.netloc or '(无)'}",
                    f"  路径: {parsed.path or '/'}",
                    f"  查询: {parsed.query or '(无)'}",
                    f"  片段: {parsed.fragment or '(无)'}",
                ]
                if params:
                    lines.append("  参数:")
                    for k, v in params.items():
                        lines.append(f"    {k} = {', '.join(v)}")
                return "\n".join(lines)
            except Exception as e:
                return f"URL 解析失败: {e}"

        return f"未知操作: {action}"
