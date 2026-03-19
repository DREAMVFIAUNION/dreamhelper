"""CSV 转表格 — CSV→Markdown/ASCII 表格"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import csv
import io


class CsvTableSchema(SkillSchema):
    data: str = Field(description="CSV 格式文本")
    format: str = Field(default="markdown", description="输出格式: markdown/ascii")


class CsvToTableSkill(BaseSkill):
    name = "csv_to_table"
    description = "将 CSV 数据转换为 Markdown 或 ASCII 表格"
    category = "document"
    args_schema = CsvTableSchema
    tags = ["CSV", "表格", "Markdown", "转换"]

    async def execute(self, **kwargs: Any) -> str:
        data = kwargs["data"].strip()
        fmt = kwargs.get("format", "markdown")

        reader = csv.reader(io.StringIO(data))
        rows = list(reader)
        if not rows:
            return "CSV 数据为空"

        headers = rows[0]
        body = rows[1:]

        # 计算列宽
        widths = [len(h) for h in headers]
        for row in body:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(cell))

        if fmt == "ascii":
            sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
            lines = [sep]
            lines.append("|" + "|".join(f" {h:<{widths[i]}} " for i, h in enumerate(headers)) + "|")
            lines.append(sep)
            for row in body:
                cells = []
                for i in range(len(headers)):
                    val = row[i] if i < len(row) else ""
                    cells.append(f" {val:<{widths[i]}} ")
                lines.append("|" + "|".join(cells) + "|")
            lines.append(sep)
            return f"ASCII 表格:\n" + "\n".join(lines)

        # markdown
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        for row in body:
            cells = [row[i] if i < len(row) else "" for i in range(len(headers))]
            lines.append("| " + " | ".join(cells) + " |")

        return f"Markdown 表格:\n" + "\n".join(lines)
