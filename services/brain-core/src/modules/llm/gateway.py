"""LLM 网关 — 统一中间件链（Phase 11）

请求流程:
  Request → RateLimiter → Cache Check → CircuitBreaker → Router → Provider → Cache Set → Response
                                                                     ↓ (失败)
                                                              Fallback Provider → Response

集成组件:
- TokenBucketRateLimiter: 按用户/全局限流
- SemanticCache: Redis 精确缓存命中
- CircuitBreaker: 按提供商熔断
- LLMRouter: 多策略路由 (cost/latency/fallback)
"""

import logging
import time
from typing import AsyncGenerator, Optional

from .types import LLMRequest, LLMResponse
from .providers.base_provider import BaseProvider
from .router.llm_router import LLMRouter
from .router.circuit_breaker import CircuitBreaker
from .middleware.rate_limiter import TokenBucketRateLimiter
from .cache.semantic_cache import get_semantic_cache

logger = logging.getLogger(__name__)

# 全局单例
_gateway: Optional["LLMGateway"] = None


def get_llm_gateway() -> "LLMGateway":
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway


class LLMGateway:
    """LLM 统一网关 — 限流 + 缓存 + 熔断 + 路由"""

    def __init__(
        self,
        rate_limit: float = 30.0,       # 每秒令牌补充速率
        rate_capacity: float = 60.0,     # 令牌桶容量
        route_strategy: str = "cost",    # 路由策略
        cache_enabled: bool = True,      # 是否启用缓存
    ):
        from .llm_client import get_llm_client
        self._client = get_llm_client()
        self._router = LLMRouter(self._client.providers)
        self._rate_limiter = TokenBucketRateLimiter(rate=rate_limit, capacity=rate_capacity)
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._route_strategy = route_strategy
        self._cache_enabled = cache_enabled

        # 统计
        self._total_requests = 0
        self._total_cached = 0
        self._total_errors = 0
        self._total_rate_limited = 0

        logger.info(
            f"[LLMGateway] initialized: strategy={route_strategy}, "
            f"cache={cache_enabled}, rate={rate_limit}/s"
        )

    def _get_circuit_breaker(self, provider_name: str) -> CircuitBreaker:
        if provider_name not in self._circuit_breakers:
            self._circuit_breakers[provider_name] = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30.0,
            )
        return self._circuit_breakers[provider_name]

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """非流式补全 — 走完整中间件链"""
        self._total_requests += 1

        # 1. 限流检查
        allowed, wait_time = self._rate_limiter.try_acquire()
        if not allowed:
            self._total_rate_limited += 1
            logger.warning(f"[LLMGateway] Rate limited, wait={wait_time:.1f}s")
            import asyncio
            await asyncio.sleep(min(wait_time, 2.0))
            # 重试一次
            allowed, _ = self._rate_limiter.try_acquire()
            if not allowed:
                return LLMResponse(
                    content="服务繁忙，请稍后再试。",
                    model=request.model,
                    provider="gateway",
                    usage={},
                    finish_reason="rate_limited",
                )

        # 2. 缓存检查（仅非流式 + 非工具调用）
        if self._cache_enabled and not request.tools:
            cache = get_semantic_cache()
            query_text = request.messages[-1]["content"] if request.messages else ""
            cached = await cache.get(query_text, request.model)
            if cached:
                self._total_cached += 1
                logger.debug(f"[LLMGateway] Cache HIT for model={request.model}")
                return LLMResponse(
                    content=cached,
                    model=request.model,
                    provider="cache",
                    usage={"cached": True},
                    finish_reason="cache_hit",
                )

        # 3. 路由选择提供商
        provider = self._router.route(request.model, self._route_strategy)
        if provider is None:
            return LLMResponse(
                content="没有可用的 LLM 提供商。",
                model=request.model,
                provider="gateway",
                finish_reason="no_provider",
            )

        # 4. 熔断检查 + 执行
        response = await self._execute_with_fallback(request, provider)

        # 5. 缓存写入
        if (
            self._cache_enabled
            and not request.tools
            and response.finish_reason not in ("error", "rate_limited", "no_provider")
        ):
            try:
                cache = get_semantic_cache()
                query_text = request.messages[-1]["content"] if request.messages else ""
                await cache.set(query_text, response.content, request.model)
            except Exception:
                pass

        return response

    async def _execute_with_fallback(
        self, request: LLMRequest, primary: BaseProvider
    ) -> LLMResponse:
        """执行请求，带熔断 + 自动降级"""
        providers_tried = []

        # 尝试 primary
        cb = self._get_circuit_breaker(primary.name)
        if cb.can_execute():
            result = await self._try_provider(request, primary)
            if result is not None:
                return result
        providers_tried.append(primary.name)

        # 尝试其他提供商作为 fallback
        for p in self._client.providers:
            if p.name in providers_tried:
                continue
            cb = self._get_circuit_breaker(p.name)
            if not cb.can_execute():
                continue
            logger.info(f"[LLMGateway] Falling back to {p.name}")
            result = await self._try_provider(request, p)
            if result is not None:
                return result
            providers_tried.append(p.name)

        # 全部失败
        self._total_errors += 1
        return LLMResponse(
            content="所有 LLM 提供商暂时不可用，请稍后重试。",
            model=request.model,
            provider="gateway",
            finish_reason="error",
        )

    async def _try_provider(
        self, request: LLMRequest, provider: BaseProvider
    ) -> Optional[LLMResponse]:
        """尝试单个提供商，返回 None 表示失败"""
        cb = self._get_circuit_breaker(provider.name)
        start = time.time()
        try:
            response = await provider.complete(request)
            latency_ms = (time.time() - start) * 1000
            cb.record_success()
            self._router.record_success(provider.name)
            self._router.record_latency(provider.name, latency_ms)
            response.latency_ms = latency_ms
            return response
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            logger.warning(f"[LLMGateway] {provider.name} failed ({latency_ms:.0f}ms): {e}")
            cb.record_failure()
            self._router.record_error(provider.name)
            self._router.record_latency(provider.name, latency_ms)
            return None

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """流式补全 — 限流 + 熔断（不走缓存）"""
        self._total_requests += 1

        # 限流
        allowed, wait_time = self._rate_limiter.try_acquire()
        if not allowed:
            self._total_rate_limited += 1
            import asyncio
            await asyncio.sleep(min(wait_time, 2.0))

        # 路由
        provider = self._router.route(request.model, self._route_strategy)
        if provider is None:
            yield "没有可用的 LLM 提供商。"
            return

        # 尝试执行（带 fallback）
        providers_tried = []

        for p in [provider] + [pp for pp in self._client.providers if pp.name != provider.name]:
            if p.name in providers_tried:
                continue
            cb = self._get_circuit_breaker(p.name)
            if not cb.can_execute():
                providers_tried.append(p.name)
                continue

            try:
                start = time.time()
                async for chunk in p.stream(request):
                    yield chunk
                latency_ms = (time.time() - start) * 1000
                cb.record_success()
                self._router.record_success(p.name)
                self._router.record_latency(p.name, latency_ms)
                return
            except Exception as e:
                logger.warning(f"[LLMGateway] stream {p.name} failed: {e}")
                cb.record_failure()
                self._router.record_error(p.name)
                providers_tried.append(p.name)

        yield "所有 LLM 提供商暂时不可用。"

    def get_stats(self) -> dict:
        """网关统计"""
        cache = get_semantic_cache()
        return {
            "total_requests": self._total_requests,
            "cached_responses": self._total_cached,
            "errors": self._total_errors,
            "rate_limited": self._total_rate_limited,
            "route_strategy": self._route_strategy,
            "router": self._router.get_stats(),
            "cache": cache.stats(),
            "circuit_breakers": {
                name: {
                    "state": cb.state.value,
                    "failures": cb._failure_count,
                }
                for name, cb in self._circuit_breakers.items()
            },
        }
