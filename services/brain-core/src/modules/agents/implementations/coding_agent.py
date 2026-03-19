"""CodingAgent — 类 Claude Code 的智能编程 Agent

基于现有 BaseAgent 扩展:
  - Think: 仿生大脑分析代码任务（丘脑路由 → 皮层深度处理）
  - Act: 调用文件/终端/搜索工具
  - Observe: 解析工具执行结果
  - 循环: 直到任务完成或达到步数上限

特性:
  - 自动代码搜索（grep 定位相关文件）
  - 编辑前自动读取（强制 Read-before-Edit）
  - 编辑后自动验证（运行测试/lint）
  - 错误自动重试（最多 3 次）
  - Plan 模式（只规划不执行）

工具链:
  shell_exec, file_read, file_write, file_edit, file_search, code_grep
"""

import json
import logging
from typing import Any

from ..base.base_agent import BaseAgent
from ..base.types import AgentStep, AgentStepType, AgentContext
from ...llm.llm_client import get_llm_client
from ...llm.types import LLMRequest
from ...tools.tool_registry import ToolRegistry

logger = logging.getLogger("agents.coding")

# CodingAgent 可用工具
CODING_TOOLS = [
    "shell_exec", "file_read", "file_write", "file_edit",
    "file_search", "code_grep",
]

CODING_SYSTEM_PROMPT = """你是梦帮小助的编程 Agent — 一个强大的本地编程助手。你可以直接操作文件系统和终端。

## 可用工具

{tools_description}

## 工作流程

1. **理解任务**: 分析用户的编程需求
2. **搜索定位**: 用 file_search/code_grep 找到相关文件
3. **阅读理解**: 用 file_read 读取文件内容（编辑前必须先读取）
4. **执行修改**: 用 file_write/file_edit 进行代码修改
5. **验证测试**: 用 shell_exec 运行测试或 lint 验证

## 输出格式

每次回复必须是一个合法 JSON 对象:

需要调用工具时:
```json
{{"thought": "分析和计划", "action": "工具名称", "action_input": {{"参数": "值"}}}}
```

任务完成时:
```json
{{"thought": "总结", "final_answer": "给用户的完整回答"}}
```

## 关键规则

1. **编辑前必须先读取** — 调用 file_edit 前必须先用 file_read 读取文件
2. **old_string 必须精确匹配** — 包括所有空格和缩进
3. **每次只调用一个工具**
4. **危险操作需说明原因** — rm/del 等命令需解释为什么必须执行
5. **出错时分析原因重试** — 不要盲目重复相同操作
6. **任务完成后总结变更** — final_answer 中列出所有修改的文件

{plan_mode_hint}"""

PLAN_MODE_HINT = """
## ⚠️ Plan 模式

当前处于 **Plan 模式** — 只规划不执行。
- 分析任务并列出详细的执行步骤
- 说明会修改哪些文件、如何修改
- 不要调用任何工具
- 直接输出 final_answer 作为执行计划
"""


def _build_coding_tools_description() -> str:
    """构建 CodingAgent 工具描述"""
    lines = []
    for tool_name in CODING_TOOLS:
        tool = ToolRegistry.get(tool_name)
        if tool:
            params = tool.args_schema.model_json_schema().get("properties", {})
            param_desc = ", ".join(
                f'{k}: {v.get("description", v.get("type", "any"))}'
                for k, v in params.items()
            )
            lines.append(f"- **{tool.name}**: {tool.description}\n  参数: {{{param_desc}}}")
    return "\n".join(lines) if lines else "(无可用工具)"


