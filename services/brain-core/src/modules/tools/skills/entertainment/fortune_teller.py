"""运势占卜 — 确定性种子的每日运势"""

from typing import Any
from datetime import datetime
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import hashlib

ASPECTS = ["事业", "爱情", "财运", "健康", "学业"]
LEVELS = ["大吉", "吉", "小吉", "中平", "小凶"]
ADVICE = [
    "今天适合大胆尝试新事物",
    "保持耐心，好运正在路上",
    "注意与人沟通时的措辞",
    "适合整理思绪，制定计划",
    "多关注身边人的感受",
    "今天的努力将在未来开花结果",
    "避免冲动消费，理性决策",
    "适合学习新知识或技能",
    "保持乐观，困难只是暂时的",
    "今天是社交的好日子",
]


class FortuneSchema(SkillSchema):
    name: str = Field(default="匿名", description="你的名字(影响结果)")


class FortuneTellerSkill(BaseSkill):
    name = "fortune_teller"
    description = "每日运势占卜，基于名字和日期生成个性化运势"
    category = "entertainment"
    args_schema = FortuneSchema
    tags = ["运势", "占卜", "fortune", "每日"]

    async def execute(self, **kwargs: Any) -> str:
        name = kwargs.get("name", "匿名")
        today = datetime.now().strftime("%Y-%m-%d")
        seed = hashlib.md5(f"{name}{today}".encode()).hexdigest()

        lines = [f"🔮 {name} 的今日运势 ({today}):", ""]
        overall = int(seed[0], 16) % 5
        lines.append(f"  综合运势: {'⭐' * (5 - overall)} {LEVELS[overall]}")
        lines.append("")

        for i, aspect in enumerate(ASPECTS):
            val = int(seed[i + 1], 16) % 5
            stars = "⭐" * (5 - val)
            lines.append(f"  {aspect}: {stars} {LEVELS[val]}")

        advice_idx = int(seed[8:10], 16) % len(ADVICE)
        lines.append(f"\n  💡 建议: {ADVICE[advice_idx]}")

        lucky_num = int(seed[10:12], 16) % 100
        lucky_color = ["红色", "蓝色", "绿色", "紫色", "金色", "白色"][int(seed[12], 16) % 6]
        lines.append(f"  🍀 幸运数字: {lucky_num} | 幸运颜色: {lucky_color}")

        return "\n".join(lines)
