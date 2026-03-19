"""批量 Embedding（第五章 5.5.1）"""

import asyncio
from typing import List

from .embedding_provider import get_embedding_provider


class BatchEmbedder:
    """批量文本向量化，支持自动攒批"""

    def __init__(self, batch_size: int = 32, max_wait_ms: float = 100.0):
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """批量向量化"""
        results = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_result = await self._embed_batch(batch)
            results.extend(batch_result)
        return results

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """单批次向量化 — 调用 EmbeddingProvider"""
        provider = get_embedding_provider()
        return await provider.embed(texts)
