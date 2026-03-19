"""代码智能模块 — GitNexus 知识图谱集成

通过 MCP 连接 GitNexus，为三脑提供代码架构感知能力:
- 执行流语义搜索
- 符号 360° 上下文
- 变更影响分析（爆炸半径）
- Git 变更检测
- 知识图谱 Cypher 查询
"""

from .gitnexus_client import get_gitnexus_client, GitNexusClient

__all__ = ["get_gitnexus_client", "GitNexusClient"]
