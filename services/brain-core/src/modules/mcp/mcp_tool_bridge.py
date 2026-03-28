"""MCP Tool Bridge — 将 MCP Server 的工具桥接到 SkillEngine

完全原生扁平化集成：将连接的所有 MCP Server 内的外部工具，
逐一动态实例化为 MCPDynamicSkill，并直接注入到系统的 SkillEngine 中。
它们将被统一向量化计算，Agent 调用时跟本地 Python 技能体验完全一致。
"""

from typing import Any
from pydantic import BaseModel, ConfigDict

from ..tools.skills.skill_engine import BaseSkill, SkillEngine
from .mcp_client_manager import MCPClientManager


class GenericMCPArgs(BaseModel):
    """允许接受任何多余参数的泛型模型，具体校验由远端 MCP Server 负责。"""
    model_config = ConfigDict(extra="allow")


class MCPDynamicSkill(BaseSkill):
    """MCP 动态技能适配器 — 桥接远端 MCP 工具到本地 SkillEngine"""

    def __init__(self, server_name: str, tool_name: str, description: str, json_schema: dict):
        # 构造扁平化名称，防止重名，例如 mcp_filesystem_read_file
        safe_server = server_name.replace("-", "_")
        safe_tool = tool_name.replace("-", "_")
        self.name = f"mcp_{safe_server}_{safe_tool}"
        self.description = description
        self.category = "mcp_plugin"
        self.args_schema = GenericMCPArgs
        self.version = "1.0.0"
        self.tags = ["mcp", server_name, tool_name]
        
        self._server_name = server_name
        self._tool_name = tool_name
        self._json_schema = json_schema

    def to_schema(self) -> dict:
        """重写 to_schema，直接返回 MCP Server 提供的精确原生 JSON Schema，让 LLM 获得正确提示"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "tags": self.tags,
            "parameters": self._json_schema,
        }

    async def execute(self, **kwargs: Any) -> str:
        """直接透传 kwargs 参数到底层 MCP Client Manager 执行"""
        return await MCPClientManager.call_tool(self._server_name, self._tool_name, kwargs)


def bridge_mcp_to_tools():
    """将已连接的 MCP Server 中的所有工具实例化为 MCPDynamicSkill 并注册到 SkillEngine"""
    for server in MCPClientManager.list_servers():
        if not server["connected"]:
            continue
            
        server_name = server["name"]
        conn = MCPClientManager.get_connection(server_name)
        if not conn or not conn.tools:
            continue
            
        for t in conn.tools:
            # 兼容空描述
            desc = t.get("description", "")
            if not desc:
                desc = f"Invoke {t['name']} from MCP server {server_name}"
                
            skill = MCPDynamicSkill(
                server_name=server_name,
                tool_name=t["name"],
                description=desc,
                json_schema=t.get("input_schema", {})
            )
            SkillEngine.register(skill)

    total_tools = sum(len(s["tools"]) for s in MCPClientManager.list_servers() if s["connected"])
    print(f"  ✓ MCP bridge registered: {total_tools} external tools flattened into SkillEngine")
