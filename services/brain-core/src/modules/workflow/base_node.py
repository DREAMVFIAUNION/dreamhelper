"""工作流节点基类 — 所有节点类型继承此类"""

from abc import ABC, abstractmethod
from typing import Any

from .types import NodeData, NodeDescriptor


class BaseNode(ABC):
    """工作流节点基类"""

    @abstractmethod
    def descriptor(self) -> NodeDescriptor:
        """返回节点元数据描述（供前端展示）"""
        ...

    @abstractmethod
    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        """执行节点逻辑

        Args:
            input_data: 上游节点传入的数据
            config: 节点配置参数

        Returns:
            NodeData: 输出数据，传给下游节点
        """
        ...
