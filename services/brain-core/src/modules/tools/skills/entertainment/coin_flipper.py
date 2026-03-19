"""抛硬币 — 随机正反面模拟"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import random


class CoinSchema(SkillSchema):
    times: int = Field(default=1, description="抛硬币次数(1-100)")


class CoinFlipperSkill(BaseSkill):
    name = "coin_flipper"
    description = "抛硬币模拟，支持多次投掷统计"
    category = "entertainment"
    args_schema = CoinSchema
    tags = ["硬币", "随机", "coin", "正反"]

    async def execute(self, **kwargs: Any) -> str:
        times = min(100, max(1, int(kwargs.get("times", 1))))
        results = [random.choice(["正面", "反面"]) for _ in range(times)]
        heads = results.count("正面")
        tails = results.count("反面")

        if times == 1:
            return f"🪙 抛硬币结果: {results[0]}！"

        return (
            f"🪙 抛硬币 {times} 次:\n"
            f"  正面: {heads} 次 ({heads/times*100:.1f}%)\n"
            f"  反面: {tails} 次 ({tails/times*100:.1f}%)\n"
            f"  序列: {''.join('正' if r == '正面' else '反' for r in results[:30])}"
            + ("..." if times > 30 else "")
        )
