"""日程规划器 — 时间段冲突检测"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
from datetime import datetime


class ScheduleSchema(SkillSchema):
    events: str = Field(description="事件列表，格式: 名称|开始时间|结束时间，多个用分号分隔。时间格式 HH:MM")


class SchedulePlannerSkill(BaseSkill):
    name = "schedule_planner"
    description = "检查日程时间段是否冲突"
    category = "office"
    args_schema = ScheduleSchema
    tags = ["日程", "排期", "冲突", "schedule"]

    async def execute(self, **kwargs: Any) -> str:
        raw = kwargs["events"].strip()
        entries = []
        for item in raw.split(";"):
            parts = [p.strip() for p in item.strip().split("|")]
            if len(parts) != 3:
                continue
            name, start_s, end_s = parts
            try:
                start = datetime.strptime(start_s, "%H:%M")
                end = datetime.strptime(end_s, "%H:%M")
            except ValueError:
                return f"时间格式错误: {start_s} 或 {end_s}，请使用 HH:MM"
            entries.append((name, start, end))

        if len(entries) < 1:
            return "请至少输入1个事件，格式: 名称|开始|结束"

        entries.sort(key=lambda x: x[1])
        conflicts = []
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                n1, s1, e1 = entries[i]
                n2, s2, e2 = entries[j]
                if s2 < e1:
                    conflicts.append((n1, n2, s2.strftime("%H:%M"), min(e1, e2).strftime("%H:%M")))

        lines = ["日程安排:"]
        for name, start, end in entries:
            lines.append(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')} {name}")

        if conflicts:
            lines.append(f"\n⚠ 发现 {len(conflicts)} 个冲突:")
            for n1, n2, s, e in conflicts:
                lines.append(f"  [{n1}] 与 [{n2}] 在 {s}-{e} 重叠")
        else:
            lines.append("\n✓ 无冲突")

        return "\n".join(lines)
