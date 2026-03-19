"""MCP 配置与工具桥接测试"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestMCPConfig:
    """测试 MCP 服务配置"""

    def test_default_p0_servers_enabled(self):
        """P0 服务默认启用"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            mock_settings.MCP_SEQUENTIAL_THINKING = True
            mock_settings.MCP_FILESYSTEM = True
            mock_settings.MCP_FILESYSTEM_ALLOWED_DIRS = "/tmp/dreamhelp"
            mock_settings.MCP_MEMORY_GRAPH = True
            mock_settings.MCP_GIT = False

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()
            names = [c.name for c in configs]

            assert "sequential-thinking" in names
            assert "filesystem" in names
            assert "memory-graph" in names
            assert "github" not in names

    def test_p1_servers_disabled_by_default(self):
        """P1 服务默认禁用"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            mock_settings.MCP_SEQUENTIAL_THINKING = True
            mock_settings.MCP_FILESYSTEM = True
            mock_settings.MCP_FILESYSTEM_ALLOWED_DIRS = "/tmp"
            mock_settings.MCP_MEMORY_GRAPH = True
            mock_settings.MCP_GIT = False

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()
            names = [c.name for c in configs]

            assert "github" not in names

    def test_filesystem_allowed_dirs_parsing(self):
        """Filesystem 允许目录正确解析"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            mock_settings.MCP_SEQUENTIAL_THINKING = False
            mock_settings.MCP_FILESYSTEM = True
            mock_settings.MCP_FILESYSTEM_ALLOWED_DIRS = "/tmp/a, /tmp/b, /data"
            mock_settings.MCP_MEMORY_GRAPH = False
            mock_settings.MCP_GIT = False

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()
            fs_config = [c for c in configs if c.name == "filesystem"][0]

            # args 应包含: -y, @modelcontextprotocol/server-filesystem, 以及各目录的绝对路径
            import os
            assert os.path.abspath("/tmp/a") in fs_config.args
            assert os.path.abspath("/tmp/b") in fs_config.args
            assert os.path.abspath("/data") in fs_config.args

    def test_server_config_defaults(self):
        """服务配置默认值正确"""
        from src.modules.mcp.mcp_config import MCPServerConfig

        cfg = MCPServerConfig(name="test")
        assert cfg.enabled is True
        assert cfg.transport == "stdio"
        assert cfg.command == "npx"
        assert cfg.timeout == 30.0
        assert cfg.args == []
        assert cfg.env == {}


class TestMCPToolBridge:
    """测试 MCP 工具桥接"""

    def test_mcp_dispatch_tool_schema(self):
        """MCPDispatchTool 有正确的 schema"""
        from src.modules.mcp.mcp_tool_bridge import MCPDispatchTool

        tool = MCPDispatchTool()
        assert tool.name == "mcp_call"
        schema = tool.to_schema()
        assert schema["name"] == "mcp_call"
        params = schema["parameters"]
        assert "server" in params.get("properties", {})
        assert "tool" in params.get("properties", {})
        assert "params" in params.get("properties", {})

    @pytest.mark.asyncio
    async def test_mcp_dispatch_no_server_lists_all(self):
        """无 server 参数时列出所有服务器"""
        from src.modules.mcp.mcp_tool_bridge import MCPDispatchTool

        tool = MCPDispatchTool()
        result = await tool.execute(server="", tool="", params={})
        assert "暂无" in result or "已注册" in result

    @pytest.mark.asyncio
    async def test_mcp_dispatch_unknown_server(self):
        """未知 server 名称返回提示"""
        from src.modules.mcp.mcp_tool_bridge import MCPDispatchTool

        tool = MCPDispatchTool()
        result = await tool.execute(server="nonexistent", tool="", params={})
        assert "不存在" in result

    @pytest.mark.asyncio
    async def test_mcp_dispatch_invalid_json_params(self):
        """非法 JSON params 返回错误"""
        from src.modules.mcp.mcp_tool_bridge import MCPDispatchTool

        tool = MCPDispatchTool()
        result = await tool.execute(server="test", tool="test_tool", params="not-json{")
        assert "不是合法 JSON" in result


