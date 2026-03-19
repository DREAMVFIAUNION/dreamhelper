"""意识核 API 路由"""

import hashlib
import logging
from fastapi import APIRouter, Depends, Request

from ...common.admin_auth import require_admin
from ...common.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consciousness", tags=["consciousness"])


@router.get("/status")
async def consciousness_status(_=Depends(require_admin)):
    """意识核完整状态（需管理员权限）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    return core.get_stats()


@router.get("/emotion")
async def consciousness_emotion(_=Depends(require_admin)):
    """情感状态详情（需管理员权限）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    return {
        "mood": core.emotion_state.get_mood_label(),
        "tone": core.emotion_state.get_tone_modifier(),
        **core.emotion_state.to_dict(),
    }


@router.get("/thoughts")
async def consciousness_thoughts(limit: int = 10, _=Depends(require_admin)):
    """近期想法（需管理员权限）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    return {
        "thoughts": core.inner_voice.get_recent_thoughts(limit),
        "stats": core.inner_voice.get_stats(),
    }


@router.get("/goals")
async def consciousness_goals(_=Depends(require_admin)):
    """当前目标（需管理员权限）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    goals = [
        {
            "id": g.id, "title": g.title, "description": g.description,
            "goal_type": g.goal_type,
            "priority": g.priority, "progress": g.progress, "status": g.status,
        }
        for g in core.goal_system.goals.values()
    ]
    return {"goals": goals, "stats": core.goal_system.get_stats()}


@router.get("/opinions")
async def consciousness_opinions(_=Depends(require_admin)):
    """观点库（需管理员权限）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    opinions = [
        {
            "topic": op.topic, "stance": op.stance,
            "confidence": op.confidence,
            "updated_at": op.updated_at,
        }
        for op in sorted(
            core.self_model.opinions.values(),
            key=lambda o: o.confidence, reverse=True,
        )
    ]
    return {"opinions": opinions, "count": len(opinions)}


@router.get("/world")
async def consciousness_world(_=Depends(require_admin)):
    """世界感知状态（需管理员权限）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    ws = core.world_model.world_state
    return {
        "current_time": ws.current_time,
        "weather": ws.weather_summary,
        "tech_headlines": ws.tech_headlines,
        "ai_headlines": ws.ai_headlines,
        "market_summary": ws.market_summary,
        "crypto_summary": ws.crypto_summary,
        "last_observed": ws.last_observed,
        "stats": core.world_model.get_stats(),
    }


@router.post("/express")
@limiter.limit("2/hour")
async def consciousness_express(request: Request, _=Depends(require_admin)):
    """P1-#5: 手动触发内心独白（需管理员权限）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    if not core._started:
        return {"error": "意识核未启动"}
    await core.inner_voice.think()
    return {
        "message": "内心独白完成",
        "thoughts": core.inner_voice.get_recent_thoughts(5),
        "mood": core.emotion_state.get_mood_label(),
    }


@router.post("/observe")
@limiter.limit("3/hour")
async def consciousness_observe(request: Request, _=Depends(require_admin)):
    """P1-#5: 手动触发世界观察（需管理员权限）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    if not core._started:
        return {"error": "意识核未启动"}
    await core.world_model.observe()
    return {
        "message": "世界观察完成",
        "stats": core.world_model.get_stats(),
    }


@router.get("/health")
async def consciousness_health():
    """意识核健康检查 — 一键诊断所有子系统"""
    from .core import get_consciousness_core
    from ..proactive.scheduler import get_scheduler

    core = get_consciousness_core()
    scheduler = get_scheduler()

    # 检查 scheduler 中意识核任务状态
    task_status = {}
    for t in scheduler.list_tasks():
        if t["task_id"].startswith("consciousness_"):
            task_status[t["task_id"]] = {
                "enabled": t["enabled"],
                "run_count": t["run_count"],
                "last_run": t["last_run"],
            }

    return {
        "healthy": core.config.enabled and core._started,
        "config": {
            "enabled": core.config.enabled,
            "consciousness_model": core.config.consciousness_model or "(LLM default)",
            "inner_voice_interval": core.config.inner_voice_interval,
            "world_weather_city": core.config.world_weather_city,
        },
        "started": core._started,
        "scheduler_tasks": task_status,
        "stats": core.get_stats(),
    }


@router.get("/users")
async def consciousness_users(_=Depends(require_admin)):
    """P1-#5: 意识核已知用户列表（需管理员权限，user_id 已脱敏）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    registry = core.user_registry
    users = registry.get_all_users()

    def _mask_uid(uid: str) -> str:
        """脱敏 user_id: 保留前4字符 + hash后4位"""
        if len(uid) <= 4:
            return uid
        h = hashlib.md5(uid.encode()).hexdigest()[-4:]
        return f"{uid[:4]}***{h}"

    return {
        "known_users": [
            {
                "user_id": _mask_uid(u.user_id),
                "display_name": u.display_name,
                "idle_label": u.idle_label,
                "interaction_count": u.interaction_count,
                "mood_estimate": u.mood_estimate,
            }
            for u in sorted(users, key=lambda x: x.last_active, reverse=True)
        ],
        "stats": registry.get_stats(),
    }


@router.get("/evolution")
async def consciousness_evolution(_=Depends(require_admin)):
    """进化追踪状态（需管理员权限）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    stats = core.evolution.get_stats()
    stats["narrative"] = core.evolution.get_evolution_narrative()
    return stats


@router.post("/test-think")
@limiter.limit("10/minute")
async def consciousness_test_think(request: Request, _=Depends(require_admin)):
    """P1-#5: 快速 LLM 调用测试（需管理员权限）"""
    from .core import get_consciousness_core
    core = get_consciousness_core()
    if not core._started:
        return {"error": "意识核未启动", "suggestion": "检查 CONSCIOUSNESS_ENABLED 是否为 true"}

    import time
    model = core.config.consciousness_model or None
    try:
        from ..llm.llm_client import get_llm_client
        from ..llm.types import LLMRequest
        client = get_llm_client()
        request = LLMRequest(
            messages=[{"role": "user", "content": "用一句话描述你现在的心情。只输出一句话。"}],
            **({"model": model} if model else {}),
            temperature=0.7,
            max_tokens=100,
            stream=False,
        )
        t0 = time.time()
        response = await client.complete(request)
        latency = round((time.time() - t0) * 1000)
        return {
            "success": True,
            "model_requested": model or "(default)",
            "model_used": response.model,
            "provider": response.provider,
            "content": response.content.strip(),
            "latency_ms": latency,
        }
    except Exception as e:
        import logging
        logging.getLogger("consciousness.router").error("test-think failed: %s", e, exc_info=True)
        return {
            "success": False,
            "model_requested": model or "(default)",
            "error": "LLM 调用失败，请检查日志",
        }
