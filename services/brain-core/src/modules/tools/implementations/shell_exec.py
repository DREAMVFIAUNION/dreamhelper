"""Shell 执行工具 — 执行 CMD / PowerShell / Bash 命令

安全特性:
  - 通过 PermissionGateway 6层验证
  - 持久化 Shell 会话（保持工作目录、环境变量）
  - 超时控制（默认 120s）
  - 危险命令拦截
  - 实时流式输出收集
"""

import asyncio
import os
import logging
from typing import Any
from pydantic import BaseModel, Field

from ..tool_registry import BaseTool
from ...security.permission_gateway import get_permission_gateway, RiskLevel

logger = logging.getLogger("tools.shell_exec")


class ShellExecArgs(BaseModel):
    command: str = Field(..., description="要执行的 Shell 命令")
    cwd: str = Field("", description="工作目录（可选，默认当前目录）")
    timeout: int = Field(120, description="超时秒数（默认120）")


class ShellExecTool(BaseTool):
    name = "shell_exec"
    description = "执行 CMD/PowerShell/Bash 命令。支持持久化工作目录、超时控制、危险命令拦截。"
    args_schema = ShellExecArgs

    def __init__(self):
        self._cwd: str = os.getcwd()

    async def execute(self, **kwargs: Any) -> str:
        command = kwargs.get("command", "")
        cwd = kwargs.get("cwd", "") or self._cwd
        timeout = min(kwargs.get("timeout", 120), 300)  # 最大5分钟

        # 权限检查
        gateway = get_permission_gateway()
        result = gateway.check_shell_command(command)

        if not result.allowed:
            return f"⛔ 命令被安全策略阻止: {result.reason}"

        if result.risk_level == RiskLevel.DANGEROUS:
            return f"⚠️ 高危命令需要用户确认: {command}\n风险: {result.reason}\n请用户在前端确认后重试。"

        # 获取工具槽位
        if not gateway.acquire_tool_slot():
            return "⚠️ 并发工具数已达上限，请稍后重试"

        try:
            # 确保工作目录存在
            if not os.path.isdir(cwd):
                cwd = os.getcwd()

            # 选择 shell
            if os.name == "nt":
                shell_cmd = ["powershell", "-NoProfile", "-Command", command]
            else:
                shell_cmd = ["/bin/bash", "-c", command]

            proc = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env={**os.environ},
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                gateway.audit("shell_exec", "timeout", RiskLevel.DANGEROUS, True, details=f"{command[:60]} (timeout={timeout}s)")
                return f"⏱️ 命令执行超时 ({timeout}s): {command[:80]}"

            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
            exit_code = proc.returncode

            # 更新持久化工作目录 (如果 cd 命令)
            if command.strip().startswith("cd "):
                try:
                    target = command.strip()[3:].strip().strip('"').strip("'")
                    new_cwd = os.path.abspath(os.path.join(cwd, target))
                    if os.path.isdir(new_cwd):
                        self._cwd = new_cwd
                except Exception:
                    pass

            # 截断过长输出
            max_output = 8000
            if len(stdout) > max_output:
                stdout = stdout[:max_output] + f"\n... (输出已截断，共 {len(stdout_bytes)} 字节)"
            if len(stderr) > max_output:
                stderr = stderr[:max_output] + f"\n... (stderr 已截断)"

            parts = [f"Exit code: {exit_code}"]
            if stdout:
                parts.append(f"stdout:\n{stdout}")
            if stderr:
                parts.append(f"stderr:\n{stderr}")

            gateway.audit(
                "shell_exec", "executed", RiskLevel.SAFE, True,
                details=f"exit={exit_code} cmd={command[:60]}",
            )

            return "\n".join(parts)

        except Exception as e:
            logger.error("[ShellExec] Error: %s", e)
            return f"❌ 命令执行失败: {e}"
        finally:
            gateway.release_tool_slot()