class CodingAgent(BaseAgent):
    """CodingAgent — 智能编程循环引擎"""

    def __init__(self):
        super().__init__(
            name="coding_agent",
            description="类 Claude Code 的智能编程 Agent，可直接操作文件和终端",
        )
        self._read_files: set[str] = set()  # 已读取的文件（强制 Read-before-Edit）
        self._retry_count: dict[str, int] = {}  # 错误重试计数
        self._plan_mode: bool = False

    def set_plan_mode(self, enabled: bool):
        """切换 Plan 模式"""
        self._plan_mode = enabled

    async def think(self, user_input: str, context: AgentContext) -> AgentStep:
        """推理步骤: LLM 分析代码任务，决定下一步"""
        tools_desc = _build_coding_tools_description()
        plan_hint = PLAN_MODE_HINT if self._plan_mode else ""
        system = CODING_SYSTEM_PROMPT.format(
            tools_description=tools_desc,
            plan_mode_hint=plan_hint,
        )

        messages = [{"role": "system", "content": system}]

        # 加入历史上下文
        for h in context.history:
            messages.append(h)

        # 加入当前用户输入（仅首次）
        if not context.history:
            messages.append({"role": "user", "content": user_input})

        try:
            client = get_llm_client()
            request = LLMRequest(
                messages=messages,
                model=context.model_name,
                temperature=context.temperature,
                max_tokens=4096,
                stream=False,
            )
            response = await client.complete(request)
            raw = response.content.strip()

            # 解析 JSON
            data = self._parse_json(raw)

            thought = data.get("thought", "")

            # 最终回答
            if "final_answer" in data:
                return AgentStep(
                    type=AgentStepType.FINAL_ANSWER,
                    content=thought,
                    is_final=True,
                    final_answer=data["final_answer"],
                )

            # 工具调用
            action = data.get("action", "")
            action_input = data.get("action_input", {})

            if not action:
                return AgentStep(
                    type=AgentStepType.THINKING,
                    content=thought or raw,
                )

            # 验证工具是否在允许列表
            if action not in CODING_TOOLS:
                return AgentStep(
                    type=AgentStepType.ERROR,
                    content=f"工具 '{action}' 不在 CodingAgent 允许列表中。可用: {CODING_TOOLS}",
                )

            # 强制 Read-before-Edit 检查
            if action == "file_edit":
                file_path = action_input.get("path", "")
                if file_path and file_path not in self._read_files:
                    # 自动插入 file_read 步骤
                    logger.info("[CodingAgent] Auto-inserting file_read before edit: %s", file_path)
                    return AgentStep(
                        type=AgentStepType.TOOL_CALL,
                        content=f"[Auto] 编辑前必须先读取文件: {file_path}",
                        tool_name="file_read",
                        tool_input={"path": file_path},
                    )

            return AgentStep(
                type=AgentStepType.TOOL_CALL,
                content=thought,
                tool_name=action,
                tool_input=action_input,
            )

        except Exception as e:
            logger.error("[CodingAgent] Think error: %s", e)
            return AgentStep(
                type=AgentStepType.ERROR,
                content=f"推理错误: {e}",
            )

    async def act(
        self, tool_name: str, tool_input: dict[str, Any], context: AgentContext
    ) -> AgentStep:
        """执行工具调用"""
        try:
            result = await ToolRegistry.execute(tool_name, **tool_input)

            # 记录已读取的文件
            if tool_name == "file_read":
                file_path = tool_input.get("path", "")
                if file_path:
                    import os
                    self._read_files.add(file_path)
                    self._read_files.add(os.path.abspath(file_path))

            # 错误重试逻辑
            error_key = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)[:100]}"
            if "❌" in result or "⛔" in result:
                self._retry_count[error_key] = self._retry_count.get(error_key, 0) + 1
                if self._retry_count[error_key] >= 3:
                    result += "\n\n⚠️ 此操作已失败 3 次，请尝试不同的方法。"
            else:
                self._retry_count.pop(error_key, None)

            return AgentStep(
                type=AgentStepType.OBSERVATION,
                content=result,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=result,
            )

        except Exception as e:
            logger.error("[CodingAgent] Tool execution error: %s", e)
            return AgentStep(
                type=AgentStepType.OBSERVATION,
                content=f"工具执行失败: {e}",
                tool_name=tool_name,
                tool_input=tool_input,
            )

    async def synthesize(self, user_input: str, context: AgentContext) -> AgentStep:
        """超过最大步数，综合所有信息生成最终回答"""
        # 收集所有观察结果
        observations = [
            h["content"] for h in context.history
            if h.get("role") == "user" and "[Observation]" in h.get("content", "")
        ]

        summary_prompt = (
            f"你是编程 Agent，已经执行了 {context.max_steps} 步但未完成任务。\n"
            f"原始任务: {user_input}\n"
            f"工具执行历史 ({len(observations)} 个观察结果):\n"
            + "\n---\n".join(obs[:200] for obs in observations[-5:])
            + "\n\n请综合以上信息，给用户一个完整的总结回答。说明已完成的部分和未完成的部分。"
        )

        try:
            client = get_llm_client()
            request = LLMRequest(
                messages=[{"role": "user", "content": summary_prompt}],
                model=context.model_name,
                temperature=0.3,
                max_tokens=2048,
                stream=False,
            )
            response = await client.complete(request)
            return AgentStep(
                type=AgentStepType.FINAL_ANSWER,
                content="达到最大步数，综合回答",
                is_final=True,
                final_answer=response.content.strip(),
            )
        except Exception as e:
            return AgentStep(
                type=AgentStepType.FINAL_ANSWER,
                content="综合失败",
                is_final=True,
                final_answer=f"编程任务未完成（已执行 {context.max_steps} 步）。错误: {e}",
            )

    def reset(self):
        """重置 Agent 状态（新任务时调用）"""
        self._read_files.clear()
        self._retry_count.clear()

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """解析 LLM 输出的 JSON（兼容 markdown code block）"""
        text = raw.strip()
        # 去除 markdown code block
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 对象
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        # 无法解析，返回为 thought
        return {"thought": text}
