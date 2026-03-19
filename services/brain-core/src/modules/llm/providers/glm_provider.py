"""智谱 GLM 提供商 — 继承 OpenAI 兼容接口

GLM-4 系列使用 OpenAI 兼容 API：
  Base URL: https://open.bigmodel.cn/api/paas/v4
  Auth: Authorization: Bearer <api_key>

特性:
  - GLM-4.7 是推理模型，流式输出包含 reasoning_content (思维链)
  - 支持 500K token 上下文窗口
  - 需要 max_tokens >= 2048 才能在推理后输出实际内容
"""

import json
import time
import httpx
from typing import AsyncGenerator

from .openai_provider import OpenAIProvider
from ..types import LLMRequest, LLMResponse


GLM_MODELS = [
    "glm-4.7",
    "glm-4.6",
    "glm-4.5",
    "glm-4.5-air",
    "glm-5",
]

# 推理模型 — 流式时有 reasoning_content delta, 需要更多 max_tokens
GLM_REASONING_MODELS = {"glm-4.7", "glm-5"}
GLM_REASONING_MIN_TOKENS = 8192  # 推理模型最少需要 8K tokens


class GLMProvider(OpenAIProvider):
    """智谱 GLM API（OpenAI 兼容格式，GLM-4.7 推理模型 + 500K 上下文）"""

    name = "glm"

    def __init__(self, api_key: str, base_url: str = "https://open.bigmodel.cn/api/paas/v4"):
        super().__init__(api_key=api_key, base_url=base_url)

    def supports_model(self, model: str) -> bool:
        return model in GLM_MODELS

    def _ensure_reasoning_tokens(self, request: LLMRequest) -> LLMRequest:
        """推理模型需要足够的 max_tokens (reasoning + output)"""
        if request.model in GLM_REASONING_MODELS and request.max_tokens < GLM_REASONING_MIN_TOKENS:
            return LLMRequest(
                messages=request.messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=GLM_REASONING_MIN_TOKENS,
                stream=request.stream,
            )
        return request

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """非流式补全 — 推理模型自动提升 max_tokens 并提取 reasoning_content"""
        request = self._ensure_reasoning_tokens(request)
        start = time.time()
        body = self._build_body(request, stream=False)
        url = f"{self.base_url}/chat/completions"

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
        # 附加推理过程到 response 对象
        response.thinking = reasoning
        return response

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """流式补全 — 推理模型额外输出 reasoning_content"""
        request = self._ensure_reasoning_tokens(request)
        is_reasoning = request.model in GLM_REASONING_MODELS

        body = self._build_body(request, stream=True)
        url = f"{self.base_url}/chat/completions"

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

                    # 推理模型: 输出思维链 reasoning_content
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
