"""代码搜索工具 — 正则/文本搜索（类 ripgrep）

安全特性:
  - 通过 PermissionGateway 路径验证
  - 结果数量上限
  - 自动排除二进制文件和 .git 等
"""

import os
import re
import logging
from typing import Any
from pydantic import BaseModel, Field

from ..tool_registry import BaseTool
from ...security.permission_gateway import get_permission_gateway

logger = logging.getLogger("tools.code_grep")

# 默认排除目录
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".next", ".nuxt",
    "dist", "build", ".venv", "venv", ".tox", ".mypy_cache",
    ".pytest_cache", "coverage", ".turbo",
}

# 文本文件扩展名
TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".vue", ".svelte",
    ".html", ".css", ".scss", ".less", ".sass",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".md", ".txt", ".rst", ".csv",
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
    ".sql", ".graphql", ".gql",
    ".xml", ".svg",
    ".env.example", ".gitignore", ".dockerignore",
    ".c", ".h", ".cpp", ".hpp", ".java", ".go", ".rs", ".rb",
    ".php", ".swift", ".kt", ".dart", ".r", ".m",
    "Dockerfile", "Makefile", "Pipfile", "Gemfile",
}


class CodeGrepArgs(BaseModel):
    query: str = Field(..., description="搜索文本或正则表达式")
    directory: str = Field(".", description="搜索起始目录")
    includes: str = Field("", description="文件名过滤（glob格式，如 *.py）")
    fixed_strings: bool = Field(False, description="是否按字面量搜索（非正则）")
    case_sensitive: bool = Field(False, description="是否区分大小写")
    max_results: int = Field(30, description="最大结果文件数")
    context_lines: int = Field(2, description="每个匹配显示的上下文行数")


class CodeGrepTool(BaseTool):
    name = "code_grep"
    description = (
        "在代码文件中搜索文本或正则表达式。类似 ripgrep。"
        "返回匹配的文件、行号和上下文。自动排除二进制文件和 .git 等目录。"
    )
    args_schema = CodeGrepArgs

    async def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        directory = kwargs.get("directory", ".")
        includes = kwargs.get("includes", "")
        fixed_strings = kwargs.get("fixed_strings", False)
        case_sensitive = kwargs.get("case_sensitive", False)
        max_results = min(kwargs.get("max_results", 30), 100)
        context_lines = min(kwargs.get("context_lines", 2), 5)

        if not query:
            return "❌ 缺少 query 参数"

        abs_dir = os.path.abspath(directory)

        # 权限检查
        gateway = get_permission_gateway()
        result = gateway.check_file_operation("code_grep", abs_dir, write=False)
        if not result.allowed:
            return f"⛔ 搜索被阻止: {result.reason}"

        if not os.path.isdir(abs_dir):
            return f"❌ 目录不存在: {abs_dir}"

        # 编译搜索模式
        try:
            if fixed_strings:
                if case_sensitive:
                    pattern = re.compile(re.escape(query))
                else:
                    pattern = re.compile(re.escape(query), re.IGNORECASE)
            else:
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(query, flags)
        except re.error as e:
            return f"❌ 无效正则表达式: {e}"

        # 解析 includes glob
        import fnmatch
        include_pattern = includes.strip() if includes else ""

        # 搜索
        file_matches = []
        total_matches = 0

        try:
            for root, dirs, files in os.walk(abs_dir):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

                for name in files:
                    # 扩展名过滤
                    ext = os.path.splitext(name)[1].lower()
                    basename = name.lower()
                    if ext not in TEXT_EXTENSIONS and basename not in TEXT_EXTENSIONS:
                        continue

                    # includes 过滤
                    if include_pattern and not fnmatch.fnmatch(name, include_pattern):
                        continue

                    filepath = os.path.join(root, name)
                    rel_path = os.path.relpath(filepath, abs_dir)

                    # 搜索文件内容
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                            lines = f.readlines()
                    except Exception:
                        continue

                    matches_in_file = []
                    for i, line in enumerate(lines):
                        if pattern.search(line):
                            # 收集上下文
                            start = max(0, i - context_lines)
                            end = min(len(lines), i + context_lines + 1)
                            context = []
                            for j in range(start, end):
                                prefix = ">" if j == i else " "
                                context.append(f"{prefix} {j + 1:>5} | {lines[j].rstrip()}")
                            matches_in_file.append({
                                "line": i + 1,
                                "context": "\n".join(context),
                            })
                            total_matches += 1

                    if matches_in_file:
                        file_matches.append({
                            "path": rel_path,
                            "matches": matches_in_file,
                        })

                    if len(file_matches) >= max_results:
                        break

                if len(file_matches) >= max_results:
                    break

        except Exception as e:
            return f"❌ 搜索失败: {e}"

        if not file_matches:
            return f"未找到匹配 '{query}' 的内容（搜索目录: {abs_dir}）"

        # 格式化输出
        parts = [f"Found {total_matches} matches in {len(file_matches)} files"]

        for fm in file_matches:
            parts.append(f"\n--- {fm['path']} ---")
            for m in fm["matches"][:5]:  # 每文件最多5处
                parts.append(m["context"])
            if len(fm["matches"]) > 5:
                parts.append(f"  ... ({len(fm['matches'])} matches total)")

        if len(file_matches) >= max_results:
            parts.append(f"\n... (结果已截断，上限 {max_results} 文件)")

        output = "\n".join(parts)

        # 截断过长输出
        if len(output) > 10000:
            output = output[:10000] + "\n... (输出已截断)"

        return output
