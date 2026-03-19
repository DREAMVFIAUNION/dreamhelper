"""工作流引擎 API 路由 — CRUD + 执行 + 状态查询 + 节点列表

持久化: asyncpg 直连 PostgreSQL (与 Prisma schema 完全一致)
"""

import asyncio
import json
import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ...common.admin_auth import require_admin
from ...common.rate_limit import limiter
from .node_registry import NodeRegistry
from .engine import WorkflowEngine
from . import db as wfdb

logger = logging.getLogger("workflow.router")

router = APIRouter(prefix="/workflows", tags=["workflows"])


# ── 请求模型 ──────────────────────────────────────────────

class WorkflowCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    trigger_type: str = Field(default="manual", pattern=r"^(manual|cron|webhook|event)$")
    trigger_config: dict = Field(default_factory=dict)
    nodes: list[dict] = Field(default_factory=list)
    connections: list[dict] = Field(default_factory=list)
    viewport: dict = Field(default_factory=dict)
    variables: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[dict] = None
    nodes: Optional[list[dict]] = None
    connections: Optional[list[dict]] = None
    viewport: Optional[dict] = None
    variables: Optional[dict] = None
    tags: Optional[list[str]] = None


class WorkflowExecuteRequest(BaseModel):
    trigger_data: dict = Field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── 节点类型查询 ──────────────────────────────────────────

@router.get("/node-types")
@limiter.limit("30/minute")
async def list_node_types(request: Request):
    """获取所有可用节点类型（供前端节点面板展示）"""
    return {
        "types": NodeRegistry.list_descriptors(),
        "categories": NodeRegistry.list_by_category(),
    }


# ── 工作流 CRUD (持久化到 PostgreSQL) ─────────────────────

@router.get("")
@limiter.limit("30/minute")
async def list_workflows_api(request: Request, status: Optional[str] = None):
    """列出所有工作流"""
    workflows = await wfdb.list_workflows(status=status)
    return {"data": workflows, "count": len(workflows)}


@router.post("")
@limiter.limit("10/minute")
async def create_workflow_api(request: Request, req: WorkflowCreate, _=Depends(require_admin)):
    """创建工作流"""
    wf = await wfdb.create_workflow(
        owner_id="system",  # TODO: 从 JWT 获取
        name=req.name,
        description=req.description or "",
        trigger_type=req.trigger_type,
        trigger_config=req.trigger_config,
        nodes=req.nodes,
        connections=req.connections,
        viewport=req.viewport,
        variables=req.variables,
        tags=req.tags,
    )
    return wf


@router.get("/{workflow_id}")
@limiter.limit("30/minute")
async def get_workflow_api(request: Request, workflow_id: str):
    """获取工作流详情"""
    wf = await wfdb.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return wf


@router.put("/{workflow_id}")
@limiter.limit("10/minute")
async def update_workflow_api(request: Request, workflow_id: str, req: WorkflowUpdate, _=Depends(require_admin)):
    """更新工作流"""
    existing = await wfdb.get_workflow(workflow_id)
    if not existing:
        raise HTTPException(status_code=404, detail="工作流不存在")

    update_data = req.model_dump(exclude_none=True)
    wf = await wfdb.update_workflow(workflow_id, **update_data)
    return wf


