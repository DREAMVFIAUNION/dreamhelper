"""CSV 分析器 — 解析CSV文本并提供统计"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import csv
import io


class CsvSchema(SkillSchema):
    data: str = Field(description="CSV 格式文本数据")
    operation: str = Field(default="summary", description="操作: summary(摘要)/head(前几行)/stats(数值统计)")


class CsvAnalyzerSkill(BaseSkill):
    name = "csv_analyzer"
    description = "解析 CSV 数据，提供摘要、预览和数值统计"
    category = "office"
    args_schema = CsvSchema
    tags = ["CSV", "数据", "分析", "表格"]

    async def execute(self, **kwargs: Any) -> str:
        data = kwargs["data"].strip()
        op = kwargs.get("operation", "summary")

        reader = csv.reader(io.StringIO(data))
        rows = list(reader)
        if not rows:
            return "CSV 数据为空"

        headers = rows[0]
        body = rows[1:]

        if op == "head":
            lines = ["CSV 预览 (前5行):"]
            lines.append(" | ".join(headers))
            lines.append("-" * 40)
            for row in body[:5]:
                lines.append(" | ".join(row))
            return "\n".join(lines)

        if op == "stats":
            lines = [f"CSV 数值统计 ({len(body)} 行):"]
            for ci, h in enumerate(headers):
                nums = []
                for row in body:
                    if ci < len(row):
                        try:
                            nums.append(float(row[ci]))
                        except ValueError:
                            pass
                if nums:
                    lines.append(f"  {h}: min={min(nums):.2f} max={max(nums):.2f} avg={sum(nums)/len(nums):.2f} ({len(nums)} 个数值)")
            if len(lines) == 1:
                lines.append("  未找到数值列")
            return "\n".join(lines)

        # summary
        return (
            f"CSV 摘要:\n"
            f"  列数: {len(headers)}\n"
            f"  行数: {len(body)} (不含表头)\n"
            f"  列名: {', '.join(headers)}\n"
            f"  首行: {', '.join(body[0]) if body else '(空)'}"
        )
