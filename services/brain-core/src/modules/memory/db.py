"""长期用户事实记忆 — asyncpg 持久化层

表映射: user_memories (与 Prisma schema UserMemory 一致)
"""

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

import asyncpg

from ...common.config import settings

logger = logging.getLogger("memory.db")

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None or _pool._closed:
        _pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=2,
            max_size=5,
            command_timeout=30,
        )
    return _pool


async def close_pool():
    global _pool
    if _pool and not _pool._closed:
        await _pool.close()
        _pool = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── CRUD ─────────────────────────────────────────────────

async def upsert_fact(user_id: str, key: str, value: str,
                      confidence: float = 1.0, source: str = "") -> dict:
    """创建或更新用户事实记忆"""
    pool = await get_pool()
    now = _now()
    user_uuid = uuid.UUID(user_id)

    row = await pool.fetchrow(
        """
        INSERT INTO user_memories (id, user_id, key, value, confidence, source, metadata, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, '{}', $7, $7)
        ON CONFLICT (user_id, key)
        DO UPDATE SET value = $4, confidence = $5, source = COALESCE(NULLIF($6, ''), user_memories.source),
                      updated_at = $7
        RETURNING *
        """,
        uuid.uuid4(), user_uuid, key, value, confidence, source, now,
    )
    return _row_to_fact(row)


async def get_fact(user_id: str, key: str) -> Optional[dict]:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM user_memories WHERE user_id = $1 AND key = $2",
        uuid.UUID(user_id), key,
    )
    return _row_to_fact(row) if row else None


async def get_all_facts(user_id: str) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT * FROM user_memories WHERE user_id = $1 ORDER BY updated_at DESC",
        uuid.UUID(user_id),
    )
    return [_row_to_fact(r) for r in rows]


async def delete_fact(user_id: str, key: str) -> bool:
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM user_memories WHERE user_id = $1 AND key = $2",
        uuid.UUID(user_id), key,
    )
    return result == "DELETE 1"


async def delete_all_facts(user_id: str) -> int:
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM user_memories WHERE user_id = $1",
        uuid.UUID(user_id),
    )
    # result = "DELETE N"
    try:
        return int(result.split()[-1])
    except (ValueError, IndexError):
        return 0


async def get_active_user_facts(limit: int = 100) -> dict[str, list[dict]]:
    """获取最近活跃用户的所有事实（启动预热用）"""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT * FROM user_memories
        WHERE user_id IN (
            SELECT user_id FROM user_memories
            GROUP BY user_id
            ORDER BY MAX(updated_at) DESC
            LIMIT $1
        )
        ORDER BY user_id, updated_at DESC
        """,
        limit,
    )
    result: dict[str, list[dict]] = {}
    for r in rows:
        uid = str(r["user_id"])
        if uid not in result:
            result[uid] = []
        result[uid].append(_row_to_fact(r))
    return result


def _row_to_fact(row: asyncpg.Record) -> dict:
    return {
        "id": str(row["id"]),
        "userId": str(row["user_id"]),
        "key": row["key"],
        "value": row["value"],
        "confidence": float(row["confidence"]),
        "source": row["source"] or "",
        "metadata": json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
        "createdAt": row["created_at"].isoformat(),
        "updatedAt": row["updated_at"].isoformat(),
    }


# ── Embedding 向量存储与语义检索 ────────────────────────────

async def upsert_fact_with_embedding(
    user_id: str, key: str, value: str,
    embedding: list[float],
    confidence: float = 1.0, source: str = "",
) -> dict:
    """创建或更新用户事实记忆（含 embedding 向量）"""
    pool = await get_pool()
    now = _now()
    user_uuid = uuid.UUID(user_id)
    metadata = json.dumps({"embedding": embedding}, ensure_ascii=False)

    row = await pool.fetchrow(
        """
        INSERT INTO user_memories (id, user_id, key, value, confidence, source, metadata, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $8)
        ON CONFLICT (user_id, key)
        DO UPDATE SET value = $4, confidence = $5,
                      source = COALESCE(NULLIF($6, ''), user_memories.source),
                      metadata = $7::jsonb, updated_at = $8
        RETURNING *
        """,
        uuid.uuid4(), user_uuid, key, value, confidence, source, metadata, now,
    )
    return _row_to_fact(row)


async def get_all_facts_with_embeddings(user_id: str) -> list[dict]:
    """获取用户所有事实记忆（含 embedding 向量，用于语义检索）"""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT * FROM user_memories WHERE user_id = $1 ORDER BY updated_at DESC",
        uuid.UUID(user_id),
    )
    results = []
    for r in rows:
        fact = _row_to_fact(r)
        meta = fact.get("metadata", {})
        fact["embedding"] = meta.get("embedding") if isinstance(meta, dict) else None
        results.append(fact)
    return results
