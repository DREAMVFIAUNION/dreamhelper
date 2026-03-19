"""番茄钟技能 — 时间管理助手"""

from typing import Any
from datetime import datetime, timezone, timedelta

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

CST = timezone(timedelta(hours=8))


class PomodoroSchema(SkillSchema):
    action: str = Field(description="操作: 'start'(开始), 'status'(查看), 'plan'(规划)")
    work_minutes: int = Field(default=25, description="工作时长(分钟)")
    break_minutes: int = Field(default=5, description="休息时长(分钟)")
    cycles: int = Field(default=4, description="循环次数 (action=plan)")
    task: str = Field(default="", description="任务描述")


class PomodoroTimerSkill(BaseSkill):
    name = "pomodoro_timer"
    description = "番茄钟时间管理：规划工作/休息周期，计算完成时间"
    category = "office"
    args_schema = PomodoroSchema
    tags = ["番茄钟", "时间管理", "专注", "pomodoro"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "plan")
        work = max(1, min(120, int(kwargs.get("work_minutes", 25))))
        brk = max(1, min(30, int(kwargs.get("break_minutes", 5))))
        cycles = max(1, min(12, int(kwargs.get("cycles", 4))))
        task = kwargs.get("task", "专注工作")
        now = datetime.now(CST)

        if action == "start":
            end_time = now + timedelta(minutes=work)
            return (
                f"番茄钟已启动!\n"
                f"  任务: {task}\n"
                f"  开始: {now.strftime('%H:%M')}\n"
                f"  工作: {work} 分钟\n"
                f"  结束: {end_time.strftime('%H:%M')}\n"
                f"  之后休息 {brk} 分钟"
            )

        elif action == "plan":
            lines = [f"番茄钟计划 — {task}\n"]
            current = now
            total_work = 0
            for i in range(cycles):
                work_end = current + timedelta(minutes=work)
                lines.append(f"  第{i+1}轮: {current.strftime('%H:%M')} - {work_end.strftime('%H:%M')} (工作 {work}min)")
                total_work += work
                current = work_end
                if i < cycles - 1:
                    long_break = brk * 3 if (i + 1) % 4 == 0 else brk
                    break_end = current + timedelta(minutes=long_break)
                    lines.append(f"         {current.strftime('%H:%M')} - {break_end.strftime('%H:%M')} (休息 {long_break}min)")
                    current = break_end

            lines.append(f"\n总计: {cycles} 轮 | 工作 {total_work} 分钟 | 预计 {current.strftime('%H:%M')} 完成")
            return "\n".join(lines)

        return "支持的操作: start(开始), plan(规划)"