@router.delete("/{workflow_id}")
@limiter.limit("10/minute")
async def delete_workflow_api(request: Request, workflow_id: str, _=Depends(require_admin)):
    """删除工作流 (级联删除关联执行记录 — DB ON DELETE CASCADE)"""
    deleted = await wfdb.delete_workflow(workflow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return {"deleted": True}


# ── 执行工作流 ────────────────────────────────────────────

async def _publish_redis(channel: str, data: dict):
    """推送状态到 Redis PubSub"""
    try:
        import redis.asyncio as aioredis
        from ...common.config import settings
        r = aioredis.from_url(settings.REDIS_URL)
        await r.publish(channel, json.dumps(data, default=str))
        await r.aclose()
    except Exception:
        pass


@router.post("/{workflow_id}/execute")
@limiter.limit("3/minute")
async def execute_workflow_api(request: Request, workflow_id: str, req: WorkflowExecuteRequest, _=Depends(require_admin)):
    """执行工作流"""
    wf = await wfdb.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="工作流不存在")

    if not wf.get("nodes"):
        raise HTTPException(status_code=400, detail="工作流没有节点")

    # 创建执行记录
    execution = await wfdb.create_execution(
        workflow_id=workflow_id,
        trigger_type="manual",
        trigger_data=req.trigger_data,
        total_nodes=len(wf["nodes"]),
    )
    exec_id = execution["id"]

    # Redis PubSub 状态推送 + DB 更新回调
    async def on_status(data: dict):
        if data.get("event") == "execution.finished":
            await wfdb.update_execution(
                exec_id,
                status=data.get("status", "success"),
                completedNodes=data.get("completedNodes", 0),
                totalTokens=data.get("totalTokens", 0),
                totalLatencyMs=data.get("totalLatencyMs", 0),
                error=data.get("error"),
                finishedAt=datetime.now(timezone.utc),
            )
        elif data.get("event") == "execution.started":
            await wfdb.update_execution(exec_id, status="running")

        await _publish_redis(f"workflow:execution:{exec_id}", data)

    # 异步执行（不阻塞响应）
    async def run():
        try:
            engine = WorkflowEngine(on_status=on_status)
            result = await engine.execute(
                execution_id=exec_id,
                nodes=wf["nodes"],
                connections=wf["connections"],
                trigger_data=req.trigger_data,
                variables=wf.get("variables", {}),
                user_id=wf.get("ownerId", "system"),
            )
            # 保存步骤到 DB
            await wfdb.save_steps(exec_id, result.get("steps", []))
            # 更新工作流统计
            await wfdb.update_workflow(
                workflow_id,
                runCount=wf.get("runCount", 0) + 1,
                lastRunAt=datetime.now(timezone.utc),
                lastRunStatus=result["status"],
            )
        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)
            await wfdb.update_execution(
                exec_id, status="failed", error=str(e),
                finishedAt=datetime.now(timezone.utc),
            )

    asyncio.create_task(run())
    return {"executionId": exec_id, "status": "pending"}


# ── 执行记录查询 ──────────────────────────────────────────

@router.get("/{workflow_id}/executions")
@limiter.limit("30/minute")
async def list_executions_api(request: Request, workflow_id: str, limit: int = 20):
    """列出工作流的执行记录"""
    execs = await wfdb.list_executions(workflow_id, limit=limit)
    return {"data": execs, "count": len(execs)}


@router.get("/{workflow_id}/executions/{execution_id}")
@limiter.limit("30/minute")
async def get_execution_api(request: Request, workflow_id: str, execution_id: str):
    """获取单次执行详情（含步骤）"""
    execution = await wfdb.get_execution(execution_id)
    if not execution or execution["workflowId"] != workflow_id:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    steps = await wfdb.get_steps(execution_id)
    return {**execution, "steps": steps}


# ── Webhook 触发器端点 ──────────────────────────────────

