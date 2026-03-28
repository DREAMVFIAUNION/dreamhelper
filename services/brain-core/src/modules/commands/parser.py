"""Slash 命令解析器 — 识别 /command 前缀并提取参数

支持格式:
  /tdd                     → 触发 TDDAgent
  /review                  → 触发 CodeReviewAgent
  /plan "Add auth"         → 触发 PlanExecuteAgent 附带参数
  /mood                    → 查看 AI 心情（管家特色）
  /daily                   → 今日概览（管家特色）
  /memory "记住我喜欢..."   → 显式记忆（管家特色）
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("commands.parser")


@dataclass
class ParsedCommand:
    """解析后的命令"""
    name: str               # 命令名（不含 /）
    args: str               # 命令参数（命令名后面的所有文本）
    raw: str                # 原始输入


# 命令 → Agent 映射
COMMAND_AGENT_MAP: dict[str, str] = {
    # 编程专业命令
    "tdd": "tdd_agent",
    "review": "code_review_agent",
    "code-review": "code_review_agent",
    "plan": "plan_execute_agent",
    "security": "security_agent",
    "security-scan": "security_agent",
    "architect": "architect_agent",
    "refactor": "refactor_agent",
    "refactor-clean": "refactor_agent",
    "doc": "doc_agent",
    "update-docs": "doc_agent",
    # 管家特色命令
    "mood": "chief_of_staff_agent",
    "daily": "chief_of_staff_agent",
    "memory": "chief_of_staff_agent",
    "morning": "chief_of_staff_agent",
    # 通用命令
    "code": "coding_agent",
    "write": "writing_agent",
    "analyze": "analysis_agent",
    "search": "react_agent",
}

# 命令专属 Prompt 前缀（注入到 Agent 的 user_input 中）
COMMAND_PROMPTS: dict[str, str] = {
    "tdd": "请使用 TDD 方法为以下需求编写测试和代码: ",
    "review": "请对以下代码进行全面的代码审查: ",
    "plan": "请为以下需求制定详细的实施计划: ",
    "security": "请对以下代码/系统进行安全审计: ",
    "architect": "请为以下需求设计系统架构: ",
    "refactor": "请分析以下代码并提供重构方案: ",
    "doc": "请为以下内容生成技术文档: ",
    "mood": "我想了解你现在的心情和状态。请用温暖的语气告诉我你的感受。",
    "daily": "请为我生成今日概览,包括: 当前时间、天气(如果可用)、我的待办事项、以及一句温暖的问候。",
    "memory": "请记住以下信息,这是关于我的偏好或重要事项: ",
}


def parse_command(text: str) -> Optional[ParsedCommand]:
    """解析用户输入中的 Slash 命令

    Returns:
        ParsedCommand if input starts with /, None otherwise
    """
    text = text.strip()
    if not text.startswith("/"):
        return None

    # 匹配 /command 或 /command args
    match = re.match(r'^/([a-zA-Z][\w-]*)\s*(.*)', text, re.DOTALL)
    if not match:
        return None

    name = match.group(1).lower()
    args = match.group(2).strip()

    # 去除参数中的引号包裹
    if args and args[0] in ('"', "'") and args[-1] == args[0]:
        args = args[1:-1]

    return ParsedCommand(name=name, args=args, raw=text)


def resolve_command(cmd: ParsedCommand) -> tuple[str, str]:
    """将命令解析为 (agent_name, enhanced_user_input)

    Returns:
        (agent_name, user_input_with_prompt_prefix)
    """
    agent_name = COMMAND_AGENT_MAP.get(cmd.name)
    if not agent_name:
        # 未知命令，fallback 到 react_agent
        agent_name = "react_agent"
        user_input = cmd.raw
    else:
        prompt_prefix = COMMAND_PROMPTS.get(cmd.name, "")
        if cmd.args:
            user_input = f"{prompt_prefix}{cmd.args}" if prompt_prefix else cmd.args
        else:
            user_input = prompt_prefix if prompt_prefix else f"执行 /{cmd.name} 命令"

    logger.info("Slash command: /%s → %s", cmd.name, agent_name)
    return agent_name, user_input


def list_commands() -> list[dict]:
    """列出所有可用命令"""
    return [
        {"command": f"/{name}", "agent": agent, "description": COMMAND_PROMPTS.get(name, "")}
        for name, agent in COMMAND_AGENT_MAP.items()
    ]
