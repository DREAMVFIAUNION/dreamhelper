"""时间追踪器 — 工时记录与汇总"""

from typing import Any
from datetime import datetime
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

_records: list[dict] = []


class TimeSchema(SkillSchema):
    action: str = Field(description="操作: log(记录)/summary(汇总)/clear(清空)")
    task: str = Field(default="", description="任务名称(log时必填)")
    hours: float = Field(default=0, description="工时(小时)")


class TimeTrackerSkill(BaseSkill):
    name = "time_tracker"
    description = "工时记录: 记录任务耗时并汇总统计"
    category = "office"
    args_schema = TimeSchema
    tags = ["时间", "工时", "记录", "time"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "summary")
        task = kwargs.get("task", "").strip()
        hours = float(kwargs.get("hours", 0))

        if action == "log":
            if not task:
                return "请指定任务名称"
            if hours <= 0:
                return "工时必须为正数"
            _records.append({"task": task, "hours": hours, "date": datetime.now().strftime("%Y-%m-%d")})
            return f"已记录: {task} — {hours:.1f}h\n累计 {len(_records)} 条记录"

        elif action == "summary":
            if not _records:
                return "暂无工时记录"
            by_task: dict[str, float] = {}
            for r in _records:
                by_task[r["task"]] = by_task.get(r["task"], 0) + r["hours"]
            total = sum(by_task.values())
            lines = [f"工时汇总 ({len(_records)} 条记录):"]
            for t, h in sorted(by_task.items(), key=lambda x: -x[1]):
                pct = h / total * 100
                lines.append(f"  {t}: {h:.1f}h ({pct:.0f}%)")
            lines.append(f"  ─────\n  总计: {total:.1f}h")
            return "\n".join(lines)

        elif action == "clear":
            count = len(_records)
            _records.clear()
            return f"已清空 {count} 条工时记录"

        return "不支持的操作: log/summary/clear"
