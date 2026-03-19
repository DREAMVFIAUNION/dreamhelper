"""节点注册中心 — 管理所有可用的工作流节点类型"""

from typing import Dict, Optional

from .base_node import BaseNode
from .types import NodeDescriptor


class NodeRegistry:
    """全局工作流节点注册中心"""

    _nodes: Dict[str, BaseNode] = {}

    @classmethod
    def register(cls, node: BaseNode):
        desc = node.descriptor()
        cls._nodes[desc.type] = node

    @classmethod
    def get(cls, node_type: str) -> Optional[BaseNode]:
        return cls._nodes.get(node_type)

    @classmethod
    def list_descriptors(cls) -> list[dict]:
        return [n.descriptor().to_dict() for n in cls._nodes.values()]

    @classmethod
    def list_by_category(cls) -> dict[str, list[dict]]:
        result: dict[str, list[dict]] = {}
        for node in cls._nodes.values():
            desc = node.descriptor()
            cat = desc.category
            if cat not in result:
                result[cat] = []
            result[cat].append(desc.to_dict())
        return result
