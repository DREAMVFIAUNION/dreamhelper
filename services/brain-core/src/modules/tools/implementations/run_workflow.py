"""run_workflow 工具 — Agent 可通过此工具触发工作流执行"""

from typing import Any
from pydantic import BaseModel, Field
from ..tool_registry import BaseTool


class RunWorkflowArgs(BaseModel):
    workflow_id: str = Field(description="工作流 ID (UUID)")
    input_data: dict = Field(default_factory=dict, description="传递给工作流的输入数据")


class RunWorkflowTool(BaseTool):
    name = "run_workflow"
    description = "触发执行一个已定义的工作流。传入工作流 ID 和可选的输入数据，返回执行结果。"
    args_schema = RunWorkflowArgs

    async def execute(self, **kwargs: Any) -> str:
        workflow_id = kwargs.get("workflow_id", "")
        input_data = kwargs.get("input_data", {})

        if not workflow_id:
            return "错误：请提供 workflow_id"

        try:
            from ...workflow import db as wfdb
            from ...workflow.engine import WorkflowEngine

            # 1. 获取工作流定义
            wf = await wfdb.get_workflow(workflow_id)
            if not wf:
                return f"错误：工作流 {workflow_id} 不存在"

            if wf["status"] not in ("active", "draft"):
                return f"错误：工作流 {wf['name']} 状态为 {wf['status']}，无法执行"

            nodes = wf.get("nodes", [])
            connections = wf.get("connections", [])
            variables = wf.get("variables", {})

            if not nodes:
                return f"工作流 {wf['name']} 没有定义节点"

            # 2. 创建执行记录
            execution = await wfdb.create_execution(
                workflow_id=workflow_id,
                trigger_type="tool",
                trigger_data={"source": "agent_tool", "input": input_data},
            )
            exec_id = execution["id"]

            # 3. 执行工作流
            engine = WorkflowEngine()
            merged_vars = {**variables, **input_data}
            result = await engine.execute(
                execution_id=exec_id,
                nodes=nodes,
                connections=connections,
                trigger_data={"source": "agent_tool", "input": input_data},
                variables=merged_vars,
            )

            # 4. 更新执行状态
            status = "success" if not result.get("error") else "failed"
            await wfdb.update_execution(
                exec_id,
                status=status,
                completed_nodes=result.get("completed_nodes", 0),
                total_nodes=result.get("total_nodes", 0),
                error=result.get("error"),
            )

            # 5. 格式化返回
            if status == "success":
                output = result.get("output", {})
                summary = f"工作流 '{wf['name']}' 执行成功。"
                if output:
                    summary += f"\n输出: {str(output)[:500]}"
                return summary
            else:
                return f"工作流 '{wf['name']}' 执行失败: {result.get('error', '未知错误')}"

        except Exception as e:
            return f"工作流执行异常: {str(e)}"
