"""Instinct 学习系统 API 路由"""

import logging
from fastapi import APIRouter, Depends

from ...common.admin_auth import require_admin

logger = logging.getLogger("learning.router")
router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/instincts")
async def list_instincts(status: str = None, category: str = None, _=Depends(require_admin)):
    """列出所有 Instinct"""
    from .store import InstinctStore
    from .instinct import InstinctStatus
    store = InstinctStore.get_instance()

    if status:
        instincts = store.list_all(InstinctStatus(status))
    elif category:
        instincts = store.list_by_category(category)
    else:
        instincts = store.list_all()

    return {
        "instincts": [i.to_dict() for i in instincts],
        "stats": store.get_stats(),
    }


@router.post("/instincts/extract")
async def extract_from_conversation(request: dict, _=Depends(require_admin)):
    """手动触发从对话提取 Instinct"""
    from .extractor import extract_instincts
    from .store import InstinctStore

    conversation = request.get("conversation", [])
    session_id = request.get("session_id", "")

    instincts = await extract_instincts(conversation, session_id)
    store = InstinctStore.get_instance()
    for inst in instincts:
        store.add(inst)

    return {
        "extracted": len(instincts),
        "instincts": [i.to_dict() for i in instincts],
    }


@router.post("/instincts/prune")
async def prune_instincts(max_age_days: int = 30, _=Depends(require_admin)):
    """清理过期 Instinct"""
    from .store import InstinctStore
    store = InstinctStore.get_instance()
    pruned = store.prune_expired(max_age_days)
    return {"pruned": pruned, "stats": store.get_stats()}


@router.get("/instincts/stats")
async def instinct_stats():
    """Instinct 统计信息（无需管理员）"""
    from .store import InstinctStore
    store = InstinctStore.get_instance()
    return store.get_stats()
