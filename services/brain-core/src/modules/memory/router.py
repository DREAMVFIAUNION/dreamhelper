"""记忆系统 API 路由 — 用户事实记忆 CRUD + 统计"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from ...common.rate_limit import limiter
from .memory_manager import get_memory_manager

router = APIRouter(prefix="/memory", tags=["memory"])


class SetFactRequest(BaseModel):
    key: str
    value: str
    confidence: float = 1.0
    source: str = ""


@router.get("/{user_id}")
@limiter.limit("30/minute")
async def get_user_memories(request: Request, user_id: str):
    """获取用户所有长期事实记忆"""
    mm = get_memory_manager()
    facts = await mm.get_all_user_facts(user_id)
    return {"userId": user_id, "facts": facts, "count": len(facts)}


@router.post("/{user_id}")
@limiter.limit("10/minute")
async def set_user_fact(request: Request, user_id: str, req: SetFactRequest):
    """设置/更新用户事实"""
    mm = get_memory_manager()
    await mm.set_user_fact(
        user_id=user_id,
        key=req.key,
        value=req.value,
        confidence=req.confidence,
        source=req.source,
    )
    return {"ok": True, "userId": user_id, "key": req.key}


@router.delete("/{user_id}")
@limiter.limit("10/minute")
async def delete_all_user_memories(request: Request, user_id: str):
    """删除用户所有事实记忆"""
    mm = get_memory_manager()
    count = await mm.delete_all_user_facts(user_id)
    return {"ok": True, "userId": user_id, "deleted": count}


@router.delete("/{user_id}/{key}")
@limiter.limit("10/minute")
async def delete_user_fact(request: Request, user_id: str, key: str):
    """删除用户单个事实"""
    mm = get_memory_manager()
    await mm.delete_user_fact(user_id, key)
    return {"ok": True, "userId": user_id, "key": key}


@router.get("/{user_id}/profile")
@limiter.limit("30/minute")
async def get_user_profile_prompt(request: Request, user_id: str):
    """获取用户画像 prompt 片段"""
    mm = get_memory_manager()
    prompt = await mm.get_user_profile_prompt(user_id)
    return {"userId": user_id, "profilePrompt": prompt}


@router.get("/{user_id}/search")
@limiter.limit("10/minute")
async def semantic_search_memories(request: Request, user_id: str, q: str = "", top_k: int = 5):
    """语义检索用户记忆 — 根据查询内容匹配最相关的记忆"""
    if not q:
        raise HTTPException(status_code=400, detail="Missing query parameter 'q'")
    mm = get_memory_manager()
    results = await mm.semantic_search(user_id, q, top_k=top_k)
    return {"userId": user_id, "query": q, "results": results, "count": len(results)}


@router.get("")
@limiter.limit("30/minute")
async def memory_stats(request: Request):
    """记忆系统统计"""
    mm = get_memory_manager()
    stats = await mm.get_stats()
    return {"status": "ok", "module": "memory", **stats}
