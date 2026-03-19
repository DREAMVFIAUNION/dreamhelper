"""文本差异比较 — unified diff"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import difflib


class DiffSchema(SkillSchema):
    text1: str = Field(description="原始文本")
    text2: str = Field(description="修改后文本")
    mode: str = Field(default="unified", description="模式: unified(统一差异)/side(并排)")


class TextDiffSkill(BaseSkill):
    name = "text_diff"
    description = "比较两段文本的差异，支持统一差异格式"
    category = "document"
    args_schema = DiffSchema
    tags = ["差异", "比较", "diff", "对比"]

    async def execute(self, **kwargs: Any) -> str:
        t1 = kwargs["text1"].splitlines(keepends=True)
        t2 = kwargs["text2"].splitlines(keepends=True)
        mode = kwargs.get("mode", "unified")

        if mode == "side":
            result = list(difflib.ndiff(t1, t2))
            added = sum(1 for l in result if l.startswith('+ '))
            removed = sum(1 for l in result if l.startswith('- '))
            output = ''.join(result[:50])
            return f"差异比较 (并排):\n  新增: {added} 行 | 删除: {removed} 行\n\n{output}"

        diff = list(difflib.unified_diff(t1, t2, fromfile='原始', tofile='修改', lineterm=''))
        if not diff:
            return "两段文本完全相同，无差异"

        added = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
        removed = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))
        output = '\n'.join(diff[:60])

        return f"差异比较:\n  新增: {added} 行 | 删除: {removed} 行\n\n{output}"
