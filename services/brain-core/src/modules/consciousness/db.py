"""意识核数据库 — 持久化自我认知、情感历史、目标、想法

复用现有 PostgreSQL 连接池 (memory.db)
当 PostgreSQL 不可用时, 自动降级到 SQLite 本地存储
"""

import json
import time
import logging
import sqlite3
import os
from typing import Optional

logger = logging.getLogger("consciousness.db")

_use_sqlite = False
_sqlite_conn: Optional[sqlite3.Connection] = None


def _get_sqlite_path() -> str:
    """P3-#12: SQLite 降级路径可配置"""
    custom = os.environ.get("CONSCIOUSNESS_SQLITE_PATH")
    if custom:
        return custom
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "..", "..", "consciousness_fallback.db")


def _get_sqlite() -> sqlite3.Connection:
    global _sqlite_conn
    if _sqlite_conn is None:
        path = _get_sqlite_path()
        _sqlite_conn = sqlite3.connect(path)
        _sqlite_conn.row_factory = sqlite3.Row
        logger.info("[ConsciousnessDB] SQLite fallback: %s", path)
    return _sqlite_conn


async def _get_pool():
    global _use_sqlite
    if _use_sqlite:
        return None
    try:
        from ..memory.db import get_pool
        from ...common.config import settings
        return await get_pool()
    except Exception as e:
        logger.warning("[ConsciousnessDB] PostgreSQL unavailable, switching to SQLite: %s", e)
        _use_sqlite = True
        return None


async def ensure_tables():
    """创建意识核所需的 3 张表"""
    pool = await _get_pool()
    if _use_sqlite:
        conn = _get_sqlite()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consciousness_self (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT '{}',
                updated_at REAL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consciousness_thoughts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                topic TEXT DEFAULT '',
                importance REAL DEFAULT 0.5,
                should_express INTEGER DEFAULT 0,
                expression TEXT DEFAULT '',
                related_user_id TEXT DEFAULT '',
                emotion_impact TEXT DEFAULT '{}',
                created_at REAL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consciousness_goals (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                goal_type TEXT DEFAULT 'long_term',
                priority REAL DEFAULT 0.5,
                status TEXT DEFAULT 'active',
                progress REAL DEFAULT 0.0,
                related_user_id TEXT DEFAULT '',
                sub_goals TEXT DEFAULT '[]',
                created_at REAL DEFAULT 0,
                updated_at REAL DEFAULT 0
            )
        """)
        conn.commit()
        logger.info("[ConsciousnessDB] SQLite tables ensured")
        return
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS consciousness_self (
                key TEXT PRIMARY KEY,
                value JSONB NOT NULL DEFAULT '{}',
                updated_at DOUBLE PRECISION DEFAULT 0
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS consciousness_thoughts (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                topic TEXT DEFAULT '',
                importance DOUBLE PRECISION DEFAULT 0.5,
                should_express BOOLEAN DEFAULT FALSE,
                expression TEXT DEFAULT '',
                related_user_id TEXT DEFAULT '',
                emotion_impact JSONB DEFAULT '{}',
                created_at DOUBLE PRECISION DEFAULT 0
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS consciousness_goals (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                goal_type TEXT DEFAULT 'long_term',
                priority DOUBLE PRECISION DEFAULT 0.5,
                status TEXT DEFAULT 'active',
                progress DOUBLE PRECISION DEFAULT 0.0,
                related_user_id TEXT DEFAULT '',
                sub_goals JSONB DEFAULT '[]',
                created_at DOUBLE PRECISION DEFAULT 0,
                updated_at DOUBLE PRECISION DEFAULT 0
            );
        """)
    logger.info("[ConsciousnessDB] PostgreSQL tables ensured")


# ── Self Model 持久化 ──────────────────────────────

