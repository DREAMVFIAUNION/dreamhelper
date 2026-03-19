"""SQL 格式化器 — 美化 SQL 语句"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re


KEYWORDS = [
    "SELECT", "FROM", "WHERE", "AND", "OR", "JOIN", "LEFT JOIN", "RIGHT JOIN",
    "INNER JOIN", "OUTER JOIN", "ON", "GROUP BY", "ORDER BY", "HAVING",
    "LIMIT", "OFFSET", "INSERT INTO", "VALUES", "UPDATE", "SET", "DELETE FROM",
    "CREATE TABLE", "ALTER TABLE", "DROP TABLE", "AS", "DISTINCT", "UNION",
    "IN", "NOT IN", "BETWEEN", "LIKE", "IS NULL", "IS NOT NULL", "EXISTS",
    "CASE", "WHEN", "THEN", "ELSE", "END", "COUNT", "SUM", "AVG", "MAX", "MIN",
]


class SqlSchema(SkillSchema):
    sql: str = Field(description="SQL 语句")


class SqlFormatterSkill(BaseSkill):
    name = "sql_formatter"
    description = "格式化美化 SQL 语句"
    category = "coding"
    args_schema = SqlSchema
    tags = ["SQL", "格式化", "数据库", "format"]

    async def execute(self, **kwargs: Any) -> str:
        sql = kwargs["sql"].strip()
        if not sql:
            return "SQL 不能为空"

        # 简单格式化: 在关键字前换行
        formatted = sql
        # 规范化空白
        formatted = re.sub(r'\s+', ' ', formatted).strip()

        # 主要关键字前换行
        for kw in ["SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING",
                    "LIMIT", "OFFSET", "JOIN", "LEFT JOIN", "RIGHT JOIN",
                    "INNER JOIN", "INSERT INTO", "VALUES", "UPDATE", "SET",
                    "DELETE FROM", "UNION", "CASE", "END"]:
            formatted = re.sub(
                rf'\b({kw})\b',
                f'\n{kw}',
                formatted,
                flags=re.IGNORECASE
            )

        # AND/OR 缩进
        formatted = re.sub(r'\b(AND|OR)\b', r'\n  \1', formatted, flags=re.IGNORECASE)

        # 清理多余换行
        formatted = re.sub(r'\n\s*\n', '\n', formatted).strip()

        # 大写关键字
        for kw in KEYWORDS:
            formatted = re.sub(rf'\b{kw}\b', kw, formatted, flags=re.IGNORECASE)

        return f"格式化 SQL:\n{formatted}"
