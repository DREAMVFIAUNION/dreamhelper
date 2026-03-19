"""NVIDIA NIM 提供商 — 继承 OpenAI 兼容接口

NVIDIA NIM API:
  Base URL: https://integrate.api.nvidia.com/v1
  Auth: Authorization: Bearer nvapi-xxx
  格式: 完全兼容 OpenAI /chat/completions

特性:
  - 免费无限量调用
  - 覆盖 GLM-5 / Qwen-3.5 / Kimi-K2.5 / Nemotron 系列
  - 支持 VLM (视觉语言模型)
  - 支持 1M token 上下文 (Nemotron-Nano-30B)
"""

import json
import time
from typing import AsyncGenerator

from .openai_provider import OpenAIProvider
from ..types import LLMRequest, LLMResponse


# ── NVIDIA NIM 上可用的模型 ──────────────────────────────
NVIDIA_MODELS = [
    # 推理/对话
    "z-ai/glm5",                                    # GLM-5 744B MoE
    "qwen/qwen3.5-397b-a17b",                       # Qwen 3.5 397B VLM
    "moonshotai/kimi-k2.5",                          # Kimi K2.5 1T MoE
    "nvidia/llama-3.1-nemotron-ultra-253b-v1",       # Nemotron Ultra 253B
    "nvidia/nemotron-3-nano-30b-a3b",                # Nemotron Nano 30B (1M ctx)
    # 视觉/多模态
    "nvidia/nemotron-nano-12b-v2-vl",                # Nemotron VL 12B
    "nvidia/cosmos-reason2-8b",                      # Cosmos 物理世界推理
    # Embedding
    "nvidia/llama-nemotron-embed-vl-1b-v2",          # 多模态 Embedding
]

# 推理模型（有 reasoning_content，需要更多 max_tokens）
NVIDIA_REASONING_MODELS = {"z-ai/glm5"}

# 视觉模型（支持图片输入）
NVIDIA_VISION_MODELS = {
    "qwen/qwen3.5-397b-a17b",
    "nvidia/nemotron-nano-12b-v2-vl",
    "nvidia/cosmos-reason2-8b",
    "moonshotai/kimi-k2.5",
}

# 超长上下文模型
NVIDIA_LONG_CONTEXT_MODELS = {
    "nvidia/nemotron-3-nano-30b-a3b": 1_000_000,  # 1M tokens
    "z-ai/glm5": 128_000,
    "qwen/qwen3.5-397b-a17b": 131_072,
    "moonshotai/kimi-k2.5": 131_072,
}

# 推理模型最少 max_tokens
NVIDIA_REASONING_MIN_TOKENS = 8192


class NvidiaProvider(OpenAIProvider):
    """NVIDIA NIM API（OpenAI 兼容格式，免费无限量）"""

    name = "nvidia"

    def __init__(self, api_key: str, base_url: str = "https://integrate.api.nvidia.com/v1"):
        super().__init__(api_key=api_key, base_url=base_url)

    def supports_model(self, model: str) -> bool:
        return model in NVIDIA_MODELS

    def _build_body(self, request: LLMRequest, stream: bool = False) -> dict:
        """构建请求体 — 推理/长上下文模型自动调参"""
        body = super()._build_body(request, stream)

        # 推理模型: 确保足够 max_tokens
        if request.model in NVIDIA_REASONING_MODELS and body.get("max_tokens", 0) < NVIDIA_REASONING_MIN_TOKENS:
            body["max_tokens"] = NVIDIA_REASONING_MIN_TOKENS

        # 长上下文模型: 默认至少 4096 max_tokens
        max_ctx = NVIDIA_LONG_CONTEXT_MODELS.get(request.model)
        if max_ctx and body.get("max_tokens", 0) < 4096:
            body["max_tokens"] = 4096

        return body

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """非流式补全 — 推理模型提取 reasoning_content"""
        start = time.time()
        body = self._build_body(request, stream=False)
        url = f"{self.base_url}/chat/completions"

        import httpx
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, headers=self.headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        message = choice.get("message", {})
        content = message.get("content") or ""
        reasoning = message.get("reasoning_content") or ""
        usage = data.get("usage") or {}
        latency = (time.time() - start) * 1000

        response = LLMResponse(
            content=content,
            model=request.model,
            provider=self.name,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
            },
            finish_reason=choice.get("finish_reason", "stop"),
            latency_ms=latency,
        )
        # 推理模型附加思维链
        if reasoning and request.model in NVIDIA_REASONING_MODELS:
            response.thinking = reasoning
        return response

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """流式补全 — 推理模型额外输出 reasoning_content"""
        is_reasoning = request.model in NVIDIA_REASONING_MODELS

        body = self._build_body(request, stream=True)
        url = f"{self.base_url}/chat/completions"

        import httpx
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=self.headers, json=body) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload == "[DONE]":
                        yield json.dumps({"type": "done", "usage": {}}, ensure_ascii=False)
                        return

                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    if not isinstance(event, dict):
                        continue

                    choice = (event.get("choices") or [{}])[0] or {}
                    delta = choice.get("delta") or {}

                    # 推理模型: 输出思维链
                    if is_reasoning:
                        reasoning = delta.get("reasoning_content", "")
                        if reasoning:
                            yield json.dumps(
                                {"type": "thinking", "content": reasoning},
                                ensure_ascii=False,
                            )

                    # 正常内容输出
                    content = delta.get("content", "")
                    if content:
                        yield json.dumps(
                            {"type": "chunk", "content": content},
                            ensure_ascii=False,
                        )

                    if choice.get("finish_reason"):
                        usage = event.get("usage") or {}
                        yield json.dumps(
                            {"type": "done", "usage": {
                                "completion_tokens": usage.get("completion_tokens", 0),
                                "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
                            }},
                            ensure_ascii=False,
                        )
