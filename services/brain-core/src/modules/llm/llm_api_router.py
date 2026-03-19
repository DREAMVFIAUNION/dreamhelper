"""LLM 网关 API 路由 — 统计 + 模型列表 + 健康状态（Phase 11）"""

from fastapi import APIRouter, Request

from ...common.rate_limit import limiter

router = APIRouter(prefix="/llm", tags=["llm-gateway"])


@router.get("/gateway/stats")
@limiter.limit("30/minute")
async def gateway_stats(request: Request):
    """LLM 网关统计: 请求数、缓存命中、熔断状态、路由延迟"""
    from .gateway import get_llm_gateway
    gw = get_llm_gateway()
    return gw.get_stats()


@router.get("/models")
@limiter.limit("30/minute")
async def list_models(request: Request):
    """列出所有可用 LLM 模型"""
    from .llm_client import get_llm_client
    client = get_llm_client()
    return {"models": client.list_models()}


@router.get("/providers")
@limiter.limit("30/minute")
async def list_providers(request: Request):
    """列出已注册的 LLM 提供商"""
    from .llm_client import get_llm_client
    client = get_llm_client()
    return {
        "providers": [
            {"name": p.name, "models_count": len(p.supported_models) if hasattr(p, 'supported_models') else "N/A"}
            for p in client.providers
        ]
    }
