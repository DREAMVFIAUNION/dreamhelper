"""代码智能模块配置"""

from dataclasses import dataclass
from ...common.config import settings


@dataclass
class CodeIntelConfig:
    """GitNexus 代码智能配置"""
    enabled: bool = True
    mcp_server_name: str = "gitnexus"
    default_repo: str = ""
    max_depth: int = 3
    query_limit: int = 5
    impact_timeout: float = 30.0

    def __post_init__(self):
        self.enabled = getattr(settings, "GITNEXUS_ENABLED", True)
        self.default_repo = getattr(settings, "GITNEXUS_DEFAULT_REPO", "")


_config: CodeIntelConfig | None = None


def get_code_intel_config() -> CodeIntelConfig:
    global _config
    if _config is None:
        _config = CodeIntelConfig()
    return _config
