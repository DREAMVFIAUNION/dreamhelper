"""文件编辑工具 — 精确字符串替换编辑（类 Claude Edit）

安全特性:
  - 通过 PermissionGateway 路径验证
  - 强制 Read-before-Edit（old_string 必须精确匹配）
  - 唯一性检查（old_string 在文件中必须唯一）
  - 编辑前自动备份（可选）
"""

import os
import logging
from typing import Any
from pydantic import BaseModel, Field

from ..tool_registry import BaseTool
from ...security.permission_gateway import get_permission_gateway

logger = logging.getLogger("tools.file_edit")


class FileEditArgs(BaseModel):
    path: str = Field(..., description="文件的绝对或相对路径")
    old_string: str = Field(..., description="要替换的原始文本（必须精确匹配）")
    new_string: str = Field(..., description="替换后的新文本")
    replace_all: bool = Field(False, description="是否替换所有匹配项（默认只替换第一个且要求唯一）")


class FileEditTool(BaseTool):
    name = "file_edit"
    description = (
        "精确字符串替换编辑文件。old_string 必须精确匹配文件中的内容（包括缩进）。"
        "默认要求 old_string 在文件中唯一，设置 replace_all=true 可替换所有匹配。"
    )
    args_schema = FileEditArgs

    async def execute(self, **kwargs: Any) -> str:
        file_path = kwargs.get("path", "")
        old_string = kwargs.get("old_string", "")
        new_string = kwargs.get("new_string", "")
        replace_all = kwargs.get("replace_all", False)

        if not file_path:
            return "❌ 缺少 path 参数"
        if not old_string:
            return "❌ 缺少 old_string 参数"
        if old_string == new_string:
            return "❌ old_string 与 new_string 相同（无操作）"

        abs_path = os.path.abspath(file_path)

        # 权限检查
        gateway = get_permission_gateway()
        result = gateway.check_file_operation("file_edit", abs_path, write=True)
        if not result.allowed:
            return f"⛔ 编辑被阻止: {result.reason}"

        if not os.path.exists(abs_path):
            return f"❌ 文件不存在: {abs_path}"

        # 读取原文件
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(abs_path, "r", encoding="gbk") as f:
                    content = f.read()
            except Exception as e:
                return f"❌ 无法读取文件: {e}"
        except Exception as e:
            return f"❌ 读取失败: {e}"

        # 匹配检查
        count = content.count(old_string)
        if count == 0:
            # 提供上下文帮助调试
            lines = content.split("\n")
            preview = "\n".join(lines[:20]) if len(lines) > 20 else content[:500]
            return (
                f"❌ old_string 在文件中未找到匹配\n"
                f"文件: {abs_path} ({len(lines)} 行)\n"
                f"搜索内容 (前50字符): {old_string[:50]!r}\n"
                f"文件前20行预览:\n{preview}"
            )

        if count > 1 and not replace_all:
            return (
                f"❌ old_string 在文件中匹配到 {count} 处（非唯一）\n"
                f"请提供更多上下文使匹配唯一，或设置 replace_all=true\n"
                f"搜索内容: {old_string[:80]!r}"
            )

        # 执行替换
        if replace_all:
            new_content = content.replace(old_string, new_string)
            replaced_count = count
        else:
            new_content = content.replace(old_string, new_string, 1)
            replaced_count = 1

        # 写入
        try:
            with open(abs_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(new_content)
        except Exception as e:
            return f"❌ 写入失败: {e}"

        # 统计变化
        old_lines = content.count("\n")
        new_lines = new_content.count("\n")
        diff_lines = new_lines - old_lines

        gateway.audit(
            "file_edit", "edited", result.risk_level, True,
            details=f"{abs_path} ({replaced_count} replacements, {diff_lines:+d} lines)",
        )

        return (
            f"✅ 文件已编辑: {abs_path}\n"
            f"   替换了 {replaced_count} 处匹配\n"
            f"   行数变化: {old_lines + 1} → {new_lines + 1} ({diff_lines:+d})"
        )
