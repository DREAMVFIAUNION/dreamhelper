"""工作流节点注册 — 启动时注册所有内置节点"""

from .node_registry import NodeRegistry
from .nodes.trigger_nodes import (
    ManualTriggerNode, CronTriggerNode, WebhookTriggerNode, EventTriggerNode,
)
from .nodes.llm_node import LlmNode
from .nodes.agent_node import AgentNode
from .nodes.skill_node import SkillNode
from .nodes.http_node import HttpNode
from .nodes.condition_node import ConditionNode
from .nodes.transform_node import TransformNode
from .nodes.delay_node import DelayNode
from .nodes.code_node import CodeNode
from .nodes.notification_node import NotificationNode
from .nodes.loop_node import LoopNode
from .nodes.merge_node import MergeNode
from .nodes.switch_node import SwitchNode


def register_workflow_nodes():
    """注册所有内置工作流节点"""
    nodes = [
        # 触发器
        ManualTriggerNode(),
        CronTriggerNode(),
        WebhookTriggerNode(),
        EventTriggerNode(),
        # AI
        LlmNode(),
        AgentNode(),
        # 技能 & 工具
        SkillNode(),
        HttpNode(),
        CodeNode(),
        # 逻辑
        ConditionNode(),
        TransformNode(),
        DelayNode(),
        LoopNode(),
        MergeNode(),
        SwitchNode(),
        # 输出
        NotificationNode(),
    ]
    for node in nodes:
        NodeRegistry.register(node)
    print(f"  ✓ Workflow nodes registered: {len(nodes)} types")