@router.api_route("/webhook/{webhook_path:path}", methods=["GET", "POST", "PUT"])
async def webhook_trigger(webhook_path: str, request: Request):
    """外部 Webhook 触发工作流

    匹配逻辑: 寻找 triggerType=webhook 且 triggerConfig.path 匹配的活跃工作流
    """
    # 收集触发数据
    trigger_data: dict = {"path": webhook_path, "method": request.method}
    if request.method in ("POST", "PUT"):
        try:
            trigger_data["body"] = await request.json()
        except Exception:
            trigger_data["body"] = (await request.body()).decode("utf-8", errors="replace")
    trigger_data["query"] = dict(request.query_params)
    trigger_data["headers"] = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}

    # 查 DB 找匹配的活跃 webhook 工作流
    all_active = await wfdb.list_workflows(status="active")
    matched = [
        wf for wf in all_active
        if wf.get("triggerType") == "webhook"
        and wf.get("triggerConfig", {}).get("path", "").strip("/") == webhook_path.strip("/")
    ]

    if not matched:
        raise HTTPException(status_code=404, detail=f"没有匹配路径 '{webhook_path}' 的活跃工作流")

    results = []
    for wf in matched:
        execution = await wfdb.create_execution(
            workflow_id=wf["id"],
            trigger_type="webhook",
            trigger_data=trigger_data,
            total_nodes=len(wf.get("nodes", [])),
        )
        exec_id = execution["id"]

        async def on_status(data: dict, _eid=exec_id):
            if data.get("event") == "execution.finished":
                await wfdb.update_execution(
                    _eid,
                    status=data.get("status", "success"),
                    completedNodes=data.get("completedNodes", 0),
                    totalTokens=data.get("totalTokens", 0),
                    totalLatencyMs=data.get("totalLatencyMs", 0),
                    error=data.get("error"),
                    finishedAt=datetime.now(timezone.utc),
                )
            elif data.get("event") == "execution.started":
                await wfdb.update_execution(_eid, status="running")
            await _publish_redis(f"workflow:execution:{_eid}", data)

        async def run(_wf=wf, _eid=exec_id, _cb=on_status):
            try:
                engine = WorkflowEngine(on_status=_cb)
                result = await engine.execute(
                    execution_id=_eid,
                    nodes=_wf.get("nodes", []),
                    connections=_wf.get("connections", []),
                    trigger_data=trigger_data,
                    variables=_wf.get("variables", {}),
                    user_id=_wf.get("ownerId", "system"),
                )
                await wfdb.save_steps(_eid, result.get("steps", []))
                await wfdb.update_workflow(
                    _wf["id"],
                    runCount=_wf.get("runCount", 0) + 1,
                    lastRunAt=datetime.now(timezone.utc),
                    lastRunStatus=result["status"],
                )
            except Exception as e:
                logger.error(f"Webhook workflow execution error: {e}", exc_info=True)
                await wfdb.update_execution(
                    _eid, status="failed", error=str(e),
                    finishedAt=datetime.now(timezone.utc),
                )

        asyncio.create_task(run())
        results.append({"executionId": exec_id, "workflowId": wf["id"]})

    return {"triggered": len(results), "executions": results}


# ── 预置示例工作流 ──────────────────────────────────────

