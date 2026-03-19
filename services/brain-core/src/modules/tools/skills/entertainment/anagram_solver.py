"""字母重排检测 — 判断两个词是否为变位词"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
from collections import Counter


class AnagramSchema(SkillSchema):
    word1: str = Field(description="第一个词")
    word2: str = Field(description="第二个词")


class AnagramSolverSkill(BaseSkill):
    name = "anagram_solver"
    description = "检测两个词是否为变位词(字母重排)"
    category = "entertainment"
    args_schema = AnagramSchema
    tags = ["变位词", "anagram", "字母", "游戏"]

    async def execute(self, **kwargs: Any) -> str:
        w1 = kwargs["word1"].strip().lower().replace(" ", "")
        w2 = kwargs["word2"].strip().lower().replace(" ", "")

        c1 = Counter(w1)
        c2 = Counter(w2)
        is_anagram = c1 == c2

        lines = [
            f"变位词检测:",
            f"  词1: {kwargs['word1']} → 字母: {dict(c1)}",
            f"  词2: {kwargs['word2']} → 字母: {dict(c2)}",
            f"  结果: {'✓ 是变位词！' if is_anagram else '✗ 不是变位词'}",
        ]
        if not is_anagram:
            diff1 = c1 - c2
            diff2 = c2 - c1
            if diff1:
                lines.append(f"  词1多余: {dict(diff1)}")
            if diff2:
                lines.append(f"  词2多余: {dict(diff2)}")

        return "\n".join(lines)