class TestMCPClientManager:
    """测试 MCP 连接管理器"""

    def test_list_servers_empty_initially(self):
        """初始时无服务器"""
        from src.modules.mcp.mcp_client_manager import MCPClientManager
        # 重置状态
        MCPClientManager._connections.clear()
        MCPClientManager._initialized = False

        servers = MCPClientManager.list_servers()
        assert servers == []

    def test_list_all_tools_empty_initially(self):
        """初始时无工具"""
        from src.modules.mcp.mcp_client_manager import MCPClientManager
        MCPClientManager._connections.clear()
        MCPClientManager._initialized = False

        tools = MCPClientManager.list_all_tools()
        assert tools == []

    @pytest.mark.asyncio
    async def test_call_tool_unregistered_server(self):
        """调用未注册服务器返回错误"""
        from src.modules.mcp.mcp_client_manager import MCPClientManager
        MCPClientManager._connections.clear()
        MCPClientManager._initialized = False

        result = await MCPClientManager.call_tool("ghost", "any_tool", {})
        assert "未注册" in result

    @pytest.mark.asyncio
    async def test_shutdown_clears_state(self):
        """shutdown 后状态清空"""
        from src.modules.mcp.mcp_client_manager import MCPClientManager
        MCPClientManager._connections.clear()
        MCPClientManager._initialized = True

        await MCPClientManager.shutdown()
        assert MCPClientManager._initialized is False
        assert len(MCPClientManager._connections) == 0


class TestMCPThinking:
    """测试 MCP Sequential Thinking 集成"""

    @pytest.mark.asyncio
    async def test_skip_non_complex_tasks(self):
        """非 complex/expert 任务跳过"""
        from src.modules.dual_brain.mcp_thinking import run_sequential_thinking

        result = await run_sequential_thinking("hello", task_complexity="simple")
        assert result is None

        result = await run_sequential_thinking("hello", task_complexity="medium")
        assert result is None

    @pytest.mark.asyncio
    async def test_skip_when_not_connected(self):
        """MCP 未连接时跳过"""
        from src.modules.dual_brain.mcp_thinking import run_sequential_thinking

        result = await run_sequential_thinking("complex math problem", task_complexity="complex")
        # 应返回 None（未连接）
        assert result is None

    def test_build_thinking_enhanced_context_empty(self):
        """无内容时返回空"""
        from src.modules.dual_brain.mcp_thinking import build_thinking_enhanced_context

        result = build_thinking_enhanced_context(None, "")
        assert result == ""

    def test_build_thinking_enhanced_context_both(self):
        """思维链 + 脑干指令合并"""
        from src.modules.dual_brain.mcp_thinking import build_thinking_enhanced_context

        result = build_thinking_enhanced_context(
            thinking_chain="Step 1: analyze...",
            brainstem_focus="关注代码准确性",
        )
        assert "脑干聚焦指令" in result
        assert "关注代码准确性" in result
        assert "结构化思维链分析" in result
        assert "Step 1: analyze" in result

    def test_build_thinking_enhanced_context_truncation(self):
        """超长思维链截断"""
        from src.modules.dual_brain.mcp_thinking import build_thinking_enhanced_context

        long_chain = "x" * 5000
        result = build_thinking_enhanced_context(thinking_chain=long_chain)
        assert len(result) < 5000  # 被截断


