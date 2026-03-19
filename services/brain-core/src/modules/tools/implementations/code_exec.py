"""代码执行沙箱工具 — 安全执行 Python 代码片段"""

import asyncio
import re
import subprocess
import sys
import tempfile
import logging
from typing import Any

from pydantic import BaseModel, Field
from ..tool_registry import BaseTool
from ....common.config import settings

# 危险模块黑名单
_BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "shutil", "socket", "signal",
    "ctypes", "importlib", "builtins", "__builtins__",
    "pathlib", "glob", "tempfile", "webbrowser", "http",
    "ftplib", "smtplib", "telnetlib", "xmlrpc", "multiprocessing",
    "threading", "pickle", "shelve", "marshal",
}

_BLOCKED_PATTERNS = [
    r"\bopen\s*\(",         # 文件操作
    r"\bexec\s*\(",         # 动态执行
    r"\beval\s*\(",         # 动态求值
    r"\bcompile\s*\(",      # 编译代码
    r"__import__",          # 动态导入
    r"\bgetattr\s*\(",      # 属性访问
    r"\bsetattr\s*\(",      # 属性设置
    r"\bdelattr\s*\(",      # 属性删除
    r"\bglobals\s*\(",      # 全局变量
    r"\blocals\s*\(",       # 局部变量
]


class CodeExecArgs(BaseModel):
    code: str = Field(description="要执行的 Python 代码")
    timeout: int = Field(default=10, description="超时秒数，默认10秒")


def _check_code_safety(code: str) -> str | None:
    """检查代码安全性，返回错误信息或 None"""
    # 检查导入
    import_pattern = re.compile(r'(?:from\s+(\w+)|import\s+(\w+))')
    for match in import_pattern.finditer(code):
        module = match.group(1) or match.group(2)
        if module in _BLOCKED_IMPORTS:
            return f"安全限制: 禁止导入模块 '{module}'"

    # 检查危险函数调用
    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, code):
            return f"安全限制: 检测到危险操作 '{pattern.strip(chr(92)).strip('b').strip('s*(')}'"

    return None


class CodeExecTool(BaseTool):
    name = "code_exec"
    description = "安全执行 Python 代码片段并返回输出结果。适用于数学计算、数据处理、算法验证等。禁止文件操作和网络访问。"
    args_schema = CodeExecArgs

    async def execute(self, **kwargs: Any) -> str:
        code = kwargs.get("code", "")
        timeout = min(int(kwargs.get("timeout", settings.CODE_EXEC_TIMEOUT)), 30)
        max_output = settings.CODE_EXEC_MAX_OUTPUT

        if not code.strip():
            return "请提供要执行的 Python 代码"

        # 安全检查
        safety_error = _check_code_safety(code)
        if safety_error:
            return f"[代码执行] {safety_error}"

        try:
            result = await self._run_code(code, timeout, max_output)
            return result
        except Exception as e:
            logging.getLogger(__name__).exception("Code execution failed")
            return "[执行错误] 代码执行失败"

    async def _run_code(self, code: str, timeout: int, max_output: int) -> str:
        """在子进程中执行代码"""
        # 写入临时文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # 不继承环境中的敏感变量
                env={"PATH": "", "PYTHONDONTWRITEBYTECODE": "1"},
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return f"[代码执行] 超时 ({timeout}s)，已终止"

            stdout_text = stdout.decode("utf-8", errors="replace").strip()
            stderr_text = stderr.decode("utf-8", errors="replace").strip()

            # 截断输出
            if len(stdout_text) > max_output:
                stdout_text = stdout_text[:max_output] + "\n...(输出已截断)"
            if len(stderr_text) > max_output:
                stderr_text = stderr_text[:max_output] + "\n...(错误输出已截断)"

            parts = ["[代码执行结果]"]
            if stdout_text:
                parts.append(f"输出:\n{stdout_text}")
            if stderr_text:
                parts.append(f"错误:\n{stderr_text}")
            if not stdout_text and not stderr_text:
                parts.append("(无输出)")
            if proc.returncode != 0:
                parts.append(f"退出码: {proc.returncode}")

            return "\n".join(parts)

        finally:
            # 清理临时文件
            import os
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
