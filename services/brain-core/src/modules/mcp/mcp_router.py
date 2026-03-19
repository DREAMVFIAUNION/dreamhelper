"""MCP 管理 API 路由"""

from fastapi import APIRouter, Request

from ...common.rate_limit import limiter
from .mcp_client_manager import MCPClientManager

router = APIRouter(prefix="/mcp", tags=["MCP"])


@router.get("/servers")
@limiter.limit("30/minute")
async def list_mcp_servers(request: Request):
    """列出所有 MCP Server 及其状态"""
    return {"servers": MCPClientManager.list_servers()}


@router.get("/tools")
@limiter.limit("30/minute")
async def list_mcp_tools(request: Request):
    """列出所有已连接 MCP Server 暴露的工具"""
    return {"tools": MCPClientManager.list_all_tools()}


@router.post("/servers/{name}/reconnect")
@limiter.limit("3/minute")
async def reconnect_server(request: Request, name: str):
    """重连指定 MCP Server"""
    conn = MCPClientManager.get_connection(name)
    if not conn:
        return {"error": f"Server '{name}' not found"}
    await MCPClientManager.reconnect(name)
    conn = MCPClientManager.get_connection(name)
    return {
        "name": name,
        "connected": conn.connected if conn else False,
        "error": conn.error if conn else "",
    }


@router.get("/status")
@limiter.limit("30/minute")
async def mcp_status(request: Request):
    """MCP 系统总体状态"""
    servers = MCPClientManager.list_servers()
    connected = sum(1 for s in servers if s["connected"])
    total_tools = sum(s["tools_count"] for s in servers if s["connected"])
    return {
        "total_servers": len(servers),
        "connected_servers": connected,
        "total_tools": total_tools,
        "servers": servers,
    }
