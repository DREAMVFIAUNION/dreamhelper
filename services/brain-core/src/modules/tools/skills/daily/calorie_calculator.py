"""卡路里计算器 — Mifflin-St Jeor 基础代谢率"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class CalorieSchema(SkillSchema):
    gender: str = Field(description="性别: male 或 female")
    age: int = Field(description="年龄(岁)")
    height_cm: float = Field(description="身高(厘米)")
    weight_kg: float = Field(description="体重(公斤)")
    activity: str = Field(default="moderate", description="活动量: sedentary/light/moderate/active/very_active")


ACTIVITY_FACTORS = {
    "sedentary": (1.2, "久坐"),
    "light": (1.375, "轻度运动"),
    "moderate": (1.55, "中度运动"),
    "active": (1.725, "高度运动"),
    "very_active": (1.9, "极高运动"),
}


class CalorieCalculatorSkill(BaseSkill):
    name = "calorie_calculator"
    description = "计算每日基础代谢率(BMR)和总热量需求(TDEE)"
    category = "daily"
    args_schema = CalorieSchema
    tags = ["卡路里", "热量", "BMR", "TDEE", "健康"]

    async def execute(self, **kwargs: Any) -> str:
        gender = kwargs["gender"].lower()
        age = int(kwargs["age"])
        h = float(kwargs["height_cm"])
        w = float(kwargs["weight_kg"])
        act = kwargs.get("activity", "moderate")

        if gender not in ("male", "female"):
            return "性别请输入 male 或 female"

        if gender == "male":
            bmr = 10 * w + 6.25 * h - 5 * age + 5
        else:
            bmr = 10 * w + 6.25 * h - 5 * age - 161

        factor, label = ACTIVITY_FACTORS.get(act, (1.55, "中度运动"))
        tdee = bmr * factor

        return (
            f"热量计算结果:\n"
            f"  性别: {'男' if gender == 'male' else '女'} | 年龄: {age}岁\n"
            f"  身高: {h:.0f}cm | 体重: {w:.1f}kg\n"
            f"  活动量: {label}\n"
            f"  ─────────────\n"
            f"  基础代谢率(BMR): {bmr:.0f} kcal/天\n"
            f"  总热量需求(TDEE): {tdee:.0f} kcal/天\n"
            f"  减脂建议: {tdee - 500:.0f} kcal/天\n"
            f"  增肌建议: {tdee + 300:.0f} kcal/天"
        )
