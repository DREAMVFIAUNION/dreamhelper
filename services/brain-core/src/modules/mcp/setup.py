"""MCP 初始化入口 — 应用启动时调用"""

import asyncio
import logging

from .mcp_config import get_mcp_server_configs
from .mcp_client_manager import MCPClientManager
from .mcp_tool_bridge import bridge_mcp_to_tools

logger = logging.getLogger("mcp.setup")

# MCP 连接就绪后的回调 — 延迟桥接到 ToolRegistry
_bridge_task: asyncio.Task | None = None


async def initialize_mcp():
    """启动所有 MCP Server 并桥接工具到 ToolRegistry

    MCP 连接是异步的，不阻塞主启动流程。
    连接建立后延迟注册 mcp_call 工具。
    """
    configs = get_mcp_server_configs()
    enabled = [c for c in configs if c.enabled]

    if not enabled:
        print("  ⚠ MCP: 无已启用的 MCP Server")
        return

    print(f"  🔌 MCP: 正在启动 {len(enabled)} 个服务器...")
    await MCPClientManager.initialize(enabled)

    # initialize() 现在是顺序连接，完成后立即检查并重试失败的
    servers = MCPClientManager.list_servers()
    connected = sum(1 for s in servers if s["connected"])
    failed = [s["name"] for s in servers if not s["connected"]]

    # 重试一次失败的连接
    if failed:
        logger.info("MCP: %d/%d 已连接，重试: %s", connected, len(enabled), failed)
        print(f"  🔄 MCP: 重试 {failed}...")
        for name in failed:
            await MCPClientManager.reconnect(name)

    # 最终状态报告 + 桥接
    servers = MCPClientManager.list_servers()
    connected = sum(1 for s in servers if s["connected"])
    total_tools = sum(s["tools_count"] for s in servers if s["connected"])
    print(f"  ✓ MCP: {connected}/{len(enabled)} 服务器已连接, {total_tools} 个工具")
    bridge_mcp_to_tools()
    
    # 动态将刚桥接进来的外源 MCP 工具全部向量化到 RAG 检索池中
    from ..tools.skills.skill_engine import SkillEngine
    try:
        await SkillEngine.vectorize_all_skills()
    except Exception as e:
        logger.error(f"MCP 工具动态向量化失败: {e}")


async def shutdown_mcp():
    """关闭所有 MCP 连接"""
    global _bridge_task
    if _bridge_task and not _bridge_task.done():
        _bridge_task.cancel()
    await MCPClientManager.shutdown()
