"""GitNexus MCP 客户端 — 封装 7 个代码知识图谱工具

通过 MCPClientManager 调用 GitNexus MCP Server，提供:
- query: 语义搜索执行流
- context: 符号 360° 视图
- impact: 变更影响分析（爆炸半径）
- detect_changes: Git 变更检测
- rename: 多文件协同重命名（预览模式）
- cypher: 原始图查询
- list_repos: 列出已索引仓库
"""

import json
import logging
from typing import Any, Optional

from ..mcp.mcp_client_manager import MCPClientManager
from .config import get_code_intel_config

logger = logging.getLogger("code_intel.client")


class GitNexusClient:
    """GitNexus 代码知识图谱客户端"""

    def __init__(self):
        self.config = get_code_intel_config()
        self._server_name = self.config.mcp_server_name

    @property
    def available(self) -> bool:
        """检查 GitNexus MCP 是否已连接"""
        conn = MCPClientManager.get_connection(self._server_name)
        return conn is not None and conn.connected

    async def _call(self, tool: str, params: dict[str, Any]) -> dict:
        """调用 GitNexus MCP 工具并解析 JSON 结果"""
        if not self.available:
            return {"error": "GitNexus MCP 未连接", "tool": tool}

        # 自动注入默认 repo
        if self.config.default_repo and "repo" not in params:
            params["repo"] = self.config.default_repo

        raw = await MCPClientManager.call_tool(self._server_name, tool, params)

        # 尝试解析 JSON
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            # GitNexus 有些工具返回 markdown 表格而非 JSON
            return {"raw": raw, "tool": tool}

    # ── 7 个核心工具 ──────────────────────────────────

    async def query(
        self,
        query: str,
        goal: str = "",
        repo: str = "",
        limit: int = 5,
        include_content: bool = False,
    ) -> dict:
        """语义搜索代码执行流 — 返回按相关性排序的进程和符号"""
        params: dict[str, Any] = {"query": query, "limit": limit}
        if goal:
            params["goal"] = goal
        if repo:
            params["repo"] = repo
        if include_content:
            params["include_content"] = True
        return await self._call("query", params)

    async def context(
        self,
        name: str,
        repo: str = "",
        include_content: bool = False,
        uid: str = "",
    ) -> dict:
        """获取符号 360° 视图 — 调用者/被调用者/所在执行流/文件位置"""
        params: dict[str, Any] = {"name": name}
        if repo:
            params["repo"] = repo
        if include_content:
            params["include_content"] = True
        if uid:
            params["uid"] = uid
        return await self._call("context", params)

    async def impact(
        self,
        target: str,
        direction: str = "upstream",
        max_depth: int = 3,
        repo: str = "",
        include_tests: bool = False,
    ) -> dict:
        """分析变更影响范围（爆炸半径）— d=1必中/d=2可能/d=3需测试"""
        params: dict[str, Any] = {
            "target": target,
            "direction": direction,
            "maxDepth": max_depth,
        }
        if repo:
            params["repo"] = repo
        if include_tests:
            params["includeTests"] = True
        return await self._call("impact", params)

    async def detect_changes(
        self,
        scope: str = "all",
        repo: str = "",
        base_ref: str = "",
    ) -> dict:
        """检测未提交的代码变更及其影响的执行流"""
        params: dict[str, Any] = {"scope": scope}
        if repo:
            params["repo"] = repo
        if base_ref:
            params["base_ref"] = base_ref
        return await self._call("detect_changes", params)

    async def rename(
        self,
        symbol_name: str,
        new_name: str,
        dry_run: bool = True,
        repo: str = "",
    ) -> dict:
        """多文件协同重命名（默认预览模式）"""
        params: dict[str, Any] = {
            "symbol_name": symbol_name,
            "new_name": new_name,
            "dry_run": dry_run,
        }
        if repo:
            params["repo"] = repo
        return await self._call("rename", params)

    async def cypher(self, query: str, repo: str = "") -> dict:
        """执行原始 Cypher 图查询"""
        params: dict[str, Any] = {"query": query}
        if repo:
            params["repo"] = repo
        return await self._call("cypher", params)

    async def list_repos(self) -> dict:
        """列出所有已索引的仓库"""
        return await self._call("list_repos", {})

    # ── 便捷方法 ──────────────────────────────────

    async def get_status(self) -> dict:
        """获取 GitNexus 连接状态和仓库概况"""
        status = {
            "available": self.available,
            "mcp_server": self._server_name,
            "default_repo": self.config.default_repo,
        }
        if self.available:
            try:
                repos = await self.list_repos()
                status["repos"] = repos
            except Exception as e:
                status["error"] = str(e)
        return status

    async def analyze_for_chat(self, user_query: str) -> str:
        """为聊天上下文分析代码问题 — 返回格式化的知识图谱数据"""
        if not self.available:
            return ""

        try:
            result = await self.query(
                query=user_query,
                goal="为用户的代码问题提供架构上下文",
                limit=3,
            )

            if "error" in result:
                return ""

            raw = result.get("raw", "")
            if raw:
                # 截取前 2000 字符避免 prompt 过长
                return f"[代码知识图谱]\n{raw[:2000]}"

            return ""

        except Exception as e:
            logger.debug("[GitNexus] analyze_for_chat failed: %s", e)
            return ""


# ── 全局单例 ──────────────────────────────────

_client: GitNexusClient | None = None


def get_gitnexus_client() -> GitNexusClient:
    global _client
    if _client is None:
        _client = GitNexusClient()
    return _client
