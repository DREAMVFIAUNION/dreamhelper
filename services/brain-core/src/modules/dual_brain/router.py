"""双脑融合 API 路由"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional

from . import get_brain_engine, reset_brain_engine
from .brain_config import BrainConfig
from .cortex import FusionStrategy
from ...common.admin_auth import require_admin
from ...common.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain", tags=["dual-brain"])


class BrainThinkRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=32000)
    system_prompt: str = ""
    history: list[dict] = Field(default_factory=list)
    strategy: Optional[str] = None
    mode: str = Field("dual", description="dual | single")


@router.post("/think")
@limiter.limit("5/minute")
async def dual_brain_think(request: Request, req: BrainThinkRequest):
    """双脑思考接口"""
    brain = get_brain_engine()

    if req.mode == "single" or not brain.config.enabled:
        content = await brain.think_single(
            query=req.query,
            system_prompt=req.system_prompt,
            history=req.history,
        )
        return {
            "content": content,
            "mode": "single",
            "brain_mode": False,
        }

    strategy = FusionStrategy(req.strategy) if req.strategy else None
    result = await brain.think(
        query=req.query,
        context={},
        system_prompt=req.system_prompt,
        history=req.history,
        strategy=strategy,
    )

    return {
        "content": result.content,
        "mode": "dual",
        "brain_mode": True,
        "task_type": result.task_type,
        "fusion_strategy": result.fusion_strategy,
        "confidence": result.confidence,
        "left_latency_ms": result.left_latency_ms,
        "right_latency_ms": result.right_latency_ms,
        "total_latency_ms": result.total_latency_ms,
        "left_weight": result.left_weight,
        "right_weight": result.right_weight,
        "metadata": result.metadata,
    }


@router.get("/stats")
async def brain_stats():
    """双脑运行统计"""
    brain = get_brain_engine()
    return brain.get_stats()


class BrainConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    left_model: Optional[str] = None
    right_model: Optional[str] = None
    judge_model: Optional[str] = None
    fusion_model: Optional[str] = None
    simple_query_threshold: Optional[int] = None
    min_confidence: Optional[float] = None


@router.post("/config")
async def update_brain_config(request: Request, update: BrainConfigUpdate, _=Depends(require_admin)):
    """P0-#4: 动态更新双脑配置（需管理员权限）"""
    brain = get_brain_engine()
    cfg = brain.config

    # P0-#4: 模型名白名单校验
    from ..llm.llm_client import get_llm_client
    allowed_models = {m["id"] for m in get_llm_client().list_models()}
    for field_name in ("left_model", "right_model", "judge_model", "fusion_model"):
        val = getattr(update, field_name, None)
        if val is not None and val not in allowed_models:
            raise HTTPException(422, f"不支持的模型: {val}")

    if update.enabled is not None:
        cfg.enabled = update.enabled
    if update.left_model is not None:
        cfg.left_model = update.left_model
    if update.right_model is not None:
        cfg.right_model = update.right_model
    if update.judge_model is not None:
        cfg.judge_model = update.judge_model
    if update.fusion_model is not None:
        cfg.fusion_model = update.fusion_model

    logger.info("Brain config updated by admin: %s", update.model_dump(exclude_none=True))
    if update.simple_query_threshold is not None:
        cfg.simple_query_threshold = update.simple_query_threshold
    if update.min_confidence is not None:
        cfg.min_confidence = update.min_confidence

    # 如果模型变了，需要重建半球
    reset_brain_engine(cfg)

    return {"status": "ok", "config": {
        "enabled": cfg.enabled,
        "left_model": cfg.left_model,
        "right_model": cfg.right_model,
        "judge_model": cfg.judge_model,
        "fusion_model": cfg.fusion_model,
        "simple_query_threshold": cfg.simple_query_threshold,
        "min_confidence": cfg.min_confidence,
    }}


@router.get("/hemispheres")
async def list_hemispheres():
    """查看双脑半球状态"""
    brain = get_brain_engine()
    return {
        "enabled": brain.config.enabled,
        "left": {
            "name": brain.left.name,
            "model": brain.left.model,
            "temperature": brain.left._get_temperature(),
            "max_tokens": brain.left._get_max_tokens(),
        },
        "right": {
            "name": brain.right.name,
            "model": brain.right.model,
            "temperature": brain.right._get_temperature(),
            "max_tokens": brain.right._get_max_tokens(),
        },
    }
