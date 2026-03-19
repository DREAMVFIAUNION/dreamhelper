"""工作流引擎核心数据结构

架构定位: 工作流 = 执行层（肌肉），由双脑（大脑）调度
原生 Python 实现，节点/连线/执行模型
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import uuid


# ── 节点类型 ──────────────────────────────────────────────

class NodeType(str, Enum):
    # 触发器
    TRIGGER_MANUAL = "trigger_manual"
    TRIGGER_CRON = "trigger_cron"
    TRIGGER_WEBHOOK = "trigger_webhook"
    TRIGGER_EVENT = "trigger_event"
    # AI
    LLM = "llm"
    AGENT = "agent"
    # 技能 & 工具
    SKILL = "skill"
    HTTP = "http"
    CODE = "code"
    # 逻辑
    CONDITION = "condition"
    TRANSFORM = "transform"
    DELAY = "delay"
    LOOP = "loop"
    MERGE = "merge"
    SWITCH = "switch"
    # 输出
    NOTIFICATION = "notification"


class NodeCategory(str, Enum):
    TRIGGER = "trigger"
    AI = "ai"
    SKILL = "skill"
    LOGIC = "logic"
    OUTPUT = "output"


NODE_CATEGORIES = {
    NodeType.TRIGGER_MANUAL: NodeCategory.TRIGGER,
    NodeType.TRIGGER_CRON: NodeCategory.TRIGGER,
    NodeType.TRIGGER_WEBHOOK: NodeCategory.TRIGGER,
    NodeType.TRIGGER_EVENT: NodeCategory.TRIGGER,
    NodeType.LLM: NodeCategory.AI,
    NodeType.AGENT: NodeCategory.AI,
    NodeType.SKILL: NodeCategory.SKILL,
    NodeType.HTTP: NodeCategory.SKILL,
    NodeType.CODE: NodeCategory.SKILL,
    NodeType.CONDITION: NodeCategory.LOGIC,
    NodeType.TRANSFORM: NodeCategory.LOGIC,
    NodeType.DELAY: NodeCategory.LOGIC,
    NodeType.LOOP: NodeCategory.LOGIC,
    NodeType.MERGE: NodeCategory.LOGIC,
    NodeType.SWITCH: NodeCategory.LOGIC,
    NodeType.NOTIFICATION: NodeCategory.OUTPUT,
}


# ── 执行状态 ──────────────────────────────────────────────

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


# ── 节点数据流 ────────────────────────────────────────────

@dataclass
class NodeData:
    """节点间传递的统一数据格式"""
    items: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"items": self.items, "metadata": self.metadata}

    @classmethod
    def from_dict(cls, d: dict) -> "NodeData":
        return cls(items=d.get("items", []), metadata=d.get("metadata", {}))

    @classmethod
    def single(cls, data: dict[str, Any]) -> "NodeData":
        """快捷创建单条数据"""
        return cls(items=[data])


# ── 工作流定义结构 ────────────────────────────────────────

@dataclass
class WorkflowNodeDef:
    """节点定义（存储在 Workflow.nodes JSON 中）"""
    id: str
    type: str  # NodeType value
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    # React Flow 位置
    position: dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "config": self.config,
            "position": self.position,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WorkflowNodeDef":
        return cls(
            id=d["id"],
            type=d["type"],
            name=d.get("name", d["type"]),
            config=d.get("config", {}),
            position=d.get("position", {"x": 0, "y": 0}),
        )


@dataclass
class WorkflowConnectionDef:
    """连线定义（存储在 Workflow.connections JSON 中）"""
    id: str
    source: str  # 源节点 id
    target: str  # 目标节点 id
    source_handle: str = "output"
    target_handle: str = "input"
    condition: Optional[str] = None  # 条件分支用: "true" | "false"

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "sourceHandle": self.source_handle,
            "targetHandle": self.target_handle,
        }
        if self.condition:
            d["condition"] = self.condition
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "WorkflowConnectionDef":
        return cls(
            id=d["id"],
            source=d["source"],
            target=d["target"],
            source_handle=d.get("sourceHandle", "output"),
            target_handle=d.get("targetHandle", "input"),
            condition=d.get("condition"),
        )


# ── 节点描述（给前端的元数据）────────────────────────────

@dataclass
class NodeDescriptor:
    """描述一种节点类型，供前端节点面板展示"""
    type: str
    name: str
    description: str
    category: str
    icon: str  # lucide icon name
    color: str  # hex color
    inputs: list[str] = field(default_factory=lambda: ["input"])
    outputs: list[str] = field(default_factory=lambda: ["output"])
    config_schema: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "color": self.color,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "configSchema": self.config_schema,
        }
