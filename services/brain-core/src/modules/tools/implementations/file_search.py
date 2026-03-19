"""文件搜索工具 — Glob 模式文件搜索（类 fd）

安全特性:
  - 通过 PermissionGateway 路径验证
  - 结果数量上限（默认50）
  - 自动排除 .git, node_modules, __pycache__
"""

import os
import fnmatch
import logging
from typing import Any
from pydantic import BaseModel, Field

from ..tool_registry import BaseTool
from ...security.permission_gateway import get_permission_gateway

logger = logging.getLogger("tools.file_search")

# 默认排除目录
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".next", ".nuxt",
    "dist", "build", ".venv", "venv", ".tox", ".mypy_cache",
    ".pytest_cache", "coverage", ".turbo",
}


class FileSearchArgs(BaseModel):
    pattern: str = Field(..., description="搜索模式（glob格式，如 *.py, **/*.tsx）")
    directory: str = Field(".", description="搜索起始目录（默认当前目录）")
    max_results: int = Field(50, description="最大结果数（默认50）")
    type: str = Field("any", description="类型过滤: file, directory, any")


class FileSearchTool(BaseTool):
    name = "file_search"
    description = (
        "搜索文件和目录。使用 glob 模式匹配文件名。"
        "自动排除 .git/node_modules/__pycache__ 等。返回匹配路径列表。"
    )
    args_schema = FileSearchArgs

    async def execute(self, **kwargs: Any) -> str:
        pattern = kwargs.get("pattern", "")
        directory = kwargs.get("directory", ".")
        max_results = min(kwargs.get("max_results", 50), 200)
        type_filter = kwargs.get("type", "any")

        if not pattern:
            return "❌ 缺少 pattern 参数"

        abs_dir = os.path.abspath(directory)

        # 权限检查
        gateway = get_permission_gateway()
        result = gateway.check_file_operation("file_search", abs_dir, write=False)
        if not result.allowed:
            return f"⛔ 搜索被阻止: {result.reason}"

        if not os.path.isdir(abs_dir):
            return f"❌ 目录不存在: {abs_dir}"

        # 搜索
        matches = []
        try:
            for root, dirs, files in os.walk(abs_dir):
                # 排除目录
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

                # 根据类型过滤
                if type_filter in ("file", "any"):
                    for name in files:
                        if fnmatch.fnmatch(name, pattern):
                            rel_path = os.path.relpath(os.path.join(root, name), abs_dir)
                            size = os.path.getsize(os.path.join(root, name))
                            matches.append(("file", rel_path, size))
                            if len(matches) >= max_results:
                                break

                if type_filter in ("directory", "any"):
                    for name in dirs:
                        if fnmatch.fnmatch(name, pattern):
                            rel_path = os.path.relpath(os.path.join(root, name), abs_dir)
                            # Count items in directory
                            try:
                                items = len(os.listdir(os.path.join(root, name)))
                            except OSError:
                                items = 0
                            matches.append(("dir", rel_path, items))
                            if len(matches) >= max_results:
                                break

                if len(matches) >= max_results:
                    break

        except PermissionError:
            return f"⚠️ 部分目录无访问权限"
        except Exception as e:
            return f"❌ 搜索失败: {e}"

        if not matches:
            return f"未找到匹配 '{pattern}' 的文件（搜索目录: {abs_dir}）"

        # 格式化输出
        lines = [f"Found {len(matches)} results in {abs_dir} (pattern: {pattern})"]
        for kind, path, meta in matches:
            if kind == "file":
                size_str = _format_size(meta)
                lines.append(f"  {kind:<4} {size_str:>8}  {path}")
            else:
                lines.append(f"  {kind:<4} {meta:>6} items  {path}")

        if len(matches) >= max_results:
            lines.append(f"  ... (结果已截断，上限 {max_results})")

        return "\n".join(lines)


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
