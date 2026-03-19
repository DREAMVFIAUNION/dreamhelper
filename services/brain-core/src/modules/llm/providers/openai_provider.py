"""OpenAI 兼容提供商 — 支持 OpenAI / DeepSeek / GLM 等兼容 API"""

import json
import time
import httpx
from typing import AsyncGenerator

from .base_provider import BaseProvider
from ..types import LLMRequest, LLMResponse


OPENAI_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]


class OpenAIProvider(BaseProvider):
    """OpenAI API 提供商"""

    name = "openai"

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def supports_model(self, model: str) -> bool:
        return model in OPENAI_MODELS

    def _build_body(self, request: LLMRequest, stream: bool = False) -> dict:
        messages = []
        for msg in request.messages:
            messages.append({"role": msg["role"], "content": msg["content"]})

        body: dict = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": stream,
        }
        return body

    async def complete(self, request: LLMRequest) -> LLMResponse:
        start = time.time()
        body = self._build_body(request, stream=False)
        url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, headers=self.headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        content = choice["message"]["content"] or ""
        usage = data.get("usage", {})
        latency = (time.time() - start) * 1000

        return LLMResponse(
            content=content,
            model=request.model,
            provider=self.name,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
            finish_reason=choice.get("finish_reason", "stop"),
            latency_ms=latency,
        )

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
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
                            }},
                            ensure_ascii=False,
                        )
