"""甘特图生成器 — ASCII/Mermaid 格式"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class GanttSchema(SkillSchema):
    tasks: str = Field(description="任务列表，格式: 名称|开始周|持续周，多个用分号分隔。如: 设计|1|2;开发|2|4;测试|5|2")
    format: str = Field(default="ascii", description="格式: ascii/mermaid")


class GanttChartSkill(BaseSkill):
    name = "gantt_chart"
    description = "生成 ASCII 或 Mermaid 格式甘特图"
    category = "office"
    args_schema = GanttSchema
    tags = ["甘特图", "gantt", "项目", "排期"]

    async def execute(self, **kwargs: Any) -> str:
        raw = kwargs["tasks"].strip()
        fmt = kwargs.get("format", "ascii")
        entries = []

        for item in raw.split(";"):
            parts = [p.strip() for p in item.strip().split("|")]
            if len(parts) != 3:
                continue
            try:
                entries.append((parts[0], int(parts[1]), int(parts[2])))
            except ValueError:
                continue

        if not entries:
            return "请输入任务，格式: 名称|开始周|持续周;..."

        if fmt == "mermaid":
            lines = ["```mermaid", "gantt", "  title 项目甘特图", "  dateFormat YYYY-MM-DD"]
            for name, start, dur in entries:
                lines.append(f"  {name} : w{start}, {dur}w")
            lines.append("```")
            return "Mermaid 甘特图:\n" + "\n".join(lines)

        # ASCII
        max_week = max(s + d for _, s, d in entries)
        max_name = max(len(n) for n, _, _ in entries)
        header = " " * (max_name + 2) + "".join(f"W{i:<3}" for i in range(1, max_week + 1))
        lines = [f"甘特图 ({len(entries)} 个任务):", header]

        for name, start, dur in entries:
            bar = " " * ((start - 1) * 4) + "█" * (dur * 4 - 1) + " "
            lines.append(f"{name:<{max_name}}  {bar}")

        return "\n".join(lines)
