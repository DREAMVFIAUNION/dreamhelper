"""主动唤醒 API 路由（Phase 4）"""

import json
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

from ...common.rate_limit import limiter
from .scheduler import get_scheduler
from .heartbeat import get_heartbeat
from .rule_engine import get_proactive_engine, TriggerType, generate_proactive_message

router = APIRouter(prefix="/proactive", tags=["proactive"])


class HeartbeatRequest(BaseModel):
    user_id: str
    action: str = "active"  # "active" | "online" | "offline"


class TriggerRequest(BaseModel):
    user_id: str
    trigger: str = "idle_greeting"  # idle_greeting | morning_brief | evening_summary | welcome_back


@router.post("/heartbeat")
@limiter.limit("60/minute")
async def heartbeat(request: Request, req: HeartbeatRequest):
    """用户心跳上报"""
    hb = get_heartbeat()
    if req.action == "online":
        hb.user_online(req.user_id)
    elif req.action == "offline":
        hb.user_offline(req.user_id)
    else:
        hb.user_active(req.user_id)
    return {"status": "ok", "user_id": req.user_id, "action": req.action}


@router.post("/trigger")
@limiter.limit("5/minute")
async def trigger_message(request: Request, req: TriggerRequest):
    """手动触发主动消息（测试用）"""
    try:
        trigger = TriggerType(req.trigger)
    except ValueError:
        return {"error": f"Unknown trigger: {req.trigger}"}

    msg = await generate_proactive_message(trigger, req.user_id)
    if msg:
        engine = get_proactive_engine()
        await engine._push(msg)
        return {
            "status": "ok",
            "message": {
                "trigger": msg.trigger.value,
                "title": msg.title,
                "content": msg.content,
                "user_id": msg.user_id,
            },
        }
    return {"status": "error", "message": "Failed to generate message"}


@router.get("/messages/{user_id}")
@limiter.limit("30/minute")
async def get_pending_messages(request: Request, user_id: str):
    """获取用户待推送消息（轮询 fallback）"""
    engine = get_proactive_engine()
    msgs = engine.get_pending_messages(user_id)
    return {
        "user_id": user_id,
        "messages": [
            {
                "trigger": m.trigger.value,
                "title": m.title,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in msgs
        ],
    }


@router.get("/stats")
@limiter.limit("30/minute")
async def proactive_stats(request: Request):
    """主动唤醒系统状态"""
    engine = get_proactive_engine()
    scheduler = get_scheduler()
    return {
        "engine": engine.get_stats(),
        "tasks": scheduler.list_tasks(),
    }


@router.get("/tasks")
@limiter.limit("30/minute")
async def list_tasks(request: Request):
    """列出所有定时任务"""
    scheduler = get_scheduler()
    return {"tasks": scheduler.list_tasks()}
