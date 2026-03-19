"""习惯追踪器 — 简单习惯打卡与统计"""

from typing import Any
from datetime import datetime
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import json

# 内存中的习惯存储 (生产环境应持久化)
_habits: dict[str, list[str]] = {}


class HabitSchema(SkillSchema):
    action: str = Field(description="操作: checkin(打卡)/status(状态)/list(列表)")
    habit: str = Field(default="", description="习惯名称，如: 跑步、读书、冥想")


class HabitTrackerSkill(BaseSkill):
    name = "habit_tracker"
    description = "习惯追踪: 打卡记录、连续天数统计"
    category = "daily"
    args_schema = HabitSchema
    tags = ["习惯", "打卡", "habit", "追踪"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "list")
        habit = kwargs.get("habit", "").strip()
        today = datetime.now().strftime("%Y-%m-%d")

        if action == "list":
            if not _habits:
                return "暂无习惯记录，使用 checkin 开始打卡"
            lines = ["习惯列表:"]
            for name, dates in _habits.items():
                streak = self._calc_streak(dates)
                lines.append(f"  {name}: {len(dates)} 次打卡 | 连续 {streak} 天")
            return "\n".join(lines)

        if not habit:
            return "请指定习惯名称"

        if action == "checkin":
            if habit not in _habits:
                _habits[habit] = []
            if today in _habits[habit]:
                return f"今天已经打过 [{habit}] 卡了！"
            _habits[habit].append(today)
            streak = self._calc_streak(_habits[habit])
            return f"打卡成功！\n  习惯: {habit}\n  日期: {today}\n  连续: {streak} 天\n  累计: {len(_habits[habit])} 次"

        elif action == "status":
            if habit not in _habits:
                return f"未找到习惯 [{habit}]"
            dates = _habits[habit]
            streak = self._calc_streak(dates)
            checked_today = today in dates
            return (
                f"习惯状态 [{habit}]:\n"
                f"  今日: {'已打卡 ✓' if checked_today else '未打卡'}\n"
                f"  连续: {streak} 天\n"
                f"  累计: {len(dates)} 次"
            )

        return "不支持的操作，可用: checkin/status/list"

    def _calc_streak(self, dates: list[str]) -> int:
        if not dates:
            return 0
        sorted_dates = sorted(dates, reverse=True)
        streak = 1
        for i in range(len(sorted_dates) - 1):
            d1 = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
            d2 = datetime.strptime(sorted_dates[i + 1], "%Y-%m-%d")
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        return streak
