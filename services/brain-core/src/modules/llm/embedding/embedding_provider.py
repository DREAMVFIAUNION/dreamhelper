"""Embedding 提供商 — 支持 MiniMax / OpenAI 兼容接口"""

import httpx
from typing import List

from ....common.config import settings


class EmbeddingProvider:
    """统一 Embedding 接口，支持多提供商"""

    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.dim = settings.EMBEDDING_DIM

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """批量文本向量化"""
        if not texts:
            return []

        if self.provider == "openai":
            return await self._embed_openai(texts)
        elif self.provider == "minimax":
            return await self._embed_minimax(texts)
        else:
            # fallback: 零向量（开发模式）
            return [[0.0] * self.dim for _ in texts]

    async def embed_single(self, text: str) -> List[float]:
        """单文本向量化"""
        results = await self.embed([text])
        return results[0] if results else [0.0] * self.dim

    async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """OpenAI 兼容 Embedding API（也兼容 DeepSeek 等）"""
        api_key = settings.OPENAI_API_KEY
        base_url = settings.OPENAI_BASE_URL.rstrip("/")
        if not api_key:
            print("[Embedding] OPENAI_API_KEY not set, returning zeros")
            return [[0.0] * self.dim for _ in texts]

        url = f"{base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "text-embedding-3-small",
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        embeddings = [item["embedding"] for item in data["data"]]
        return embeddings

    async def _embed_minimax(self, texts: List[str]) -> List[List[float]]:
        """MiniMax Embedding API"""
        api_key = settings.MINIMAX_API_KEY
        if not api_key:
            print("[Embedding] MINIMAX_API_KEY not set, returning zeros")
            return [[0.0] * self.dim for _ in texts]

        url = "https://api.minimaxi.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "embo-01",
            "texts": texts,
            "type": "db",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        vectors = data.get("vectors", [])
        if len(vectors) != len(texts):
            # API 格式可能不同，尝试其他字段
            embeddings_data = data.get("data", [])
            if embeddings_data:
                vectors = [item.get("embedding", [0.0] * self.dim) for item in embeddings_data]
            else:
                vectors = [[0.0] * self.dim for _ in texts]

        return vectors


# 全局单例
_embedding_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _embedding_provider
    if _embedding_provider is None:
        _embedding_provider = EmbeddingProvider()
    return _embedding_provider
