"""倒计时计算器 — 计算两个日期之间的天数"""

from typing import Any
from datetime import datetime
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class CountdownSchema(SkillSchema):
    target_date: str = Field(description="目标日期，格式 YYYY-MM-DD")
    label: str = Field(default="目标日", description="事件名称(可选)")


class CountdownTimerSkill(BaseSkill):
    name = "countdown_timer"
    description = "计算从今天到目标日期的倒计时天数"
    category = "daily"
    args_schema = CountdownSchema
    tags = ["倒计时", "日期", "countdown", "天数"]

    async def execute(self, **kwargs: Any) -> str:
        target_str = kwargs["target_date"]
        label = kwargs.get("label", "目标日")
        try:
            target = datetime.strptime(target_str, "%Y-%m-%d")
        except ValueError:
            return "日期格式错误，请使用 YYYY-MM-DD"

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        delta = (target - today).days

        if delta > 0:
            return f"距离 [{label}] ({target_str}) 还有 {delta} 天"
        elif delta == 0:
            return f"今天就是 [{label}] ({target_str})！"
        else:
            return f"[{label}] ({target_str}) 已经过去了 {abs(delta)} 天"