async def save_self(key: str, value: dict):
    if _use_sqlite:
        conn = _get_sqlite()
        conn.execute(
            "INSERT OR REPLACE INTO consciousness_self (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value, ensure_ascii=False), time.time()),
        )
        conn.commit()
        return
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO consciousness_self (key, value, updated_at)
               VALUES ($1, $2::jsonb, $3)
               ON CONFLICT (key) DO UPDATE SET value = $2::jsonb, updated_at = $3""",
            key, json.dumps(value, ensure_ascii=False), time.time(),
        )


async def load_self(key: str) -> Optional[dict]:
    if _use_sqlite:
        conn = _get_sqlite()
        cur = conn.execute("SELECT value FROM consciousness_self WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            return json.loads(row["value"])
        return None
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT value FROM consciousness_self WHERE key = $1", key
        )
        if row:
            return json.loads(row["value"])
    return None


async def load_all_self() -> dict[str, dict]:
    if _use_sqlite:
        conn = _get_sqlite()
        cur = conn.execute("SELECT key, value FROM consciousness_self")
        return {r["key"]: json.loads(r["value"]) for r in cur.fetchall()}
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT key, value FROM consciousness_self")
        return {r["key"]: json.loads(r["value"]) for r in rows}


# ── Thoughts 持久化 ──────────────────────────────

async def save_thought(thought: dict) -> int:
    if _use_sqlite:
        conn = _get_sqlite()
        cur = conn.execute(
            """INSERT INTO consciousness_thoughts
               (content, topic, importance, should_express, expression,
                related_user_id, emotion_impact, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                thought.get("content", ""),
                thought.get("topic", ""),
                thought.get("importance", 0.5),
                1 if thought.get("should_express", False) else 0,
                thought.get("expression", ""),
                thought.get("related_user_id", ""),
                json.dumps(thought.get("emotion_impact", {}), ensure_ascii=False),
                thought.get("created_at", time.time()),
            ),
        )
        conn.commit()
        return cur.lastrowid or 0
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO consciousness_thoughts
               (content, topic, importance, should_express, expression,
                related_user_id, emotion_impact, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
               RETURNING id""",
            thought.get("content", ""),
            thought.get("topic", ""),
            thought.get("importance", 0.5),
            thought.get("should_express", False),
            thought.get("expression", ""),
            thought.get("related_user_id", ""),
            json.dumps(thought.get("emotion_impact", {}), ensure_ascii=False),
            thought.get("created_at", time.time()),
        )
        return row["id"]


async def get_recent_thoughts(limit: int = 20) -> list[dict]:
    if _use_sqlite:
        conn = _get_sqlite()
        cur = conn.execute(
            "SELECT * FROM consciousness_thoughts ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM consciousness_thoughts ORDER BY created_at DESC LIMIT $1",
            limit,
        )
        return [dict(r) for r in rows]


# ── Goals 持久化 ──────────────────────────────

async def save_goal(goal: dict):
    if _use_sqlite:
        conn = _get_sqlite()
        conn.execute(
            """INSERT OR REPLACE INTO consciousness_goals
               (id, title, description, goal_type, priority, status, progress,
                related_user_id, sub_goals, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                goal["id"], goal["title"], goal.get("description", ""),
                goal.get("goal_type", "long_term"), goal.get("priority", 0.5),
                goal.get("status", "active"), goal.get("progress", 0.0),
                goal.get("related_user_id", ""),
                json.dumps(goal.get("sub_goals", []), ensure_ascii=False),
                goal.get("created_at", time.time()), time.time(),
            ),
        )
        conn.commit()
        return
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO consciousness_goals
               (id, title, description, goal_type, priority, status, progress,
                related_user_id, sub_goals, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11)
               ON CONFLICT (id) DO UPDATE SET
                 title=$2, description=$3, priority=$5, status=$6, progress=$7,
                 sub_goals=$9::jsonb, updated_at=$11""",
            goal["id"], goal["title"], goal.get("description", ""),
            goal.get("goal_type", "long_term"), goal.get("priority", 0.5),
            goal.get("status", "active"), goal.get("progress", 0.0),
            goal.get("related_user_id", ""),
            json.dumps(goal.get("sub_goals", []), ensure_ascii=False),
            goal.get("created_at", time.time()), time.time(),
        )


async def load_goals(status: str = "active") -> list[dict]:
    if _use_sqlite:
        conn = _get_sqlite()
        cur = conn.execute(
            "SELECT * FROM consciousness_goals WHERE status = ? ORDER BY priority DESC",
            (status,),
        )
        return [dict(r) for r in cur.fetchall()]
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM consciousness_goals WHERE status = $1 ORDER BY priority DESC",
            status,
        )
        return [dict(r) for r in rows]
