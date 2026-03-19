"""工作流执行引擎 — DAG 解析 + 拓扑排序 + 按序/并行执行

架构定位: 这是系统的"肌肉"——执行层，由双脑（大脑）调度。
原生 Python asyncio 实现，DAG 拓扑排序执行。
"""

import asyncio
import time
import json
import uuid
from typing import Any, Optional, Callable, Awaitable
from collections import defaultdict

from .types import (
    NodeData, WorkflowNodeDef, WorkflowConnectionDef,
    ExecutionStatus, StepStatus,
)
from .node_registry import NodeRegistry


# 类型别名: 状态回调函数
StatusCallback = Callable[[dict[str, Any]], Awaitable[None]]


class WorkflowEngine:
    """工作流 DAG 执行引擎"""

    def __init__(self, on_status: Optional[StatusCallback] = None):
        self._on_status = on_status

    async def execute(
        self,
        execution_id: str,
        nodes: list[dict],
        connections: list[dict],
        trigger_data: Optional[dict] = None,
        variables: Optional[dict] = None,
        user_id: str = "system",
    ) -> dict[str, Any]:
        """执行工作流

        Args:
            execution_id: 执行记录 ID
            nodes: 节点定义列表
            connections: 连线定义列表
            trigger_data: 触发器数据
            variables: 工作流变量
            user_id: 触发用户

        Returns:
            执行结果摘要
        """
        # 解析定义
        node_defs = [WorkflowNodeDef.from_dict(n) for n in nodes]
        conn_defs = [WorkflowConnectionDef.from_dict(c) for c in connections]

        node_map = {n.id: n for n in node_defs}

        # 构建邻接表
        adjacency: dict[str, list[WorkflowConnectionDef]] = defaultdict(list)
        in_degree: dict[str, int] = {n.id: 0 for n in node_defs}
        for conn in conn_defs:
            adjacency[conn.source].append(conn)
            if conn.target in in_degree:
                in_degree[conn.target] += 1

        # 拓扑排序（Kahn 算法）
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        topo_order: list[str] = []
        while queue:
            nid = queue.pop(0)
            topo_order.append(nid)
            for conn in adjacency.get(nid, []):
                in_degree[conn.target] -= 1
                if in_degree[conn.target] == 0:
                    queue.append(conn.target)

        if len(topo_order) != len(node_defs):
            raise ValueError("工作流存在循环依赖")

        # 执行状态
        node_outputs: dict[str, NodeData] = {}
        step_results: list[dict] = []
        total_tokens = 0
        total_latency = 0
        completed = 0
        failed = False
        error_msg: Optional[str] = None

        await self._emit_status(execution_id, {
            "event": "execution.started",
            "status": ExecutionStatus.RUNNING,
            "totalNodes": len(node_defs),
        })

        for node_id in topo_order:
            node_def = node_map[node_id]
            node_impl = NodeRegistry.get(node_def.type)

            if not node_impl:
                step_result = self._make_step(
                    execution_id, node_def, StepStatus.FAILED,
                    error=f"未知节点类型: {node_def.type}",
                )
                step_results.append(step_result)
                failed = True
                error_msg = f"节点 '{node_def.name}' 类型未注册: {node_def.type}"
                await self._emit_status(execution_id, {
                    "event": "step.failed", "nodeId": node_id,
                    "nodeName": node_def.name, "error": error_msg,
                })
                break

            # 收集上游数据
            input_data = self._collect_inputs(node_id, conn_defs, node_outputs, trigger_data)
            # 注入用户和变量
            input_data.metadata["_user_id"] = user_id
            if variables:
                input_data.metadata["_variables"] = variables

            await self._emit_status(execution_id, {
                "event": "step.started", "nodeId": node_id,
                "nodeName": node_def.name, "nodeType": node_def.type,
            })

            start_time = time.time()
            try:
                output = await node_impl.execute(input_data, node_def.config)
                elapsed_ms = int((time.time() - start_time) * 1000)
                tokens = output.metadata.get("tokens", 0)
                total_tokens += tokens
                total_latency += elapsed_ms
                completed += 1

                # 条件分支特殊处理
                if node_def.type == "condition":
                    condition_result = output.metadata.get("_condition_result", True)
                    output.metadata["_branch"] = "true" if condition_result else "false"

                node_outputs[node_id] = output

                step_result = self._make_step(
                    execution_id, node_def, StepStatus.SUCCESS,
                    input_data=input_data, output_data=output,
                    latency_ms=elapsed_ms, tokens=tokens,
                )
                step_results.append(step_result)

                await self._emit_status(execution_id, {
                    "event": "step.completed", "nodeId": node_id,
                    "nodeName": node_def.name, "status": "success",
                    "latencyMs": elapsed_ms, "tokens": tokens,
                })

            except Exception as e:
                elapsed_ms = int((time.time() - start_time) * 1000)
                total_latency += elapsed_ms
                error_msg = f"节点 '{node_def.name}' 执行失败: {type(e).__name__}: {e}"

                step_result = self._make_step(
                    execution_id, node_def, StepStatus.FAILED,
                    input_data=input_data, error=str(e),
                    latency_ms=elapsed_ms,
                )
                step_results.append(step_result)
                failed = True

                await self._emit_status(execution_id, {
                    "event": "step.failed", "nodeId": node_id,
                    "nodeName": node_def.name, "error": str(e),
                    "latencyMs": elapsed_ms,
                })
                break

        # 标记被跳过的节点
        executed_ids = {s["nodeId"] for s in step_results}
        for node_def in node_defs:
            if node_def.id not in executed_ids:
                step_results.append(self._make_step(
                    execution_id, node_def, StepStatus.SKIPPED,
                ))

        final_status = ExecutionStatus.FAILED if failed else ExecutionStatus.SUCCESS

        await self._emit_status(execution_id, {
            "event": "execution.finished",
            "status": final_status,
            "completedNodes": completed,
            "totalNodes": len(node_defs),
            "totalTokens": total_tokens,
            "totalLatencyMs": total_latency,
            "error": error_msg,
        })

        return {
            "execution_id": execution_id,
            "status": final_status,
            "steps": step_results,
            "completed_nodes": completed,
            "total_nodes": len(node_defs),
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency,
            "error": error_msg,
        }

    def _collect_inputs(
        self,
        node_id: str,
        connections: list[WorkflowConnectionDef],
        outputs: dict[str, NodeData],
        trigger_data: Optional[dict],
    ) -> NodeData:
        """收集上游节点的输出作为当前节点的输入"""
        incoming = [c for c in connections if c.target == node_id]

        if not incoming:
            # 根节点（触发器）— 使用 trigger_data
            if trigger_data:
                return NodeData.single(trigger_data)
            return NodeData()

        merged_items: list[dict] = []
        merged_meta: dict[str, Any] = {}

        for conn in incoming:
            source_output = outputs.get(conn.source)
            if not source_output:
                continue

            # 条件分支过滤: 只有匹配的分支才传递数据
            branch = source_output.metadata.get("_branch")
            if branch and conn.source_handle in ("true", "false"):
                if conn.source_handle != branch:
                    continue

            merged_items.extend(source_output.items)
            merged_meta.update(source_output.metadata)

        return NodeData(items=merged_items, metadata=merged_meta)

    def _make_step(
        self,
        execution_id: str,
        node_def: WorkflowNodeDef,
        status: StepStatus,
        input_data: Optional[NodeData] = None,
        output_data: Optional[NodeData] = None,
        error: Optional[str] = None,
        latency_ms: int = 0,
        tokens: int = 0,
    ) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "executionId": execution_id,
            "nodeId": node_def.id,
            "nodeName": node_def.name,
            "nodeType": node_def.type,
            "status": status,
            "inputData": input_data.to_dict() if input_data else {},
            "outputData": output_data.to_dict() if output_data else {},
            "error": error,
            "tokens": tokens,
            "latencyMs": latency_ms,
        }

    async def _emit_status(self, execution_id: str, data: dict):
        """推送执行状态到回调"""
        if self._on_status:
            try:
                await self._on_status({"executionId": execution_id, **data})
            except Exception:
                pass
