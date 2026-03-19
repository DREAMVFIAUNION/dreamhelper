"""ENV 文件解析器 — 解析 .env 格式并校验"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class EnvSchema(SkillSchema):
    content: str = Field(description=".env 文件内容")


class EnvParserSkill(BaseSkill):
    name = "env_parser"
    description = "解析 .env 文件格式，提取变量并校验"
    category = "coding"
    args_schema = EnvSchema
    tags = ["env", "环境变量", "配置", "parse"]

    async def execute(self, **kwargs: Any) -> str:
        content = kwargs["content"].strip()
        if not content:
            return ".env 内容为空"

        entries = []
        errors = []
        for i, line in enumerate(content.split("\n"), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                errors.append(f"  行 {i}: 缺少 '=' → {line[:40]}")
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if not key:
                errors.append(f"  行 {i}: 空键名")
                continue
            is_secret = any(k in key.upper() for k in ["SECRET", "KEY", "PASSWORD", "TOKEN"])
            entries.append((key, val, is_secret))

        lines = [f"ENV 解析结果 ({len(entries)} 个变量):"]
        for key, val, secret in entries:
            display = "****" if secret else (val[:30] + "..." if len(val) > 30 else val) if val else "(空)"
            tag = " 🔒" if secret else ""
            lines.append(f"  {key} = {display}{tag}")

        if errors:
            lines.append(f"\n⚠ {len(errors)} 个问题:")
            lines.extend(errors)

        return "\n".join(lines)
