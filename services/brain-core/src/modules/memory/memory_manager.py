"""记忆管理器 — 短期会话记忆(Redis) + 长期用户事实记忆(PostgreSQL) + Hook 事件

Phase 8: Redis 短期 + PostgreSQL 长期持久化
Phase 9: 语义向量化长期记忆 — Embedding + 余弦相似度检索
"""

import asyncio
import math
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from .redis_store import get_session_store, RedisSessionStore
from . import db as memory_db

logger = logging.getLogger("memory.manager")


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class MemoryItem:
    content: str
    role: str  # "user" | "assistant" | "system"
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)
    session_id: str = ""


@dataclass
class UserFact:
    """长期用户事实记忆 — 跨会话持久"""
    key: str          # 如 "name", "occupation", "preference_language"
    value: str        # 如 "王森冉", "程序员", "中文"
    confidence: float = 1.0
    source: str = ""  # 来源会话 ID
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class MemoryManager:
    """管理短期会话记忆(Redis) + 长期用户事实记忆(PostgreSQL)

    短期记忆: Redis list per session, 24h TTL, 自动降级到内存
    长期记忆: PostgreSQL user_memories 表 + 内存热缓存
    """

    def __init__(self):
        self._store: RedisSessionStore = get_session_store()
        # 长期记忆内存缓存（DB 为 source of truth）
        self._fact_cache: Dict[str, Dict[str, UserFact]] = defaultdict(dict)
        self._cache_loaded: set[str] = set()

    # ── 初始化 / 预热 ──

    async def warm_up(self, max_users: int = 100):
        """启动时从 DB 预热活跃用户的长期记忆到缓存"""
        try:
            data = await memory_db.get_active_user_facts(limit=max_users)
            for uid, facts in data.items():
                for f in facts:
                    self._fact_cache[uid][f["key"]] = UserFact(
                        key=f["key"], value=f["value"],
                        confidence=f["confidence"], source=f["source"],
                    )
                self._cache_loaded.add(uid)
            logger.info("[MemoryManager] Warmed up %d users with %d facts",
                        len(data), sum(len(v) for v in data.values()))
        except Exception as e:
            logger.warning("[MemoryManager] Warm-up failed: %s", e)

    # ── 短期记忆（会话级 — Redis）──

    async def set_session_owner(self, session_id: str, user_id: str):
        """P0-#3: 记录会话归属用户"""
        await self._store.set_session_owner(session_id, user_id)

    async def get_session_owner(self, session_id: str) -> str | None:
        """P0-#3: 获取会话归属用户"""
        return await self._store.get_session_owner(session_id)

    async def add_message(self, session_id: str, role: str, content: str, metadata: dict | None = None):
        """添加一条会话消息到短期记忆 (Redis)"""
        await self._store.add_message(session_id, role, content, metadata)

    async def get_session_history(self, session_id: str, limit: int = 40) -> List[dict]:
        """获取会话历史（返回 messages 格式）"""
        return await self._store.get_history(session_id, limit)

    async def get_session_context(self, session_id: str, max_messages: int = 20) -> str:
        """获取会话上下文摘要（用于注入 system prompt）"""
        return await self._store.get_context(session_id, max_messages)

    async def clear_session(self, session_id: str):
        """清除会话记忆"""
        await self._store.clear_session(session_id)

    async def get_session_summary(self, session_id: str) -> str:
        """获取会话摘要缓存"""
        r = None
        try:
            from .redis_store import get_redis, SUMMARY_KEY_PREFIX
            r = await get_redis()
        except Exception:
            pass
        if r:
            cached = await r.get(SUMMARY_KEY_PREFIX + session_id)
            return cached or ""
        return self._store._mem_summaries.get(session_id, "")

    async def set_session_summary(self, session_id: str, summary: str):
        """设置会话摘要缓存"""
        await self._store.set_summary(session_id, summary)

    # ── 长期记忆（用户级 — PostgreSQL + 缓存）──

    async def _ensure_cache(self, user_id: str):
        """确保用户的长期记忆已加载到缓存"""
        if user_id in self._cache_loaded:
            return
        try:
            facts = await memory_db.get_all_facts(user_id)
            for f in facts:
                self._fact_cache[user_id][f["key"]] = UserFact(
                    key=f["key"], value=f["value"],
                    confidence=f["confidence"], source=f["source"],
                )
            self._cache_loaded.add(user_id)
        except Exception as e:
            logger.warning("[MemoryManager] Failed to load facts for %s: %s", user_id, e)

    async def set_user_fact(self, user_id: str, key: str, value: str,
                            confidence: float = 1.0, source: str = ""):
        """设置/更新用户事实 — 写入 DB(含 embedding) + 更新缓存"""
        # 生成 embedding 向量（异步，失败不阻塞）
        embedding = None
        try:
            from ..llm.embedding.embedding_provider import get_embedding_provider
            embedder = get_embedding_provider()
            text = f"{key}: {value}"
            embedding = await embedder.embed_single(text)
        except Exception as e:
            logger.debug("[MemoryManager] Embedding generation skipped: %s", e)

        # DB 写入
        try:
            if embedding:
                await memory_db.upsert_fact_with_embedding(
                    user_id, key, value, embedding, confidence, source,
                )
            else:
                await memory_db.upsert_fact(user_id, key, value, confidence, source)
        except Exception as e:
            logger.error("[MemoryManager] DB upsert failed for %s/%s: %s", user_id, key, e)

        # 缓存更新
        existing = self._fact_cache[user_id].get(key)
        if existing:
            existing.value = value
            existing.confidence = confidence
            existing.updated_at = time.time()
            if source:
                existing.source = source
        else:
            self._fact_cache[user_id][key] = UserFact(
                key=key, value=value, confidence=confidence, source=source,
            )
        self._cache_loaded.add(user_id)

        # Hook: 记忆更新事件
        asyncio.create_task(self._emit_memory_update(user_id, key, value))

    async def get_user_fact(self, user_id: str, key: str) -> Optional[str]:
        """获取单个用户事实"""
        await self._ensure_cache(user_id)
        fact = self._fact_cache.get(user_id, {}).get(key)
        return fact.value if fact else None

    async def get_all_user_facts(self, user_id: str) -> Dict[str, str]:
        """获取用户所有事实记忆"""
        await self._ensure_cache(user_id)
        facts = self._fact_cache.get(user_id, {})
        return {k: v.value for k, v in facts.items()}

    async def get_user_profile_prompt(self, user_id: str) -> str:
        """将用户事实格式化为 system prompt 片段"""
        facts = await self.get_all_user_facts(user_id)
        if not facts:
            return ""
        lines = ["[用户画像]"]
        for k, v in facts.items():
            lines.append(f"- {k}: {v}")
        return "\n".join(lines)

    async def delete_user_fact(self, user_id: str, key: str):
        """删除用户事实"""
        try:
            await memory_db.delete_fact(user_id, key)
        except Exception as e:
            logger.error("[MemoryManager] DB delete failed for %s/%s: %s", user_id, key, e)
        self._fact_cache.get(user_id, {}).pop(key, None)
        asyncio.create_task(self._emit_memory_update(user_id, key, None))

    async def delete_all_user_facts(self, user_id: str) -> int:
        """删除用户所有事实"""
        try:
            count = await memory_db.delete_all_facts(user_id)
        except Exception as e:
            logger.error("[MemoryManager] DB delete_all failed for %s: %s", user_id, e)
            count = len(self._fact_cache.get(user_id, {}))
        self._fact_cache.pop(user_id, None)
        self._cache_loaded.discard(user_id)
        return count

    # ── 语义检索（向量化长期记忆）──

    async def semantic_search(
        self, user_id: str, query: str, top_k: int = 5, min_score: float = 0.3,
    ) -> list[dict]:
        """语义检索用户记忆 — 用 embedding 余弦相似度排序

        Returns: [{"key": ..., "value": ..., "score": float, "confidence": float}]
        """
        # 1. 生成 query embedding
        try:
            from ..llm.embedding.embedding_provider import get_embedding_provider
            embedder = get_embedding_provider()
            query_embedding = await embedder.embed_single(query)
        except Exception as e:
            logger.warning("[MemoryManager] Semantic search: embedding failed: %s", e)
            return []

        # 检查是否为零向量（API key 未配置时的 fallback）
        if all(v == 0.0 for v in query_embedding[:10]):
            logger.debug("[MemoryManager] Semantic search: zero embedding, falling back to keyword")
            return await self._keyword_search(user_id, query, top_k)

        # 2. 获取带 embedding 的所有记忆
        try:
            facts = await memory_db.get_all_facts_with_embeddings(user_id)
        except Exception as e:
            logger.warning("[MemoryManager] Semantic search: DB fetch failed: %s", e)
            return []

        # 3. 计算余弦相似度并排序
        scored = []
        for f in facts:
            emb = f.get("embedding")
            if not emb:
                continue
            score = _cosine_similarity(query_embedding, emb)
            if score >= min_score:
                scored.append({
                    "key": f["key"],
                    "value": f["value"],
                    "score": round(score, 4),
                    "confidence": f["confidence"],
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    async def _keyword_search(
        self, user_id: str, query: str, top_k: int = 5,
    ) -> list[dict]:
        """关键词降级检索 — embedding 不可用时的 fallback"""
        await self._ensure_cache(user_id)
        facts = self._fact_cache.get(user_id, {})
        query_lower = query.lower()
        results = []
        for key, fact in facts.items():
            text = f"{key} {fact.value}".lower()
            if any(w in text for w in query_lower.split() if len(w) >= 2):
                results.append({
                    "key": key, "value": fact.value,
                    "score": 0.5, "confidence": fact.confidence,
                })
        return results[:top_k]

    async def get_semantic_profile_prompt(
        self, user_id: str, query: str, top_k: int = 5,
    ) -> str:
        """语义检索相关记忆并格式化为 prompt 片段"""
        results = await self.semantic_search(user_id, query, top_k=top_k)
        if not results:
            return await self.get_user_profile_prompt(user_id)

        lines = ["[用户记忆 — 与当前对话相关]"]
        for r in results:
            score_label = "高度相关" if r["score"] >= 0.7 else "可能相关"
            lines.append(f"- {r['key']}: {r['value']} ({score_label})")

        # 补充不在语义结果中的核心事实（如 name、occupation）
        all_facts = await self.get_all_user_facts(user_id)
        core_keys = {"name", "occupation", "language", "preference_language", "location"}
        matched_keys = {r["key"] for r in results}
        for ck in core_keys:
            if ck in all_facts and ck not in matched_keys:
                lines.append(f"- {ck}: {all_facts[ck]}")

        return "\n".join(lines)

    @staticmethod
    async def _emit_memory_update(user_id: str, key: str, value: str | None):
        """Hook: 触发记忆更新事件"""
        try:
            from ..hooks.hook_registry import HookRegistry, HookEventType
            await HookRegistry.emit(HookEventType.MEMORY_UPDATE, {
                "user_id": user_id, "key": key, "value": value,
            })
        except Exception:
            pass  # Hook 失败不影响主流程

    # ── 统计 ──

    async def get_stats(self) -> dict:
        session_stats = await self._store.get_stats()
        return {
            **session_stats,
            "users_with_facts": len(self._fact_cache),
            "total_facts": sum(len(v) for v in self._fact_cache.values()),
            "cache_loaded_users": len(self._cache_loaded),
        }


# 全局单例
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
