"""MCP Sequential Thinking 集成 — 结构化思维链增强三脑推理

当脑干检测到 complex/expert 级别任务时，
并行调用 Sequential Thinking MCP 分解问题，
将思维链注入融合阶段以提升输出质量。
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger("dual_brain.mcp_thinking")


async def run_sequential_thinking(
    query: str,
    task_complexity: str = "complex",
    timeout: float = 45.0,
) -> Optional[str]:
    """调用 Sequential Thinking MCP 获取结构化思维链

    Args:
        query: 用户原始问题
        task_complexity: 任务复杂度 (complex/expert 才值得调用)
        timeout: 超时秒数

    Returns:
        思维链文本，失败返回 None
    """
    if task_complexity not in ("complex", "expert"):
        return None

    try:
        from ..mcp.mcp_client_manager import MCPClientManager

        conn = MCPClientManager.get_connection("sequential-thinking")
        if not conn or not conn.connected:
            logger.debug("Sequential Thinking MCP 未连接，跳过")
            return None

        # 调用 sequentialthinking 工具
        result = await asyncio.wait_for(
            MCPClientManager.call_tool(
                "sequential-thinking",
                "sequentialthinking",
                {
                    "thought": f"分析并分步骤拆解以下问题，识别关键要素、可能的解决路径和需要注意的边界条件: {query}",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 1,
                    "totalThoughts": 3,
                },
            ),
            timeout=timeout,
        )

        if result and not result.startswith("MCP"):
            logger.info("Sequential Thinking 返回 %d 字符思维链", len(result))
            return result
        else:
            logger.debug("Sequential Thinking 返回异常: %s", result[:100] if result else "None")
            return None

    except asyncio.TimeoutError:
        logger.warning("Sequential Thinking 超时 (%.0fs)", timeout)
        return None
    except Exception as e:
        logger.warning("Sequential Thinking 调用失败: %s", e)
        return None


def build_thinking_enhanced_context(
    thinking_chain: Optional[str],
    brainstem_focus: str = "",
) -> str:
    """将思维链与脑干指令合并为融合增强上下文

    Returns:
        合并后的增强指令文本
    """
    parts = []

    if brainstem_focus:
        parts.append(f"[脑干聚焦指令]\n{brainstem_focus}")

    if thinking_chain:
        # 截断过长的思维链
        truncated = thinking_chain[:2000] if len(thinking_chain) > 2000 else thinking_chain
        parts.append(f"[结构化思维链分析]\n{truncated}")

    return "\n\n".join(parts) if parts else ""
