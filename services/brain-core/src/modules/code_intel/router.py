"""代码智能 API 路由 — GitNexus 知识图谱接口

提供 5 个端点:
- GET  /code-intel/repos     — 列出已索引仓库
- POST /code-intel/query     — 语义搜索执行流
- GET  /code-intel/context/{name} — 符号 360° 视图
- POST /code-intel/impact    — 影响分析（爆炸半径）
- POST /code-intel/changes   — 变更检测
- GET  /code-intel/status    — 模块状态
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional

from ...common.rate_limit import limiter
from .gitnexus_client import get_gitnexus_client

router = APIRouter(prefix="/code-intel", tags=["code-intel"])


# ── Request Models ────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(description="语义搜索查询")
    goal: str = Field(default="", description="搜索目标描述")
    repo: str = Field(default="", description="仓库名（空=默认）")
    limit: int = Field(default=5, ge=1, le=20)
    include_content: bool = Field(default=False, description="是否包含源码")


class ImpactRequest(BaseModel):
    target: str = Field(description="目标符号名（函数/类/文件）")
    direction: str = Field(default="upstream", description="upstream(谁依赖我) 或 downstream(我依赖谁)")
    max_depth: int = Field(default=3, ge=1, le=5)
    repo: str = Field(default="")
    include_tests: bool = Field(default=False)


class ChangesRequest(BaseModel):
    scope: str = Field(default="all", description="unstaged/staged/all/compare")
    repo: str = Field(default="")
    base_ref: str = Field(default="", description="compare 模式的基准分支")


# ── Endpoints ─────────────────────────────────────

@router.get("/status")
@limiter.limit("30/minute")
async def code_intel_status(request: Request):
    """代码智能模块状态"""
    client = get_gitnexus_client()
    return await client.get_status()


@router.get("/repos")
@limiter.limit("30/minute")
async def list_repos(request: Request):
    """列出已索引仓库"""
    client = get_gitnexus_client()
    if not client.available:
        raise HTTPException(status_code=503, detail="GitNexus MCP 未连接")
    return await client.list_repos()


@router.post("/query")
@limiter.limit("10/minute")
async def query_code(request: Request, req: QueryRequest):
    """语义搜索代码执行流"""
    client = get_gitnexus_client()
    if not client.available:
        raise HTTPException(status_code=503, detail="GitNexus MCP 未连接")
    return await client.query(
        query=req.query,
        goal=req.goal,
        repo=req.repo,
        limit=req.limit,
        include_content=req.include_content,
    )


@router.get("/context/{name}")
@limiter.limit("10/minute")
async def get_symbol_context(request: Request, name: str, repo: str = "", include_content: bool = False):
    """获取符号 360° 上下文视图"""
    client = get_gitnexus_client()
    if not client.available:
        raise HTTPException(status_code=503, detail="GitNexus MCP 未连接")
    return await client.context(name=name, repo=repo, include_content=include_content)


@router.post("/impact")
@limiter.limit("10/minute")
async def analyze_impact(request: Request, req: ImpactRequest):
    """分析代码变更影响范围（爆炸半径）"""
    client = get_gitnexus_client()
    if not client.available:
        raise HTTPException(status_code=503, detail="GitNexus MCP 未连接")
    return await client.impact(
        target=req.target,
        direction=req.direction,
        max_depth=req.max_depth,
        repo=req.repo,
        include_tests=req.include_tests,
    )


@router.post("/changes")
@limiter.limit("10/minute")
async def detect_changes(request: Request, req: ChangesRequest):
    """检测未提交的代码变更及其影响"""
    client = get_gitnexus_client()
    if not client.available:
        raise HTTPException(status_code=503, detail="GitNexus MCP 未连接")
    return await client.detect_changes(
        scope=req.scope,
        repo=req.repo,
        base_ref=req.base_ref,
    )
