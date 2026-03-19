"""会议纪要生成器 — 结构化会议记录模板"""

from typing import Any
from datetime import datetime
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class MeetingSchema(SkillSchema):
    title: str = Field(description="会议主题")
    attendees: str = Field(default="", description="参会人员，用逗号分隔")
    decisions: str = Field(default="", description="决议事项，用分号分隔")
    action_items: str = Field(default="", description="行动项，用分号分隔")


class MeetingMinutesSkill(BaseSkill):
    name = "meeting_minutes"
    description = "生成结构化会议纪要模板"
    category = "office"
    args_schema = MeetingSchema
    tags = ["会议", "纪要", "meeting", "记录"]

    async def execute(self, **kwargs: Any) -> str:
        title = kwargs["title"]
        attendees = kwargs.get("attendees", "")
        decisions = kwargs.get("decisions", "")
        actions = kwargs.get("action_items", "")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [
            f"═══ 会议纪要 ═══",
            f"主题: {title}",
            f"时间: {now}",
        ]

        if attendees:
            people = [p.strip() for p in attendees.split(",") if p.strip()]
            lines.append(f"参会: {', '.join(people)} ({len(people)}人)")

        lines.append("")

        if decisions:
            lines.append("【决议事项】")
            for i, d in enumerate(decisions.split(";"), 1):
                if d.strip():
                    lines.append(f"  {i}. {d.strip()}")
            lines.append("")

        if actions:
            lines.append("【行动项】")
            for i, a in enumerate(actions.split(";"), 1):
                if a.strip():
                    lines.append(f"  □ {a.strip()}")
            lines.append("")

        if not decisions and not actions:
            lines.extend([
                "【讨论要点】",
                "  1. [待补充]",
                "",
                "【决议事项】",
                "  1. [待补充]",
                "",
                "【行动项】",
                "  □ [待补充] - 负责人: [待定] - 截止: [待定]",
            ])

        lines.append(f"\n记录人: ___  |  审核: ___")
        return "\n".join(lines)
