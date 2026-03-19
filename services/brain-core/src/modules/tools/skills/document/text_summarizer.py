"""提取式摘要 — 基于句子重要性的简单摘要"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re
from collections import Counter


class SummarySchema(SkillSchema):
    text: str = Field(description="要摘要的文本")
    sentences: int = Field(default=3, description="摘要句数(默认3)")


class TextSummarizerSkill(BaseSkill):
    name = "text_summarizer"
    description = "提取式文本摘要: 基于词频的关键句提取"
    category = "document"
    args_schema = SummarySchema
    tags = ["摘要", "总结", "summary", "提取"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs["text"].strip()
        n = int(kwargs.get("sentences", 3))

        if not text:
            return "文本为空"

        # 分句
        sents = re.split(r'(?<=[。！？.!?\n])', text)
        sents = [s.strip() for s in sents if len(s.strip()) > 5]

        if len(sents) <= n:
            return f"文本较短 ({len(sents)} 句)，无需摘要:\n{text}"

        # 词频
        words = re.findall(r'[\u4e00-\u9fff]{2,4}|[a-zA-Z]{3,}', text.lower())
        freq = Counter(words)

        # 句子评分
        scored = []
        for i, sent in enumerate(sents):
            sent_words = re.findall(r'[\u4e00-\u9fff]{2,4}|[a-zA-Z]{3,}', sent.lower())
            score = sum(freq.get(w, 0) for w in sent_words)
            # 位置加权: 首句和末句加分
            if i == 0:
                score *= 1.5
            elif i == len(sents) - 1:
                score *= 1.2
            scored.append((i, score, sent))

        # 按分数取 top-n，按原始顺序排列
        top = sorted(scored, key=lambda x: -x[1])[:n]
        top = sorted(top, key=lambda x: x[0])

        summary = "\n".join(s[2] for s in top)
        ratio = len(summary) / max(len(text), 1) * 100

        return (
            f"文本摘要 ({n} 句, 压缩率 {ratio:.0f}%):\n\n"
            f"{summary}\n\n"
            f"[原文 {len(sents)} 句 / {len(text)} 字]"
        )
