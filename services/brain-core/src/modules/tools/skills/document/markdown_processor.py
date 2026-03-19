"""Markdown 处理器 — Markdown→HTML 纯正则转换"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re
import html as html_mod


class MarkdownSchema(SkillSchema):
    text: str = Field(description="Markdown 文本")
    mode: str = Field(default="to_html", description="模式: to_html(转HTML)/strip(去格式)")


class MarkdownProcessorSkill(BaseSkill):
    name = "markdown_processor"
    description = "Markdown 转 HTML 或去格式纯文本"
    category = "document"
    args_schema = MarkdownSchema
    tags = ["markdown", "HTML", "转换", "文档"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs["text"]
        mode = kwargs.get("mode", "to_html")

        if mode == "strip":
            result = text
            result = re.sub(r'```[\s\S]*?```', '', result)
            result = re.sub(r'`([^`]+)`', r'\1', result)
            result = re.sub(r'#{1,6}\s+', '', result)
            result = re.sub(r'\*\*(.+?)\*\*', r'\1', result)
            result = re.sub(r'\*(.+?)\*', r'\1', result)
            result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', result)
            result = re.sub(r'^[-*]\s+', '', result, flags=re.MULTILINE)
            result = re.sub(r'^\d+\.\s+', '', result, flags=re.MULTILINE)
            result = re.sub(r'\n{3,}', '\n\n', result).strip()
            return f"纯文本结果:\n{result}"

        # to_html
        h = text
        # 代码块
        h = re.sub(r'```(\w*)\n([\s\S]*?)```', lambda m: f'<pre><code class="{m.group(1)}">{html_mod.escape(m.group(2).strip())}</code></pre>', h)
        h = re.sub(r'`([^`]+)`', r'<code>\1</code>', h)
        # 标题
        h = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', h, flags=re.MULTILINE)
        h = re.sub(r'^### (.+)$', r'<h3>\1</h3>', h, flags=re.MULTILINE)
        h = re.sub(r'^## (.+)$', r'<h2>\1</h2>', h, flags=re.MULTILINE)
        h = re.sub(r'^# (.+)$', r'<h1>\1</h1>', h, flags=re.MULTILINE)
        # 粗体/斜体
        h = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', h)
        h = re.sub(r'\*(.+?)\*', r'<em>\1</em>', h)
        # 链接
        h = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', h)
        # 分割线
        h = re.sub(r'^---$', '<hr>', h, flags=re.MULTILINE)
        # 列表
        h = re.sub(r'^[-*]\s+(.+)$', r'<li>\1</li>', h, flags=re.MULTILINE)
        # 段落
        h = re.sub(r'^(?!<[hlopua]|<pre|<hr)(.+)$', r'<p>\1</p>', h, flags=re.MULTILINE)

        return f"HTML 转换结果:\n{h}"
