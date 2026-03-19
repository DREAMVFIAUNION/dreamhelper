"""多 Agent 协作编排器（Phase 5）

支持:
- 拓扑排序依赖执行
- 每个 Agent 步骤标注来源
- 前一个 Agent 的结果传递给下一个
- 预置协作模板（分析→写作、分析→编码等）
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, AsyncGenerator

from ..base.base_agent import BaseAgent
from ..base.types import AgentContext, AgentStep, AgentStepType


@dataclass
class AgentNode:
    agent: BaseAgent
    dependencies: list[str] = field(default_factory=list)
    condition: Optional[str] = None


class Orchestrator:
    """管理多个 Agent 的协作执行"""

    def __init__(self):
        self._agents: Dict[str, AgentNode] = {}

    def register(
        self,
        name: str,
        agent: BaseAgent,
        dependencies: list[str] | None = None,
        condition: str | None = None,
    ):
        self._agents[name] = AgentNode(
            agent=agent,
            dependencies=dependencies or [],
            condition=condition,
        )

    async def execute(
        self, user_input: str, context: AgentContext
    ) -> AsyncGenerator[AgentStep, None]:
        """按依赖拓扑顺序执行 Agent 链，前一个结果传递给后续"""
        executed: set[str] = set()
        results: Dict[str, str] = {}  # agent_name → final_answer

        for name in self._resolve_order():
            node = self._agents[name]

            if not all(dep in executed for dep in node.dependencies):
                continue

            # 构建输入：原始 + 前置 Agent 结果
            enriched_input = user_input
            if node.dependencies:
                dep_context = "\n\n".join(
                    f"[{dep} 的分析结果]\n{results[dep]}"
                    for dep in node.dependencies if dep in results
                )
                enriched_input = f"{user_input}\n\n{dep_context}"

            # 标记当前 Agent
            yield AgentStep(
                type=AgentStepType.THINKING,
                content=f"正在由 {node.agent.description or name} 处理...",
                metadata={"orchestrator_agent": name},
            )

            final = ""
            async for step in node.agent.run(enriched_input, context):
                step.metadata = step.metadata or {}
                step.metadata["orchestrator_agent"] = name
                if step.is_final and step.final_answer:
                    final = step.final_answer
                yield step

            results[name] = final
            executed.add(name)

    def _resolve_order(self) -> list[str]:
        """拓扑排序"""
        visited: set[str] = set()
        order: list[str] = []

        def dfs(name: str):
            if name in visited:
                return
            visited.add(name)
            for dep in self._agents[name].dependencies:
                if dep in self._agents:
                    dfs(dep)
            order.append(name)

        for name in self._agents:
            dfs(name)

        return order


def create_analysis_then_code(analysis_agent: BaseAgent, code_agent: BaseAgent) -> Orchestrator:
    """预置模板：先分析需求，再生成代码"""
    orch = Orchestrator()
    orch.register("analysis", analysis_agent)
    orch.register("code", code_agent, dependencies=["analysis"])
    return orch


def create_analysis_then_writing(analysis_agent: BaseAgent, writing_agent: BaseAgent) -> Orchestrator:
    """预置模板：先分析主题，再撰写文章"""
    orch = Orchestrator()
    orch.register("analysis", analysis_agent)
    orch.register("writing", writing_agent, dependencies=["analysis"])
    return orch
