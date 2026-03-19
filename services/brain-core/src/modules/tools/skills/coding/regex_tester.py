"""正则表达式测试器 — 测试正则并高亮匹配"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re


class RegexTestSchema(SkillSchema):
    pattern: str = Field(description="正则表达式")
    text: str = Field(description="测试文本")
    flags: str = Field(default="", description="标志: i(忽略大小写)/m(多行)/s(dotall)，可组合如 im")


class RegexTesterSkill(BaseSkill):
    name = "regex_tester"
    description = "正则表达式测试器: 测试匹配、显示分组、统计结果"
    category = "coding"
    args_schema = RegexTestSchema
    tags = ["正则", "regex", "测试", "匹配"]

    async def execute(self, **kwargs: Any) -> str:
        pattern = kwargs["pattern"]
        text = kwargs["text"]
        flags_str = kwargs.get("flags", "")

        flags = 0
        if "i" in flags_str:
            flags |= re.IGNORECASE
        if "m" in flags_str:
            flags |= re.MULTILINE
        if "s" in flags_str:
            flags |= re.DOTALL

        try:
            compiled = re.compile(pattern, flags)
        except re.error as e:
            return f"正则表达式错误: {e}"

        matches = list(compiled.finditer(text))
        if not matches:
            return f"正则: /{pattern}/{''.join(flags_str)}\n未匹配到任何内容"

        lines = [
            f"正则测试: /{pattern}/{''.join(flags_str)}",
            f"匹配数: {len(matches)}",
            "",
        ]

        for i, m in enumerate(matches[:15]):
            lines.append(f"  匹配 {i+1}: \"{m.group()}\" (位置 {m.start()}-{m.end()})")
            if m.groups():
                for gi, g in enumerate(m.groups(), 1):
                    lines.append(f"    分组 {gi}: \"{g}\"")

        if len(matches) > 15:
            lines.append(f"  ... 还有 {len(matches) - 15} 个匹配")

        return "\n".join(lines)
