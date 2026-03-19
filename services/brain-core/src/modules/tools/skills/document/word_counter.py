"""字数统计器 — 中英文字数/行数/段落统计"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re


class WordCountSchema(SkillSchema):
    text: str = Field(description="要统计的文本")


class WordCounterSkill(BaseSkill):
    name = "word_counter"
    description = "精确字数统计: 中文字数、英文词数、行数、段落数"
    category = "document"
    args_schema = WordCountSchema
    tags = ["字数", "统计", "word count", "计数"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs["text"]
        if not text.strip():
            return "文本为空"

        total_chars = len(text)
        cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        en_words = len(re.findall(r'[a-zA-Z]+', text))
        numbers = len(re.findall(r'\d+', text))
        punctuation = len(re.findall(r'[^\w\s]', text))
        spaces = text.count(' ') + text.count('\t')
        lines = text.count('\n') + 1
        paragraphs = len(re.split(r'\n\s*\n', text.strip()))
        chars_no_space = total_chars - spaces - text.count('\n')

        return (
            f"字数统计:\n"
            f"  总字符: {total_chars}\n"
            f"  非空字符: {chars_no_space}\n"
            f"  中文字: {cn_chars}\n"
            f"  英文词: {en_words}\n"
            f"  数字: {numbers}\n"
            f"  标点: {punctuation}\n"
            f"  空格: {spaces}\n"
            f"  行数: {lines}\n"
            f"  段落: {paragraphs}"
        )
