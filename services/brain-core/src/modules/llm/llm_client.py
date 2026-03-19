"""LLM 客户端 — 统一入口（第三章 3.8）"""

import logging
from typing import AsyncGenerator, List
from .types import LLMRequest, LLMResponse
from .providers.base_provider import BaseProvider
from .providers.minimax_provider import MiniMaxProvider
from .providers.openai_provider import OpenAIProvider
from .providers.deepseek_provider import DeepSeekProvider
from .providers.qwen_provider import QwenProvider
from .providers.glm_provider import GLMProvider
from .providers.kimi_provider import KimiProvider
from .providers.nvidia_provider import NvidiaProvider
from ...common.config import settings

logger = logging.getLogger(__name__)

# 全局单例
_llm_client: "LLMClient | None" = None


def get_llm_client() -> "LLMClient":
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


class LLMClient:
    """所有 LLM 调用的统一入口 — 支持多提供商"""

    def __init__(self):
        self.providers: List[BaseProvider] = []

        # MiniMax (有 API Key 才注册)
        if settings.MINIMAX_API_KEY:
            self.providers.append(MiniMaxProvider(api_key=settings.MINIMAX_API_KEY))

        # OpenAI (按需注册)
        if settings.OPENAI_API_KEY:
            self.providers.append(OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
            ))

        # DeepSeek (按需注册)
        if settings.DEEPSEEK_API_KEY:
            self.providers.append(DeepSeekProvider(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
            ))

        # Qwen (按需注册)
        if settings.QWEN_API_KEY:
            self.providers.append(QwenProvider(
                api_key=settings.QWEN_API_KEY,
                base_url=settings.QWEN_BASE_URL,
            ))

        # GLM / 智谱 (按需注册)
        if settings.GLM_API_KEY:
            self.providers.append(GLMProvider(
                api_key=settings.GLM_API_KEY,
                base_url=settings.GLM_BASE_URL,
            ))

        # Kimi / Moonshot AI (按需注册)
        if settings.KIMI_API_KEY:
            self.providers.append(KimiProvider(
                api_key=settings.KIMI_API_KEY,
                base_url=settings.KIMI_BASE_URL,
            ))

        # NVIDIA NIM (按需注册 — 免费无限量)
        if settings.NVIDIA_API_KEY:
            self.providers.append(NvidiaProvider(
                api_key=settings.NVIDIA_API_KEY,
                base_url=settings.NVIDIA_BASE_URL,
            ))

        provider_names = [p.name for p in self.providers]
        if not self.providers:
            logger.warning("No LLM providers registered! Check API keys in .env")
        else:
            logger.info("LLM providers: %s", provider_names)

    def _get_provider(self, model: str) -> BaseProvider:
        """智能路由: NVIDIA(免费) 优先 → 原厂(付费) → fallback"""
        nvidia_provider = None
        original_provider = None

        for provider in self.providers:
            if provider.supports_model(model):
                if provider.name == "nvidia":
                    nvidia_provider = provider
                else:
                    original_provider = provider

        # NVIDIA 免费通道优先
        if nvidia_provider:
            return nvidia_provider
        if original_provider:
            return original_provider
        # fallback: 使用第一个 provider
        if self.providers:
            return self.providers[0]
        raise ValueError(f"No provider supports model: {model}")

    def list_models(self) -> List[dict]:
        """列出所有可用模型"""
        models = []
        for p in self.providers:
            from .providers.minimax_provider import MINIMAX_MODELS
            from .providers.openai_provider import OPENAI_MODELS
            from .providers.deepseek_provider import DEEPSEEK_MODELS
            from .providers.qwen_provider import QWEN_MODELS

            if p.name == "minimax":
                for m in MINIMAX_MODELS:
                    models.append({"id": m, "provider": "minimax"})
            elif p.name == "openai":
                for m in OPENAI_MODELS:
                    models.append({"id": m, "provider": "openai"})
            elif p.name == "deepseek":
                for m in DEEPSEEK_MODELS:
                    models.append({"id": m, "provider": "deepseek"})
            elif p.name == "qwen":
                for m in QWEN_MODELS:
                    models.append({"id": m, "provider": "qwen"})
            elif p.name == "glm":
                from .providers.glm_provider import GLM_MODELS
                for m in GLM_MODELS:
                    models.append({"id": m, "provider": "glm"})
            elif p.name == "kimi":
                from .providers.kimi_provider import KIMI_MODELS
                for m in KIMI_MODELS:
                    models.append({"id": m, "provider": "kimi"})
            elif p.name == "nvidia":
                from .providers.nvidia_provider import NVIDIA_MODELS
                for m in NVIDIA_MODELS:
                    models.append({"id": m, "provider": "nvidia"})
        return models

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """非流式补全"""
        provider = self._get_provider(request.model)
        return await provider.complete(request)

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """流式补全"""
        provider = self._get_provider(request.model)
        async for chunk in provider.stream(request):
            yield chunk
