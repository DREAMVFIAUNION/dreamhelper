"""BMI 计算器技能 — 体质指数计算 + 健康评估"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class BMISchema(SkillSchema):
    height_cm: float = Field(description="身高(厘米)")
    weight_kg: float = Field(description="体重(公斤)")


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "偏瘦 — 建议适当增加营养摄入"
    elif bmi < 24:
        return "正常 — 继续保持健康生活方式"
    elif bmi < 28:
        return "偏胖 — 建议适当运动和控制饮食"
    else:
        return "肥胖 — 建议咨询医生制定健康计划"


class BMICalculatorSkill(BaseSkill):
    name = "bmi_calculator"
    description = "计算 BMI 体质指数，给出健康评估和建议"
    category = "daily"
    args_schema = BMISchema
    tags = ["BMI", "健康", "体重", "health"]

    async def execute(self, **kwargs: Any) -> str:
        height_cm = float(kwargs["height_cm"])
        weight_kg = float(kwargs["weight_kg"])

        if height_cm <= 0 or weight_kg <= 0:
            return "身高和体重必须为正数"

        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        category = _bmi_category(bmi)

        ideal_low = 18.5 * (height_m ** 2)
        ideal_high = 24 * (height_m ** 2)

        return (
            f"BMI 计算结果:\n"
            f"  身高: {height_cm:.1f} cm | 体重: {weight_kg:.1f} kg\n"
            f"  BMI: {bmi:.1f}\n"
            f"  评估: {category}\n"
            f"  正常体重范围: {ideal_low:.1f} - {ideal_high:.1f} kg"
        )
