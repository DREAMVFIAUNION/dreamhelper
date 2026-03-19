"""LLM 智能路由器 — 多策略提供商选择（Phase 11）

路由策略:
- cost:     优先选择成本最低的提供商
- latency:  优先选择最近延迟最低的提供商
- fallback: 按注册顺序尝试，失败自动降级
"""

import logging
import time
from typing import List, Optional
from ..providers.base_provider import BaseProvider
from ..types import ProviderConfig

logger = logging.getLogger(__name__)

# 提供商成本评分（越低越优先）
COST_SCORES: dict[str, float] = {
    "minimax": 1.0,
    "deepseek": 1.5,
    "openai": 3.0,
}


class LLMRouter:
    """根据模型、成本、延迟、可用性选择最优提供商"""

    def __init__(self, providers: List[BaseProvider]):
        self._providers = {p.name: p for p in providers}
        self._latency: dict[str, float] = {}       # provider_name → avg latency ms
        self._error_count: dict[str, int] = {}      # provider_name → recent errors

    def route(self, model: str, strategy: str = "cost") -> Optional[BaseProvider]:
        """选择最优提供商"""
        candidates = [p for p in self._providers.values() if p.supports_model(model)]
        if not candidates:
            # fallback: 支持任意模型的第一个提供商
            return list(self._providers.values())[0] if self._providers else None

        # 过滤掉错误过多的提供商（>10 连续错误暂时跳过）
        healthy = [p for p in candidates if self._error_count.get(p.name, 0) < 10]
        if not healthy:
            healthy = candidates  # 全部不健康则放开

        if strategy == "cost":
            healthy.sort(key=lambda p: COST_SCORES.get(p.name, 5.0))
            return healthy[0]

        if strategy == "latency":
            healthy.sort(key=lambda p: self._latency.get(p.name, 999.0))
            return healthy[0]

        # fallback: 按注册顺序
        return healthy[0]

    def record_latency(self, provider_name: str, latency_ms: float):
        """记录延迟（滑动平均）"""
        prev = self._latency.get(provider_name, latency_ms)
        self._latency[provider_name] = prev * 0.7 + latency_ms * 0.3

    def record_success(self, provider_name: str):
        """记录成功，重置错误计数"""
        self._error_count[provider_name] = 0

    def record_error(self, provider_name: str):
        """记录错误"""
        self._error_count[provider_name] = self._error_count.get(provider_name, 0) + 1

    def get_stats(self) -> dict:
        """路由器状态"""
        return {
            "providers": list(self._providers.keys()),
            "latency": {k: round(v, 1) for k, v in self._latency.items()},
            "errors": dict(self._error_count),
        }
