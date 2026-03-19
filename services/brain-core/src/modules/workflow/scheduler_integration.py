"""工作流 Cron 触发器 — 与现有 Scheduler 集成

当工作流 status=active 且 triggerType=cron 时，自动注册到 Scheduler。
"""

import uuid
import json
import asyncio
from typing import Optional

from ..proactive.scheduler import get_scheduler, ScheduledTask, TaskType
from .engine import WorkflowEngine
from .router import _workflows, _executions, _steps, _now_iso


def _parse_cron_to_hhmm(cron_expr: str) -> Optional[str]:
    """将简单 cron 表达式转为 HH:MM 格式（简化版：仅支持每日定时）

    支持格式:
    - "HH:MM" → 直接使用
    - "M H * * *" → 标准 cron 前两位
    """
    cron_expr = cron_expr.strip()
    if ":" in cron_expr and len(cron_expr) <= 5:
        return cron_expr

    parts = cron_expr.split()
    if len(parts) >= 2:
        try:
            minute = int(parts[0])
            hour = int(parts[1])
            return f"{hour:02d}:{minute:02d}"
        except ValueError:
            pass
    return None


async def _execute_workflow_by_id(workflow_id: str):
    """Cron 回调: 执行指定工作流"""
    wf = _workflows.get(workflow_id)
    if not wf or wf.get("status") != "active":
        return

    exec_id = str(uuid.uuid4())
    now = _now_iso()

    execution = {
        "id": exec_id,
        "workflowId": workflow_id,
        "status": "pending",
        "triggerType": "cron",
        "triggerData": {"cron": wf.get("triggerConfig", {}).get("cron", "")},
        "error": None,
        "totalNodes": len(wf.get("nodes", [])),
        "completedNodes": 0,
        "totalTokens": 0,
        "totalLatencyMs": 0,
        "startedAt": now,
        "finishedAt": None,
    }
    _executions[exec_id] = execution

    async def on_status(data: dict):
        if data.get("event") == "execution.finished":
            execution["status"] = data.get("status", "success")
            execution["completedNodes"] = data.get("completedNodes", 0)
            execution["totalTokens"] = data.get("totalTokens", 0)
            execution["totalLatencyMs"] = data.get("totalLatencyMs", 0)
            execution["error"] = data.get("error")
            execution["finishedAt"] = _now_iso()
        elif data.get("event") == "execution.started":
            execution["status"] = "running"

        try:
            import redis.asyncio as aioredis
            from ...common.config import settings
            r = aioredis.from_url(settings.REDIS_URL)
            await r.publish(f"workflow:execution:{exec_id}", json.dumps(data, default=str))
            await r.aclose()
        except Exception:
            pass

    engine = WorkflowEngine(on_status=on_status)
    result = await engine.execute(
        execution_id=exec_id,
        nodes=wf.get("nodes", []),
        connections=wf.get("connections", []),
        trigger_data=execution["triggerData"],
        variables=wf.get("variables", {}),
        user_id=wf.get("ownerId", "system"),
    )
    _steps[exec_id] = result.get("steps", [])
    wf["runCount"] = wf.get("runCount", 0) + 1
    wf["lastRunAt"] = _now_iso()
    wf["lastRunStatus"] = result["status"]


def register_workflow_cron(workflow_id: str, cron_expr: str):
    """为工作流注册 Cron 任务"""
    hhmm = _parse_cron_to_hhmm(cron_expr)
    if not hhmm:
        print(f"  ⚠ Invalid cron for workflow {workflow_id}: {cron_expr}")
        return

    task_id = f"workflow_cron_{workflow_id}"
    scheduler = get_scheduler()

    # 先清除旧的
    scheduler.unregister(task_id)

    task = ScheduledTask(
        task_id=task_id,
        name=f"Workflow Cron: {workflow_id[:8]}",
        task_type=TaskType.CRON,
        cron_expr=hhmm,
        callback=lambda wid=workflow_id: _execute_workflow_by_id(wid),
        description=f"Cron trigger for workflow {workflow_id}",
    )
    scheduler.register(task)
    # 如果调度器已启动，立即启动此任务
    if scheduler._running:
        task._handle = asyncio.create_task(scheduler._run_task(task))


def unregister_workflow_cron(workflow_id: str):
    """取消工作流的 Cron 任务"""
    task_id = f"workflow_cron_{workflow_id}"
    get_scheduler().unregister(task_id)
