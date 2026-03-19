"""日期时间计算器 — 日期加减、工作日计算"""

from typing import Any
from datetime import datetime, timedelta
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class DatetimeSchema(SkillSchema):
    date: str = Field(default="today", description="起始日期(YYYY-MM-DD)，默认今天")
    operation: str = Field(default="info", description="操作: info(信息)/add_days(加天)/weekday(工作日)/diff(差值)")
    value: str = Field(default="0", description="天数(add_days用)或第二个日期(diff用)")


class DatetimeCalcSkill(BaseSkill):
    name = "datetime_calc"
    description = "日期时间计算: 日期信息、加减天数、工作日判断、日期差值"
    category = "daily"
    args_schema = DatetimeSchema
    tags = ["日期", "时间", "工作日", "datetime", "计算"]

    async def execute(self, **kwargs: Any) -> str:
        date_str = kwargs.get("date", "today")
        op = kwargs.get("operation", "info")
        value = kwargs.get("value", "0")

        try:
            if date_str == "today":
                dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return "日期格式错误，请使用 YYYY-MM-DD"

        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        wd = weekdays[dt.weekday()]
        is_workday = dt.weekday() < 5

        if op == "info":
            day_of_year = dt.timetuple().tm_yday
            week_num = dt.isocalendar()[1]
            return (
                f"日期信息:\n"
                f"  日期: {dt.strftime('%Y-%m-%d')} {wd}\n"
                f"  工作日: {'是' if is_workday else '否(周末)'}\n"
                f"  年内第 {day_of_year} 天 | 第 {week_num} 周"
            )

        elif op == "add_days":
            try:
                days = int(value)
            except ValueError:
                return "天数必须为整数"
            result = dt + timedelta(days=days)
            rwd = weekdays[result.weekday()]
            return f"日期计算:\n  {dt.strftime('%Y-%m-%d')} {'+' if days >= 0 else ''}{days}天\n  = {result.strftime('%Y-%m-%d')} {rwd}"

        elif op == "weekday":
            # 计算接下来N个工作日
            try:
                n = int(value)
            except ValueError:
                n = 5
            current = dt
            count = 0
            while count < n:
                current += timedelta(days=1)
                if current.weekday() < 5:
                    count += 1
            return f"从 {dt.strftime('%Y-%m-%d')} 起第 {n} 个工作日:\n  = {current.strftime('%Y-%m-%d')} {weekdays[current.weekday()]}"

        elif op == "diff":
            try:
                dt2 = datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return "第二个日期格式错误，请使用 YYYY-MM-DD"
            delta = (dt2 - dt).days
            return f"日期差值:\n  {dt.strftime('%Y-%m-%d')} → {dt2.strftime('%Y-%m-%d')}\n  = {abs(delta)} 天 ({abs(delta)//7} 周 {abs(delta)%7} 天)"

        return "不支持的操作，可用: info/add_days/weekday/diff"
