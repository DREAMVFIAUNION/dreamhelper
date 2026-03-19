"""Agent 基类 — ReAct 核心循环（第一章 1.3）"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any

from .types import AgentStep, AgentStepType, AgentContext


class BaseAgent(ABC):
    """所有 Agent 的基类，实现 ReAct 推理循环"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    async def run(
        self, user_input: str, context: AgentContext
    ) -> AsyncGenerator[AgentStep, None]:
        """ReAct 主循环：Think → Act → Observe → Think → ... → Final Answer"""
        steps = 0

        while steps < context.max_steps:
            steps += 1

            # 1. 思考：LLM 决定下一步（工具调用 or 最终回答）
            thought = await self.think(user_input, context)
            yield thought

            if thought.is_final:
                return

            # 2. 执行工具
            if thought.tool_name and thought.tool_input is not None:
                # 记录 assistant 的工具调用决策到历史
                context.history.append({
                    "role": "assistant",
                    "content": f"[Thought] {thought.content}\n[Action] {thought.tool_name}({thought.tool_input})",
                })

                observation = await self.act(thought.tool_name, thought.tool_input, context)
                yield observation

                # 记录工具观察结果到历史（作为 user 角色，让 LLM 继续推理）
                context.history.append({
                    "role": "user",
                    "content": f"[Observation] 工具 {thought.tool_name} 返回: {observation.content}\n\n请根据以上结果继续推理，决定是否需要调用更多工具，或者给出最终回答。",
                })

            # 循环回到 think，让 LLM 根据 observation 决定下一步

        # 超过最大步数，强制综合回答
        final = await self.synthesize(user_input, context)
        yield final

    @abstractmethod
    async def think(self, user_input: str, context: AgentContext) -> AgentStep:
        """推理步骤：分析问题，决定下一步行动"""
        ...

    @abstractmethod
    async def act(
        self, tool_name: str, tool_input: dict[str, Any], context: AgentContext
    ) -> AgentStep:
        """执行步骤：调用工具"""
        ...

    async def evaluate(self, context: AgentContext) -> bool:
        """评估是否需要继续推理，默认继续"""
        return True

    @abstractmethod
    async def synthesize(self, user_input: str, context: AgentContext) -> AgentStep:
        """综合所有信息生成最终回答"""
        ...
