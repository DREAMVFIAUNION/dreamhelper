"""工具注册初始化 — 在应用启动时调用"""

from .tool_registry import ToolRegistry
from .implementations.calculator import CalculatorTool
from .implementations.datetime_tool import DateTimeTool
from .implementations.web_search import WebSearchTool
from .implementations.web_fetch import WebFetchTool
from .implementations.code_exec import CodeExecTool
from .implementations.run_workflow import RunWorkflowTool
from .implementations.weather_tool import WeatherTool
from .implementations.stock_tool import StockTool
from .implementations.crypto_tool import CryptoTool
from .implementations.news_tool import NewsTool
# Desktop Agent 工具
from .implementations.shell_exec import ShellExecTool
from .implementations.file_read import FileReadTool
from .implementations.file_write import FileWriteTool
from .implementations.file_edit import FileEditTool
from .implementations.file_search import FileSearchTool
from .implementations.code_grep import CodeGrepTool


def register_all_tools():
    """注册所有内置工具"""
    ToolRegistry.register(CalculatorTool())
    ToolRegistry.register(DateTimeTool())
    ToolRegistry.register(WebSearchTool())
    ToolRegistry.register(WebFetchTool())
    ToolRegistry.register(CodeExecTool())
    ToolRegistry.register(RunWorkflowTool())
    # 实时联网数据工具
    ToolRegistry.register(WeatherTool())
    ToolRegistry.register(StockTool())
    ToolRegistry.register(CryptoTool())
    ToolRegistry.register(NewsTool())
    # Desktop Agent 工具 (Phase A)
    ToolRegistry.register(ShellExecTool())
    ToolRegistry.register(FileReadTool())
    ToolRegistry.register(FileWriteTool())
    ToolRegistry.register(FileEditTool())
    ToolRegistry.register(FileSearchTool())
    ToolRegistry.register(CodeGrepTool())
    print(f"  ✓ Registered {len(ToolRegistry._tools)} tools: {list(ToolRegistry._tools.keys())}")