@router.post("/seed-examples")
@limiter.limit("3/minute")
async def seed_example_workflows(request: Request, _=Depends(require_admin)):
    """创建预置示例工作流（仅当没有工作流时）"""
    existing = await wfdb.list_workflows()
    if existing:
        return {"message": "已有工作流，跳过预置", "count": len(existing)}

    examples = [
        {
            "name": "每日早报 → AI 总结",
            "description": "每天早上 8:00 抓取新闻，用 LLM 生成早报摘要",
            "trigger_type": "cron",
            "trigger_config": {"cron": "08:00"},
            "nodes": [
                {"id": "t1", "type": "trigger_cron", "name": "每日 8:00", "config": {"cron": "08:00"}, "position": {"x": 0, "y": 100}},
                {"id": "n1", "type": "http", "name": "抓取新闻", "config": {"url": "https://newsapi.org/v2/top-headlines?country=cn", "method": "GET"}, "position": {"x": 250, "y": 100}},
                {"id": "n2", "type": "llm", "name": "AI 总结", "config": {"prompt": "请将以下新闻列表总结为一份简洁的中文早报，包含要点和简评：\n\n{{items}}", "model": "default"}, "position": {"x": 500, "y": 100}},
                {"id": "n3", "type": "notification", "name": "推送通知", "config": {"channel": "log", "title": "AI 早报"}, "position": {"x": 750, "y": 100}},
            ],
            "connections": [
                {"id": "e1", "source": "t1", "target": "n1"},
                {"id": "e2", "source": "n1", "target": "n2"},
                {"id": "e3", "source": "n2", "target": "n3"},
            ],
        },
        {
            "name": "Webhook → 智能回复",
            "description": "接收外部 Webhook 请求，用 Agent 智能生成回复",
            "trigger_type": "webhook",
            "trigger_config": {"path": "smart-reply"},
            "nodes": [
                {"id": "t1", "type": "trigger_webhook", "name": "接收请求", "config": {"path": "smart-reply"}, "position": {"x": 0, "y": 100}},
                {"id": "n1", "type": "agent", "name": "智能分析", "config": {"agent_type": "analysis"}, "position": {"x": 250, "y": 100}},
                {"id": "n2", "type": "notification", "name": "返回结果", "config": {"channel": "log"}, "position": {"x": 500, "y": 100}},
            ],
            "connections": [
                {"id": "e1", "source": "t1", "target": "n1"},
                {"id": "e2", "source": "n1", "target": "n2"},
            ],
        },
        {
            "name": "数据处理管道",
            "description": "手动触发 → 条件分支 → 不同处理路径",
            "trigger_type": "manual",
            "trigger_config": {},
            "nodes": [
                {"id": "t1", "type": "trigger_manual", "name": "手动触发", "config": {}, "position": {"x": 0, "y": 150}},
                {"id": "n1", "type": "condition", "name": "数据量判断", "config": {"expression": "len(items) > 10", "field": "items"}, "position": {"x": 250, "y": 150}},
                {"id": "n2", "type": "llm", "name": "AI 摘要", "config": {"prompt": "总结以下数据的关键发现：\n{{items}}"}, "position": {"x": 500, "y": 50}},
                {"id": "n3", "type": "transform", "name": "格式化", "config": {"template": "数据条目: {{items.length}}"}, "position": {"x": 500, "y": 250}},
                {"id": "n4", "type": "notification", "name": "完成通知", "config": {"channel": "log", "title": "处理完成"}, "position": {"x": 750, "y": 150}},
            ],
            "connections": [
                {"id": "e1", "source": "t1", "target": "n1"},
                {"id": "e2", "source": "n1", "target": "n2", "sourceHandle": "true"},
                {"id": "e3", "source": "n1", "target": "n3", "sourceHandle": "false"},
                {"id": "e4", "source": "n2", "target": "n4"},
                {"id": "e5", "source": "n3", "target": "n4"},
            ],
        },
    ]

    created = []
    for ex in examples:
        wf = await wfdb.create_workflow(
            owner_id="system",
            name=ex["name"],
            description=ex["description"],
            trigger_type=ex["trigger_type"],
            trigger_config=ex["trigger_config"],
            nodes=ex["nodes"],
            connections=ex["connections"],
            tags=["example"],
        )
        created.append({"id": wf["id"], "name": ex["name"]})

    return {"message": f"已创建 {len(created)} 个示例工作流", "workflows": created}


# ── 工作流模板 ────────────────────────────────────────────

@router.get("/templates")
@limiter.limit("30/minute")
async def list_templates(request: Request):
    """获取所有可用的工作流模板"""
    from .templates import get_all_templates
    return {"templates": get_all_templates()}


@router.get("/templates/{template_id}")
@limiter.limit("30/minute")
async def get_template(request: Request, template_id: str):
    """获取模板详情（含完整节点和连线定义）"""
    from .templates import get_template_detail
    detail = get_template_detail(template_id)
    if not detail:
        raise HTTPException(404, "模板不存在")
    return detail


@router.post("/templates/{template_id}/create")
@limiter.limit("10/minute")
async def create_from_template(template_id: str, request: Request):
    """从模板一键创建工作流"""
    from .templates import get_template_detail
    detail = get_template_detail(template_id)
    if not detail:
        raise HTTPException(404, "模板不存在")

    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    user_id = body.get("user_id", "system")
    custom_name = body.get("name", detail["name"])

    wf = await wfdb.create_workflow(
        owner_id=user_id,
        name=custom_name,
        description=detail["description"],
        trigger_type=detail["nodes"][0]["type"].replace("trigger_", "") if detail["nodes"] else "manual",
        trigger_config=detail["nodes"][0].get("config", {}) if detail["nodes"] else {},
        nodes=detail["nodes"],
        connections=detail["connections"],
        tags=["template", detail.get("category", "")],
    )

    return {"message": f"从模板「{detail['name']}」创建成功", "workflow": wf}
