"""MiniMax M2.5 提供商 — 通过 httpx 直接调用 Anthropic 兼容接口

MiniMax 要求 Authorization: Bearer <key> 认证方式，
Anthropic SDK 默认使用 x-api-key header 会导致认证失败，
因此改用 httpx 直接发送 HTTP 请求。
"""

import json
import time
import httpx
from typing import AsyncGenerator

from .base_provider import BaseProvider
from ..types import LLMRequest, LLMResponse

MINIMAX_MODELS = [
    "MiniMax-M2.5",
    "MiniMax-M2.5-highspeed",
    "MiniMax-M2.1",
    "MiniMax-M2.1-highspeed",
    "MiniMax-M2",
]

MINIMAX_BASE_URL = "https://api.minimaxi.com/anthropic/v1/messages"


class MiniMaxProvider(BaseProvider):
    """MiniMax LLM 提供商（httpx 直连 + Bearer 认证）"""

    name = "minimax"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def supports_model(self, model: str) -> bool:
        return model in MINIMAX_MODELS

    def _build_body(self, request: LLMRequest, stream: bool = False) -> dict:
        system_prompt = ""
        messages = []
        for msg in request.messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                messages.append({
                    "role": msg["role"],
                    "content": [{"type": "text", "text": msg["content"]}],
                })

        body: dict = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "system": system_prompt or "You are a helpful assistant.",
            "messages": messages,
            "temperature": request.temperature,
        }
        if stream:
            body["stream"] = True
        return body

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """非流式补全"""
        start = time.time()
        body = self._build_body(request, stream=False)

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(MINIMAX_BASE_URL, headers=self.headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        content = ""
        thinking = ""
        for block in data.get("content", []):
            if block.get("type") == "thinking":
                thinking += block.get("thinking", "")
            elif block.get("type") == "text":
                content += block.get("text", "")

        latency = (time.time() - start) * 1000
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=request.model,
            provider=self.name,
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
            },
            finish_reason=data.get("stop_reason", "stop"),
            latency_ms=latency,
        )

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """流式补全 — SSE 解析"""
        body = self._build_body(request, stream=True)

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", MINIMAX_BASE_URL, headers=self.headers, json=body
            ) as resp:
                resp.raise_for_status()
                buffer = ""
                async for raw in resp.aiter_text():
                    buffer += raw
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload == "[DONE]":
                            continue
                        try:
                            event = json.loads(payload)
                        except json.JSONDecodeError:
                            continue

                        evt_type = event.get("type", "")

                        if evt_type == "content_block_delta":
                            delta = event.get("delta", {})
                            delta_type = delta.get("type", "")
                            if delta_type == "thinking_delta":
                                text = delta.get("thinking", "")
                                if text:
                                    yield json.dumps(
                                        {"type": "thinking", "content": text},
                                        ensure_ascii=False,
                                    )
                            elif delta_type == "text_delta":
                                text = delta.get("text", "")
                                if text:
                                    yield json.dumps(
                                        {"type": "chunk", "content": text},
                                        ensure_ascii=False,
                                    )
                        elif evt_type == "message_delta":
                            usage = event.get("usage", {})
                            yield json.dumps(
                                {"type": "done", "usage": {
                                    "completion_tokens": usage.get("output_tokens", 0),
                                }},
                                ensure_ascii=False,
                            )
                        elif evt_type == "error":
                            error_msg = event.get("error", {}).get("message", "Unknown error")
                            yield json.dumps(
                                {"type": "error", "content": error_msg},
                                ensure_ascii=False,
                            )
                            return
