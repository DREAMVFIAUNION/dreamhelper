"""HTML 清洗器 — 去除 HTML 标签保留纯文本"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re
import html as html_mod


class HtmlCleanSchema(SkillSchema):
    html: str = Field(description="HTML 文本")
    keep_links: bool = Field(default=False, description="是否保留链接地址")


class HtmlCleanerSkill(BaseSkill):
    name = "html_cleaner"
    description = "去除 HTML 标签，提取纯文本内容"
    category = "document"
    args_schema = HtmlCleanSchema
    tags = ["HTML", "清洗", "纯文本", "strip"]

    async def execute(self, **kwargs: Any) -> str:
        raw = kwargs["html"]
        keep_links = kwargs.get("keep_links", False)

        text = raw
        # 移除 script 和 style
        text = re.sub(r'<script[\s\S]*?</script>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<style[\s\S]*?</style>', '', text, flags=re.IGNORECASE)
        # 提取链接
        if keep_links:
            text = re.sub(r'<a[^>]+href="([^"]*)"[^>]*>([\s\S]*?)</a>', r'\2 [\1]', text, flags=re.IGNORECASE)
        # 块级标签换行
        text = re.sub(r'<(?:br|p|div|h[1-6]|li|tr)[^>]*/?>', '\n', text, flags=re.IGNORECASE)
        # 去除所有标签
        text = re.sub(r'<[^>]+>', '', text)
        # 解码实体
        text = html_mod.unescape(text)
        # 清理多余空白
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text).strip()

        orig_len = len(raw)
        clean_len = len(text)

        return (
            f"HTML 清洗结果:\n"
            f"  原始: {orig_len} 字符 → 纯文本: {clean_len} 字符\n"
            f"  压缩率: {(1 - clean_len / max(orig_len, 1)) * 100:.0f}%\n\n"
            f"{text[:2000]}"
        )
