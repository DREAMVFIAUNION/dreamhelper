"""Diff/Patch 工具 — 生成和应用补丁"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import difflib


class DiffPatchSchema(SkillSchema):
    action: str = Field(description="操作: diff(生成补丁)/apply(应用补丁)")
    original: str = Field(description="原始文本")
    modified: str = Field(default="", description="修改后文本(diff时需要)")
    patch: str = Field(default="", description="补丁内容(apply时需要)")


class DiffPatchSkill(BaseSkill):
    name = "diff_patch"
    description = "生成 unified diff 补丁或应用补丁"
    category = "coding"
    args_schema = DiffPatchSchema
    tags = ["diff", "patch", "补丁", "差异"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "diff")
        original = kwargs.get("original", "")
        modified = kwargs.get("modified", "")
        patch_text = kwargs.get("patch", "")

        if action == "diff":
            if not modified:
                return "生成补丁需要提供修改后文本"
            orig_lines = original.splitlines(keepends=True)
            mod_lines = modified.splitlines(keepends=True)
            diff = list(difflib.unified_diff(
                orig_lines, mod_lines,
                fromfile="original", tofile="modified"
            ))
            if not diff:
                return "两个文本完全相同，无差异"
            patch_out = "".join(diff)
            added = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
            removed = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))
            return f"Unified Diff (+{added}/-{removed}):\n{patch_out}"

        elif action == "apply":
            if not patch_text:
                return "应用补丁需要提供补丁内容"
            # 简单逐行应用
            orig_lines = original.splitlines()
            result = list(orig_lines)
            offset = 0
            for line in patch_text.splitlines():
                if line.startswith('-') and not line.startswith('---'):
                    content = line[1:].strip()
                    for i, r in enumerate(result):
                        if r.strip() == content:
                            result.pop(i)
                            offset -= 1
                            break
                elif line.startswith('+') and not line.startswith('+++'):
                    content = line[1:]
                    result.append(content)
            return f"应用补丁结果:\n" + "\n".join(result)

        return "不支持的操作: diff/apply"
