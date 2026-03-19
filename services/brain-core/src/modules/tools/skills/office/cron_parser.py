"""Cron 表达式解析技能 — 解读 cron 表达式含义 + 生成下次执行时间"""

from typing import Any
from datetime import datetime, timezone, timedelta

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

CST = timezone(timedelta(hours=8))

_FIELD_NAMES = ["分钟", "小时", "日", "月", "星期"]
_WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"]


def _explain_field(value: str, field_name: str) -> str:
    if value == "*":
        return f"每{field_name}"
    if "/" in value:
        parts = value.split("/")
        return f"每隔 {parts[1]} {field_name}"
    if "-" in value:
        parts = value.split("-")
        return f"{field_name} {parts[0]} 到 {parts[1]}"
    if "," in value:
        return f"{field_name} {value}"
    if field_name == "星期":
        idx = int(value) if value.isdigit() else -1
        if 0 <= idx <= 6:
            return f"星期{_WEEKDAYS[idx]}"
    return f"{field_name} {value}"


class CronParseSchema(SkillSchema):
    expression: str = Field(description="Cron 表达式，如 '0 9 * * 1-5' 或 '*/5 * * * *'")


class CronParserSkill(BaseSkill):
    name = "cron_parser"
    description = "解析 Cron 表达式：解释含义、翻译为中文描述"
    category = "office"
    args_schema = CronParseSchema
    tags = ["cron", "定时", "调度", "schedule"]

    async def execute(self, **kwargs: Any) -> str:
        expr = kwargs.get("expression", "").strip()
        if not expr:
            return "请输入 Cron 表达式"

        parts = expr.split()
        if len(parts) != 5:
            return f"Cron 表达式应有 5 个字段 (分 时 日 月 周)，收到 {len(parts)} 个"

        lines = [f"Cron 表达式: {expr}\n"]
        lines.append("字段解析:")
        descriptions = []
        for i, (val, name) in enumerate(zip(parts, _FIELD_NAMES)):
            desc = _explain_field(val, name)
            lines.append(f"  {name}: {val} → {desc}")
            descriptions.append(desc)

        # 简洁中文描述
        summary = self._summarize(parts)
        lines.append(f"\n含义: {summary}")

        # 常见示例
        lines.append("\n常见 Cron 示例:")
        lines.append("  * * * * *     → 每分钟")
        lines.append("  0 * * * *     → 每小时整点")
        lines.append("  0 9 * * 1-5   → 工作日每天 9:00")
        lines.append("  0 0 1 * *     → 每月1号 0:00")
        lines.append("  */5 * * * *   → 每5分钟")

        return "\n".join(lines)

    def _summarize(self, parts: list[str]) -> str:
        minute, hour, day, month, weekday = parts

        if all(p == "*" for p in parts):
            return "每分钟执行"
        if minute == "0" and hour == "*" and day == "*" and month == "*" and weekday == "*":
            return "每小时整点执行"
        if minute.startswith("*/"):
            return f"每 {minute.split('/')[1]} 分钟执行"
        if hour.startswith("*/"):
            return f"每 {hour.split('/')[1]} 小时执行"

        time_str = ""
        if minute != "*" and hour != "*":
            time_str = f"{hour}:{minute.zfill(2)}"
        elif hour != "*":
            time_str = f"{hour} 点"

        day_str = ""
        if weekday == "1-5":
            day_str = "工作日"
        elif weekday == "0,6":
            day_str = "周末"
        elif weekday != "*":
            day_str = f"星期{_explain_field(weekday, '星期')}"
        elif day != "*" and month == "*":
            day_str = f"每月{day}号"
        elif day != "*" and month != "*":
            day_str = f"{month}月{day}号"

        parts_str = " ".join(filter(None, [day_str, time_str]))
        return f"{parts_str} 执行" if parts_str else "自定义调度"
