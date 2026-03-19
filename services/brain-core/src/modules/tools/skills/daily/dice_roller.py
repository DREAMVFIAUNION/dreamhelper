"""骰子模拟器 — 支持 DnD 语法 (如 2d6+3)"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import random
import re


class DiceSchema(SkillSchema):
    expression: str = Field(description="骰子表达式，如: d6, 2d20, 3d8+5, d100")


class DiceRollerSkill(BaseSkill):
    name = "dice_roller"
    description = "掷骰子，支持 DnD 语法: NdX+M"
    category = "daily"
    args_schema = DiceSchema
    tags = ["骰子", "dice", "随机", "DnD", "游戏"]

    async def execute(self, **kwargs: Any) -> str:
        expr = kwargs["expression"].strip().lower().replace(" ", "")

        m = re.match(r"^(\d*)d(\d+)([+-]\d+)?$", expr)
        if not m:
            return f"无法解析骰子表达式: {expr}\n格式: NdX+M (例: 2d6+3, d20, 3d8)"

        count = int(m.group(1)) if m.group(1) else 1
        sides = int(m.group(2))
        modifier = int(m.group(3)) if m.group(3) else 0

        if count < 1 or count > 100:
            return "骰子数量: 1-100"
        if sides < 2 or sides > 1000:
            return "面数: 2-1000"

        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier

        mod_str = f" + {modifier}" if modifier > 0 else f" - {abs(modifier)}" if modifier < 0 else ""

        lines = [f"掷骰结果 [{expr}]:"]
        if count <= 20:
            lines.append(f"  各骰: {', '.join(str(r) for r in rolls)}")
        lines.append(f"  骰子合计: {sum(rolls)}{mod_str}")
        lines.append(f"  最终结果: {total}")

        if count > 1:
            lines.append(f"  最高: {max(rolls)} | 最低: {min(rolls)} | 平均: {sum(rolls)/count:.1f}")

        return "\n".join(lines)
