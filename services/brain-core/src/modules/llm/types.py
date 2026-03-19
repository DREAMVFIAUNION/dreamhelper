"""LLM 网关核心数据结构（第三章 3.2）"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LLMRequest:
    messages: List[Dict[str, str]]
    model: str = "abab6.5s-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = True
    tools: Optional[List[dict]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    thinking: str = ""


@dataclass
class ProviderConfig:
    name: str
    api_key: str
    base_url: str
    models: List[str]
    weight: int = 1
    max_retries: int = 3
    timeout: float = 30.0
    enabled: bool = True
