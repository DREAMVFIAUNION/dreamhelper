"""Agent 核心数据结构（第一章 1.2）"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import uuid


class AgentStepType(str, Enum):
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"
    ERROR = "error"


@dataclass
class AgentStep:
    type: AgentStepType
    content: str
    tool_name: Optional[str] = None
    tool_input: Optional[dict[str, Any]] = None
    tool_output: Optional[str] = None
    is_final: bool = False
    final_answer: Optional[str] = None
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Optional[dict[str, Any]] = None


@dataclass
class AgentContext:
    session_id: str
    user_id: str
    agent_id: str = ""
    system_prompt: str = ""
    model_name: str = "abab6.5s-chat"
    temperature: float = 0.7
    max_steps: int = 10
    tools: list[str] = field(default_factory=list)
    history: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