class TestMCPP1Config:
    """测试 P1 MCP 服务配置"""

    def _mock_settings(self, **overrides):
        """构建标准 mock settings"""
        defaults = {
            "MCP_SEQUENTIAL_THINKING": False,
            "MCP_FILESYSTEM": False,
            "MCP_FILESYSTEM_ALLOWED_DIRS": "/tmp",
            "MCP_MEMORY_GRAPH": False,
            "MCP_WINDOWS": False,
            "MCP_WINDOWS_DIR": "D:/Windows-MCP-main",
            "MCP_GIT": True,
            "GITHUB_PERSONAL_ACCESS_TOKEN": "",
            "MCP_MODELSCOPE": False,
            "MODELSCOPE_API_TOKEN": "",
        }
        defaults.update(overrides)
        return defaults

    def test_windows_mcp_enabled_by_default(self):
        """Windows MCP 默认启用"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            for k, v in self._mock_settings(
                MCP_WINDOWS=True,
                MCP_WINDOWS_DIR="D:/Windows-MCP-main",
                MCP_GIT=False,
            ).items():
                setattr(mock_settings, k, v)

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()
            names = [c.name for c in configs]

            assert "windows" in names

    def test_windows_mcp_uses_uv(self):
        """Windows MCP 使用 uv 启动"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            for k, v in self._mock_settings(
                MCP_WINDOWS=True,
                MCP_WINDOWS_DIR="D:/Windows-MCP-main",
                MCP_GIT=False,
            ).items():
                setattr(mock_settings, k, v)

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()
            win = [c for c in configs if c.name == "windows"][0]

            assert "uv" in win.command
            assert "--directory" in win.args
            assert "run" in win.args
            assert "windows-mcp" in win.args
            assert win.env.get("ANONYMIZED_TELEMETRY") == "false"

    def test_windows_mcp_disabled(self):
        """Windows MCP 禁用后不出现"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            for k, v in self._mock_settings(
                MCP_WINDOWS=False,
                MCP_WINDOWS_DIR="D:/Windows-MCP-main",
                MCP_GIT=False,
            ).items():
                setattr(mock_settings, k, v)

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()
            names = [c.name for c in configs]

            assert "windows" not in names

    def test_p1_github_enabled(self):
        """P1 GitHub 服务启用后出现在配置列表"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            for k, v in self._mock_settings().items():
                setattr(mock_settings, k, v)

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()
            names = [c.name for c in configs]

            assert "github" in names

    def test_p1_github_uses_npx(self):
        """GitHub MCP 使用 npx 启动"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            for k, v in self._mock_settings().items():
                setattr(mock_settings, k, v)

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()
            gh = [c for c in configs if c.name == "github"][0]

            assert gh.command == "npx"
            assert "@modelcontextprotocol/server-github" in gh.args

    def test_modelscope_disabled_without_token(self):
        """ModelScope MCP 无 token 时不启用"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            for k, v in self._mock_settings(MCP_MODELSCOPE=True, MODELSCOPE_API_TOKEN="").items():
                setattr(mock_settings, k, v)

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()
            names = [c.name for c in configs]

            assert "modelscope" not in names

    def test_modelscope_enabled_with_token(self):
        """ModelScope MCP 有 token 时正确启用"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            for k, v in self._mock_settings(
                MCP_MODELSCOPE=True,
                MODELSCOPE_API_TOKEN="ms-test-token-123",
            ).items():
                setattr(mock_settings, k, v)

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()
            ms = [c for c in configs if c.name == "modelscope"][0]

            assert ms.command == "modelscope-mcp-server"
            assert ms.args == []
            assert ms.env["MODELSCOPE_API_TOKEN"] == "ms-test-token-123"

    def test_all_six_servers_enabled(self):
        """全部 6 个 MCP Server 同时启用"""
        with patch("src.modules.mcp.mcp_config.settings") as mock_settings:
            all_on = {
                "MCP_SEQUENTIAL_THINKING": True,
                "MCP_FILESYSTEM": True,
                "MCP_FILESYSTEM_ALLOWED_DIRS": "/tmp",
                "MCP_MEMORY_GRAPH": True,
                "MCP_WINDOWS": True,
                "MCP_WINDOWS_DIR": "D:/Windows-MCP-main",
                "MCP_GIT": True,
                "GITHUB_PERSONAL_ACCESS_TOKEN": "gh-token",
                "MCP_MODELSCOPE": True,
                "MODELSCOPE_API_TOKEN": "ms-token",
            }
            for k, v in all_on.items():
                setattr(mock_settings, k, v)

            from src.modules.mcp.mcp_config import get_mcp_server_configs
            configs = get_mcp_server_configs()

            assert len(configs) == 6
            names = {c.name for c in configs}
            assert names == {
                "sequential-thinking", "filesystem", "memory-graph",
                "windows", "github", "modelscope",
            }
