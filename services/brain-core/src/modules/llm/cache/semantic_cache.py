"""语义缓存 — Redis Hash + 可选向量相似度

两层策略:
1. 精确缓存: SHA-256(normalize(query)+model) → Redis STRING, TTL 1h
2. 语义缓存: (未来) Embedding → Milvus cosine > threshold → 命中

适用于:
- 完全相同的问题 (精确命中率高)
- 短时间内重复请求 (API 成本节省)
"""

import hashlib
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 全局单例
_instance: Optional["SemanticCache"] = None


def get_semantic_cache() -> "SemanticCache":
    global _instance
    if _instance is None:
        _instance = SemanticCache()
    return _instance


class SemanticCache:
    """Redis-backed LLM response cache"""

    def __init__(
        self,
        similarity_threshold: float = 0.95,
        default_ttl: int = 3600,
        key_prefix: str = "llm_cache:",
    ):
        self.similarity_threshold = similarity_threshold
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self._redis = None
        self._hits = 0
        self._misses = 0

    async def _get_redis(self):
        """惰性连接 Redis"""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                from src.common.config import settings
                self._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                )
                await self._redis.ping()
                logger.info("[SemanticCache] Redis connected")
            except Exception as e:
                logger.warning(f"[SemanticCache] Redis unavailable, cache disabled: {e}")
                self._redis = None
        return self._redis

    @staticmethod
    def _normalize(query: str) -> str:
        """规范化查询: 去首尾空格、转小写、压缩空格"""
        return " ".join(query.strip().lower().split())

    def _make_key(self, query: str, model: str = "") -> str:
        """生成缓存键: prefix + SHA-256(normalized_query + model)"""
        normalized = self._normalize(query)
        raw = f"{normalized}||{model}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        return f"{self.key_prefix}{digest}"

    async def get(self, query: str, model: str = "") -> Optional[str]:
        """查找精确缓存"""
        redis = await self._get_redis()
        if redis is None:
            return None
        try:
            key = self._make_key(query, model)
            cached = await redis.get(key)
            if cached:
                self._hits += 1
                logger.debug(f"[SemanticCache] HIT key={key[:20]}...")
                return cached
            self._misses += 1
            return None
        except Exception as e:
            logger.warning(f"[SemanticCache] get error: {e}")
            return None

    async def set(self, query: str, response: str, model: str = "", ttl: int = 0):
        """存入精确缓存"""
        redis = await self._get_redis()
        if redis is None:
            return
        try:
            key = self._make_key(query, model)
            await redis.set(key, response, ex=ttl or self.default_ttl)
            logger.debug(f"[SemanticCache] SET key={key[:20]}... ttl={ttl or self.default_ttl}")
        except Exception as e:
            logger.warning(f"[SemanticCache] set error: {e}")

    async def invalidate(self, query: str, model: str = ""):
        """手动使某条缓存失效"""
        redis = await self._get_redis()
        if redis is None:
            return
        try:
            key = self._make_key(query, model)
            await redis.delete(key)
        except Exception:
            pass

    def stats(self) -> dict:
        """返回缓存命中统计"""
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0,
            "total": total,
        }
