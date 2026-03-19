"""MCP Tool Bridge — 将 MCP Server 的工具桥接到 ToolRegistry

采用单调度器模式: 注册一个 `mcp_call` 元工具到 ToolRegistry，
LLM 通过 mcp_call(server, tool, params) 调用任意 MCP 工具。
避免工具列表爆炸，与 run_skill 模式一致。
"""

from typing import Any
from pydantic import BaseModel, Field

from ..tools.tool_registry import BaseTool, ToolRegistry
from .mcp_client_manager import MCPClientManager


class MCPCallArgs(BaseModel):
    server: str = Field(description="MCP 服务器名称，如 sequential-thinking, filesystem, memory-graph, windows, github, modelscope")
    tool: str = Field(description="工具名称，由对应 MCP 服务器提供")
    params: dict = Field(default={}, description="工具参数 (JSON 对象)")


class MCPDispatchTool(BaseTool):
    """MCP 调度工具 — 转发调用到 MCP Server"""

    name = "mcp_call"
    args_schema = MCPCallArgs

    def __init__(self):
        self.description = self._build_description()

    def _build_description(self) -> str:
        servers = MCPClientManager.list_servers()
        connected = [s for s in servers if s["connected"]]
        if not connected:
            return "调用 MCP 外接工具服务 (暂无已连接的服务器)"

        lines = [f"调用 MCP 外接工具服务。已连接 {len(connected)} 个服务器:"]
        for s in connected:
            tools_str = ", ".join(s["tools"]) if s["tools"] else "(无工具)"
            lines.append(f"  [{s['name']}]: {s['description']} — 工具: {tools_str}")
        lines.append("传入 server + tool + params 调用。不确定参数时可只传 server 和 tool 查看帮助。")
        lines.append("⚠️ 安全提示: windows/Shell 工具可执行系统命令，禁止执行破坏性操作 (如 rm -rf、format、del /s、注册表删除、Stop-Service 等)。")
        return "\n".join(lines)

    def refresh_description(self):
        """刷新描述（当 MCP 连接状态变化后调用）"""
        self.description = self._build_description()

    async def execute(self, **kwargs: Any) -> str:
        server = kwargs.get("server", "").strip()
        tool = kwargs.get("tool", "").strip()
        params = kwargs.get("params", {})

        # 无参数: 列出所有可用服务器和工具
        if not server:
            return self._list_all()

        # 有 server 无 tool: 列出该服务器的工具
        if not tool:
            return self._list_server_tools(server)

        # 解析 params
        if isinstance(params, str):
            import json
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                return f"params 不是合法 JSON: {params}"

        # 调用 MCP 工具
        return await MCPClientManager.call_tool(server, tool, params)

    def _list_all(self) -> str:
        servers = MCPClientManager.list_servers()
        if not servers:
            return "暂无已注册的 MCP 服务器。"
        lines = ["已注册的 MCP 服务器:"]
        for s in servers:
            status = "✓ 已连接" if s["connected"] else f"✗ 未连接({s['error'][:50]})"
            tools_str = ", ".join(s["tools"]) if s["tools"] else "-"
            lines.append(f"\n[{s['name']}] {status}")
            lines.append(f"  描述: {s['description']}")
            lines.append(f"  工具: {tools_str}")
        return "\n".join(lines)

    def _list_server_tools(self, server: str) -> str:
        conn = MCPClientManager.get_connection(server)
        if not conn:
            available = [s["name"] for s in MCPClientManager.list_servers()]
            return f"服务器 '{server}' 不存在。可用: {available}"
        if not conn.connected:
            return f"服务器 '{server}' 未连接: {conn.error}"
        if not conn.tools:
            return f"服务器 '{server}' 已连接但无可用工具。"
        lines = [f"[{server}] 可用工具:"]
        for t in conn.tools:
            lines.append(f"  - {t['name']}: {t['description']}")
        return "\n".join(lines)


def bridge_mcp_to_tools():
    """注册 mcp_call 调度工具到 ToolRegistry"""
    if "mcp_call" in ToolRegistry._tools:
        # 已注册则刷新描述
        tool = ToolRegistry._tools["mcp_call"]
        if hasattr(tool, "refresh_description"):
            tool.refresh_description()
        return

    ToolRegistry.register(MCPDispatchTool())
    total_tools = sum(len(s["tools"]) for s in MCPClientManager.list_servers() if s["connected"])
    print(f"  ✓ MCP bridge registered: mcp_call → {total_tools} external tools")
