"""决策助手 — 加权随机选择"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import random


class DecisionSchema(SkillSchema):
    options: str = Field(description="选项列表，用逗号分隔，如: 吃火锅,吃烧烤,吃面")
    weights: str = Field(default="", description="权重列表(可选)，用逗号分隔，如: 3,2,1")


class DecisionMakerSkill(BaseSkill):
    name = "decision_maker"
    description = "帮你做选择！支持加权随机决策"
    category = "daily"
    args_schema = DecisionSchema
    tags = ["决策", "选择", "随机", "decision"]

    async def execute(self, **kwargs: Any) -> str:
        raw = kwargs["options"].strip()
        options = [o.strip() for o in raw.split(",") if o.strip()]

        if len(options) < 2:
            return "至少需要2个选项(用逗号分隔)"

        weights_raw = kwargs.get("weights", "").strip()
        if weights_raw:
            try:
                weights = [float(w) for w in weights_raw.split(",")]
                if len(weights) != len(options):
                    return f"权重数量({len(weights)})与选项数量({len(options)})不匹配"
            except ValueError:
                return "权重格式错误，请用逗号分隔的数字"
        else:
            weights = [1.0] * len(options)

        total = sum(weights)
        probs = [w / total * 100 for w in weights]
        choice = random.choices(options, weights=weights, k=1)[0]

        lines = ["决策结果:", f"  🎯 选择: {choice}", "", "  各选项概率:"]
        for opt, prob in zip(options, probs):
            marker = " ← 中选" if opt == choice else ""
            lines.append(f"    {opt}: {prob:.1f}%{marker}")

        return "\n".join(lines)
