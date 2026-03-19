"""Skills API 路由 — 技能列表/搜索/执行"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

from ....common.rate_limit import limiter
from .skill_engine import SkillEngine

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillExecuteRequest(BaseModel):
    name: str
    params: dict = {}


@router.get("/list")
@limiter.limit("30/minute")
async def list_skills(request: Request):
    """获取所有技能列表"""
    return {"skills": SkillEngine.list_skills(), "total": len(SkillEngine._skills)}


@router.get("/categories")
@limiter.limit("30/minute")
async def list_categories(request: Request):
    """获取技能分类统计"""
    return {"categories": SkillEngine.categories()}


@router.get("/search")
@limiter.limit("30/minute")
async def search_skills(request: Request, q: str = ""):
    """搜索技能"""
    if not q:
        return {"skills": SkillEngine.list_skills(), "query": ""}
    results = SkillEngine.search(q)
    return {"skills": results, "query": q, "total": len(results)}


@router.get("/category/{category}")
@limiter.limit("30/minute")
async def list_by_category(request: Request, category: str):
    """按分类获取技能"""
    skills = SkillEngine.list_by_category(category)
    return {"skills": skills, "category": category, "total": len(skills)}


@router.get("/{name}/schema")
@limiter.limit("30/minute")
async def get_skill_schema(request: Request, name: str):
    """获取技能参数 Schema"""
    skill = SkillEngine.get(name)
    if not skill:
        return {"error": f"技能 '{name}' 不存在"}
    return skill.to_schema()


@router.post("/execute")
@limiter.limit("5/minute")
async def execute_skill(request: Request, req: SkillExecuteRequest):
    """执行技能"""
    result = await SkillEngine.execute(req.name, **req.params)
    return result
