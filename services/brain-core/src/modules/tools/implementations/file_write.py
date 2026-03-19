"""文件写入工具 — 创建新文件或完全覆写

安全特性:
  - 通过 PermissionGateway 路径验证
  - 自动创建父目录
  - 不覆盖已有文件（除非 overwrite=true）
  - 写入后验证
"""

import os
import logging
from typing import Any
from pydantic import BaseModel, Field

from ..tool_registry import BaseTool
from ...security.permission_gateway import get_permission_gateway

logger = logging.getLogger("tools.file_write")


class FileWriteArgs(BaseModel):
    path: str = Field(..., description="文件的绝对或相对路径")
    content: str = Field(..., description="要写入的文件内容")
    overwrite: bool = Field(False, description="是否允许覆盖已有文件")


class FileWriteTool(BaseTool):
    name = "file_write"
    description = "创建新文件并写入内容。默认不覆盖已有文件，需设置 overwrite=true。自动创建父目录。"
    args_schema = FileWriteArgs

    async def execute(self, **kwargs: Any) -> str:
        file_path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        overwrite = kwargs.get("overwrite", False)

        if not file_path:
            return "❌ 缺少 path 参数"

        abs_path = os.path.abspath(file_path)

        # 权限检查
        gateway = get_permission_gateway()
        result = gateway.check_file_operation("file_write", abs_path, write=True)
        if not result.allowed:
            return f"⛔ 写入被阻止: {result.reason}"

        # 已有文件检查
        if os.path.exists(abs_path) and not overwrite:
            return (
                f"⚠️ 文件已存在: {abs_path}\n"
                f"如需覆盖，请设置 overwrite=true\n"
                f"如需编辑，请使用 file_edit 工具"
            )

        # 创建父目录
        parent = os.path.dirname(abs_path)
        if parent and not os.path.exists(parent):
            try:
                os.makedirs(parent, exist_ok=True)
                logger.info("[FileWrite] Created directory: %s", parent)
            except Exception as e:
                return f"❌ 无法创建目录 {parent}: {e}"

        # 写入
        try:
            with open(abs_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
        except Exception as e:
            return f"❌ 写入失败: {e}"

        # 验证
        size = os.path.getsize(abs_path)
        lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

        gateway.audit(
            "file_write", "written", result.risk_level, True,
            details=f"{abs_path} ({lines} lines, {size} bytes)",
        )

        return f"✅ 文件已写入: {abs_path}\n   {lines} 行, {size} 字节"
