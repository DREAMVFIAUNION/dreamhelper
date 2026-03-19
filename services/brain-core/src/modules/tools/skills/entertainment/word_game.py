"""文字游戏 — 成语接龙 + 字谜"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import random

# 内置成语库 (精简版)
IDIOMS = [
    "一心一意", "意气风发", "发扬光大", "大器晚成", "成竹在胸",
    "胸有成竹", "竹报平安", "安居乐业", "业精于勤", "勤能补拙",
    "拙嘴笨舌", "舌战群儒", "儒雅大方", "方兴未艾", "艾草芬芳",
    "心想事成", "成人之美", "美不胜收", "收放自如", "如鱼得水",
    "水落石出", "出人意料", "料事如神", "神通广大", "大显身手",
    "手不释卷", "卷土重来", "来之不易", "易如反掌", "掌上明珠",
    "珠联璧合", "合二为一", "一目了然", "然而然之", "之乎者也",
    "马到成功", "功德无量", "量力而行", "行云流水", "水到渠成",
    "天下太平", "平步青云", "云淡风轻", "轻描淡写", "写意人生",
    "龙腾虎跃", "跃跃欲试", "试目以待", "待人接物", "物美价廉",
]


class WordGameSchema(SkillSchema):
    mode: str = Field(default="chain", description="模式: chain(成语接龙)/riddle(字谜)")
    input: str = Field(default="", description="成语接龙的起始成语，或字谜的答案")


class WordGameSkill(BaseSkill):
    name = "word_game"
    description = "文字游戏: 成语接龙、字谜"
    category = "entertainment"
    args_schema = WordGameSchema
    tags = ["成语", "接龙", "字谜", "游戏", "文字"]

    async def execute(self, **kwargs: Any) -> str:
        mode = kwargs.get("mode", "chain")
        user_input = kwargs.get("input", "").strip()

        if mode == "chain":
            if not user_input:
                starter = random.choice(IDIOMS)
                return f"成语接龙开始！\n  🎯 {starter}\n  请接「{starter[-1]}」开头的成语"

            last_char = user_input[-1]
            matches = [i for i in IDIOMS if i[0] == last_char and i != user_input]
            if matches:
                picked = random.choice(matches)
                return (
                    f"成语接龙:\n"
                    f"  你: {user_input}\n"
                    f"  我: {picked}\n"
                    f"  请接「{picked[-1]}」开头的成语"
                )
            return f"我接不上「{last_char}」开头的成语了，你赢了！🎉"

        elif mode == "riddle":
            riddles = [
                ("一口咬掉牛尾巴", "告"),
                ("人在草木中", "茶"),
                ("一加一不是二", "王"),
                ("上下合一", "卡"),
                ("一人一口", "合"),
                ("两人土上坐", "坐"),
                ("大口吞小口", "回"),
                ("半推半就", "掠"),
            ]
            r = random.choice(riddles)
            if user_input:
                for desc, ans in riddles:
                    if user_input == ans:
                        return f"字谜: {desc}\n  你的答案: {user_input}\n  ✓ 正确！"
                return f"答案不在题库中，再试试？\n  新字谜: {r[0]}"

            return f"字谜:\n  🧩 {r[0]}\n  (输入你的答案试试)"

        return "不支持的模式: chain(成语接龙)/riddle(字谜)"
