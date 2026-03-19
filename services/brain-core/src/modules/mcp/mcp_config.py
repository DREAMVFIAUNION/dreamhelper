"""MCP 服务配置 — 定义可用的 MCP Server 及其启动参数"""

import os
from dataclasses import dataclass, field
from typing import Optional
from ...common.config import settings


@dataclass
class MCPServerConfig:
    """单个 MCP Server 的配置"""
    name: str
    enabled: bool = True
    transport: str = "stdio"          # "stdio" | "http"
    command: str = "npx"              # stdio 启动命令
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str = ""                     # HTTP transport URL
    timeout: float = 30.0             # 连接/调用超时 (秒)
    description: str = ""


def get_mcp_server_configs() -> list[MCPServerConfig]:
    """返回所有已配置的 MCP Server 列表（根据环境变量动态启用）"""
    configs: list[MCPServerConfig] = []

    # ── P0: Sequential Thinking ──
    if getattr(settings, "MCP_SEQUENTIAL_THINKING", True):
        configs.append(MCPServerConfig(
            name="sequential-thinking",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
            timeout=90.0,
            description="动态反思式思维链推理，增强三脑复杂问题处理",
        ))

    # ── P0: Filesystem ──
    if getattr(settings, "MCP_FILESYSTEM", True):
        allowed_dirs = getattr(settings, "MCP_FILESYSTEM_ALLOWED_DIRS", "./tmp/dreamhelp")
        dir_list = []
        for d in allowed_dirs.split(","):
            d = d.strip()
            if not d:
                continue
            abs_d = os.path.abspath(d)
            os.makedirs(abs_d, exist_ok=True)
            dir_list.append(abs_d)
        configs.append(MCPServerConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"] + dir_list,
            timeout=30.0,
            description="安全文件读写、搜索、目录操作",
        ))

    # ── P0: Memory (Knowledge Graph) ──
    if getattr(settings, "MCP_MEMORY_GRAPH", True):
        configs.append(MCPServerConfig(
            name="memory-graph",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
            timeout=15.0,
            description="知识图谱持久化记忆系统",
        ))

    # ── P0: Windows Desktop Automation ──
    if getattr(settings, "MCP_WINDOWS", True):
        windows_dir = getattr(settings, "MCP_WINDOWS_DIR", "D:/Windows-MCP-main")
        windows_dir = os.path.abspath(windows_dir)
        # uv 可能不在 PATH 中，尝试常见位置
        uv_cmd = "uv"
        uv_candidates = [
            os.path.expandvars(r"%APPDATA%\Python\Python314\Scripts\uv.exe"),
            os.path.expandvars(r"%APPDATA%\Python\Python313\Scripts\uv.exe"),
            os.path.expanduser("~/.local/bin/uv"),
        ]
        for candidate in uv_candidates:
            if os.path.isfile(candidate):
                uv_cmd = candidate
                break
        configs.append(MCPServerConfig(
            name="windows",
            command=uv_cmd,
            args=["--directory", windows_dir, "run", "windows-mcp"],
            env={"ANONYMIZED_TELEMETRY": "false"},
            timeout=90.0,
            description="Windows 桌面自动化: 点击/输入/截图/应用控制/Shell命令 (11 tools)",
        ))

    # ── P0: GitNexus Code Intelligence ──
    if getattr(settings, "MCP_GITNEXUS", True):
        gitnexus_cmd = getattr(settings, "GITNEXUS_MCP_CMD", "npx")
        gitnexus_args_str = getattr(settings, "GITNEXUS_MCP_ARGS", "-y gitnexus@latest mcp")
        gitnexus_args = gitnexus_args_str.split()
        configs.append(MCPServerConfig(
            name="gitnexus",
            command=gitnexus_cmd,
            args=gitnexus_args,
            timeout=60.0,
            description="代码知识图谱: 调用链/影响分析/语义搜索/符号上下文/变更检测 (7 tools)",
        ))

    # ── P1: GitHub ──
    if getattr(settings, "MCP_GIT", False):
        github_token = getattr(settings, "GITHUB_PERSONAL_ACCESS_TOKEN", "")
        env = {"GITHUB_PERSONAL_ACCESS_TOKEN": github_token} if github_token else {}
        configs.append(MCPServerConfig(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env=env,
            timeout=30.0,
            description="GitHub 仓库、Issues、PR 读取与操作",
        ))

    # ── P1: ModelScope (魔搭AI生态) ──
    modelscope_token = getattr(settings, "MODELSCOPE_API_TOKEN", "")
    if getattr(settings, "MCP_MODELSCOPE", False) and modelscope_token:
        configs.append(MCPServerConfig(
            name="modelscope",
            command="modelscope-mcp-server",
            args=[],
            env={"MODELSCOPE_API_TOKEN": modelscope_token},
            timeout=30.0,
            description="魔搭AI生态: 模型/数据集/应用/论文/MCP搜索, AI图像生成 (9 tools)",
        ))

    # ── P1: 无影 AgentBay (云端 Agent 执行环境) ──
    agentbay_key = getattr(settings, "AGENTBAY_API_KEY", "")
    if getattr(settings, "MCP_AGENTBAY", False) and agentbay_key:
        image_id = getattr(settings, "AGENTBAY_IMAGE_ID", "code_latest")
        configs.append(MCPServerConfig(
            name="agentbay",
            transport="sse",
            url=f"https://agentbay.wuying.aliyuncs.com/v2/sse?APIKEY={agentbay_key}&IMAGEID={image_id}",
            timeout=120.0,
            description="无影AgentBay云环境: 代码执行(Python/JS)/Shell/文件系统/OSS (Serverless)",
        ))

    return configs
