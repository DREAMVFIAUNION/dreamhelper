"""小费/AA计算器 — 精确分账"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import math


class TipSchema(SkillSchema):
    amount: float = Field(description="账单金额")
    tip_percent: float = Field(default=15, description="小费百分比(默认15%)")
    people: int = Field(default=1, description="分账人数(默认1)")


class TipCalculatorSkill(BaseSkill):
    name = "tip_calculator"
    description = "计算小费和AA分账金额"
    category = "daily"
    args_schema = TipSchema
    tags = ["小费", "AA", "分账", "tip", "账单"]

    async def execute(self, **kwargs: Any) -> str:
        amount = float(kwargs["amount"])
        tip_pct = float(kwargs.get("tip_percent", 15))
        people = int(kwargs.get("people", 1))

        if amount <= 0:
            return "账单金额必须为正数"
        if people < 1:
            return "人数至少为1"

        tip = amount * tip_pct / 100
        total = amount + tip
        per_person = math.ceil(total / people * 100) / 100

        lines = [
            f"账单计算结果:",
            f"  原始金额: ¥{amount:.2f}",
            f"  小费({tip_pct:.0f}%): ¥{tip:.2f}",
            f"  总计: ¥{total:.2f}",
        ]
        if people > 1:
            lines.append(f"  每人({people}人): ¥{per_person:.2f}")

        return "\n".join(lines)
