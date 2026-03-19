"""随机生成器技能 — 随机数/UUID/颜色/抽签"""

import random
import uuid
from typing import Any

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class RandomGenSchema(SkillSchema):
    action: str = Field(
        description="操作: 'number'(随机数), 'uuid'(UUID), 'color'(随机颜色), 'pick'(从列表抽取), 'dice'(掷骰子)"
    )
    min_val: int = Field(default=1, description="最小值 (action=number)")
    max_val: int = Field(default=100, description="最大值 (action=number)")
    count: int = Field(default=1, description="生成数量")
    items: str = Field(default="", description="逗号分隔的选项列表 (action=pick)")
    sides: int = Field(default=6, description="骰子面数 (action=dice)")


class RandomGeneratorSkill(BaseSkill):
    name = "random_generator"
    description = "随机生成器：随机数、UUID、随机颜色、从列表抽取、掷骰子"
    category = "daily"
    args_schema = RandomGenSchema
    tags = ["随机", "UUID", "骰子", "抽签", "random"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "number")
        count = max(1, min(10, int(kwargs.get("count", 1))))

        if action == "number":
            lo = int(kwargs.get("min_val", 1))
            hi = int(kwargs.get("max_val", 100))
            nums = [random.randint(lo, hi) for _ in range(count)]
            return f"随机数 [{lo}, {hi}]: {', '.join(map(str, nums))}"

        elif action == "uuid":
            uuids = [str(uuid.uuid4()) for _ in range(count)]
            return "UUID:\n" + "\n".join(f"  {i+1}. {u}" for i, u in enumerate(uuids))

        elif action == "color":
            colors = []
            for _ in range(count):
                r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
                colors.append(f"#{r:02x}{g:02x}{b:02x} (rgb({r},{g},{b}))")
            return "随机颜色:\n" + "\n".join(f"  {i+1}. {c}" for i, c in enumerate(colors))

        elif action == "pick":
            items_str = kwargs.get("items", "")
            items = [i.strip() for i in items_str.split(",") if i.strip()]
            if not items:
                return "请提供选项列表（逗号分隔）"
            picks = [random.choice(items) for _ in range(count)]
            return f"从 {len(items)} 个选项中抽取: {', '.join(picks)}"

        elif action == "dice":
            sides = max(2, int(kwargs.get("sides", 6)))
            rolls = [random.randint(1, sides) for _ in range(count)]
            total = sum(rolls)
            return f"掷 {count}d{sides}: {rolls} (合计: {total})"

        return f"未知操作: {action}"
