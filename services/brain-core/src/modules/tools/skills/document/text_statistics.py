"""文本统计 — 字数/词频/阅读时间"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re
from collections import Counter


class TextStatsSchema(SkillSchema):
    text: str = Field(description="要统计的文本")


class TextStatisticsSkill(BaseSkill):
    name = "text_statistics"
    description = "文本统计: 字数、词频、句数、阅读时间"
    category = "document"
    args_schema = TextStatsSchema
    tags = ["统计", "字数", "词频", "阅读时间"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs["text"].strip()
        if not text:
            return "文本为空"

        chars = len(text)
        chars_no_space = len(text.replace(" ", "").replace("\n", ""))
        lines = text.count("\n") + 1
        sentences = len(re.split(r'[。！？.!?]+', text)) - 1 or 1

        # 中文字符数
        cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 英文单词
        en_words = re.findall(r'[a-zA-Z]+', text)
        en_word_count = len(en_words)

        # 阅读时间 (中文300字/分钟, 英文200词/分钟)
        read_min = cn_chars / 300 + en_word_count / 200
        read_min = max(read_min, 0.1)

        # 高频词 (≥2字的中文词或英文词)
        words = re.findall(r'[\u4e00-\u9fff]{2,4}|[a-zA-Z]{3,}', text.lower())
        top_words = Counter(words).most_common(8)

        lines_out = [
            f"文本统计:",
            f"  总字符: {chars} | 非空字符: {chars_no_space}",
            f"  中文字: {cn_chars} | 英文词: {en_word_count}",
            f"  行数: {lines} | 句数: {sentences}",
            f"  预计阅读: {read_min:.1f} 分钟",
        ]
        if top_words:
            lines_out.append(f"  高频词: {', '.join(f'{w}({c})' for w, c in top_words)}")

        return "\n".join(lines_out)
