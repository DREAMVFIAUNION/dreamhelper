"""文件读取工具 — 读取文件内容（支持行号范围）

安全特性:
  - 通过 PermissionGateway 路径验证
  - 支持行号范围读取（大文件友好）
  - 自动检测编码
  - 文件大小限制
"""

import os
import logging
from typing import Any
from pydantic import BaseModel, Field

from ..tool_registry import BaseTool
from ...security.permission_gateway import get_permission_gateway

logger = logging.getLogger("tools.file_read")


class FileReadArgs(BaseModel):
    path: str = Field(..., description="文件的绝对或相对路径")
    start_line: int = Field(0, description="起始行号（1-indexed，0=从头开始）")
    end_line: int = Field(0, description="结束行号（0=到文件末尾）")


class FileReadTool(BaseTool):
    name = "file_read"
    description = "读取文件内容。支持指定行号范围，自动检测编码。返回带行号的文件内容。"
    args_schema = FileReadArgs

    async def execute(self, **kwargs: Any) -> str:
        file_path = kwargs.get("path", "")
        start_line = kwargs.get("start_line", 0)
        end_line = kwargs.get("end_line", 0)

        if not file_path:
            return "❌ 缺少 path 参数"

        abs_path = os.path.abspath(file_path)

        # 权限检查
        gateway = get_permission_gateway()
        result = gateway.check_file_operation("file_read", abs_path, write=False)
        if not result.allowed:
            return f"⛔ 读取被阻止: {result.reason}"

        if not os.path.exists(abs_path):
            return f"❌ 文件不存在: {abs_path}"

        if os.path.isdir(abs_path):
            return f"❌ 路径是目录，请使用 file_search 工具: {abs_path}"

        # 文件大小检查
        size_bytes = os.path.getsize(abs_path)
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > gateway.max_file_size_mb:
            return f"⚠️ 文件过大 ({size_mb:.1f}MB)，请指定行号范围读取"

        # 读取文件
        try:
            for encoding in ("utf-8", "gbk", "latin-1"):
                try:
                    with open(abs_path, "r", encoding=encoding) as f:
                        lines = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return f"❌ 无法解码文件: {abs_path}"
        except Exception as e:
            return f"❌ 读取失败: {e}"

        total_lines = len(lines)

        # 行号范围
        s = max(1, start_line) if start_line > 0 else 1
        e = min(total_lines, end_line) if end_line > 0 else total_lines

        selected = lines[s - 1 : e]

        # 格式化带行号的输出
        numbered = []
        for i, line in enumerate(selected, start=s):
            numbered.append(f"{i:>6}\t{line.rstrip()}")

        content = "\n".join(numbered)

        # 截断过长输出
        max_chars = 12000
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n... (输出已截断，文件共 {total_lines} 行)"

        header = f"File: {abs_path} ({total_lines} lines, {size_bytes} bytes)"
        if start_line > 0 or end_line > 0:
            header += f" [showing lines {s}-{e}]"

        return f"{header}\n{content}"
