"""半球定义 — 左脑皮层(逻辑推理/GLM-4.7) + 右脑皮层(创意洞察/Qwen-3-235B)"""

import time
from abc import ABC
from dataclasses import dataclass, field
from typing import Optional

from ..llm.llm_client import get_llm_client
from ..llm.types import LLMRequest, LLMResponse
from .brain_config import BrainConfig
from .activation import TaskType
from .prompts import (
    LEFT_BRAIN_HINTS, RIGHT_BRAIN_HINTS,
    LEFT_SYSTEM_TEMPLATE, RIGHT_SYSTEM_TEMPLATE,
)


@dataclass
class HemisphereResult:
    """半球推理结果"""
    content: str
    hemisphere: str          # "left" | "right"
    model: str
    latency_ms: float
    token_usage: dict = field(default_factory=dict)
    thinking: str = ""


class Hemisphere(ABC):
    """半球基类"""

    def __init__(self, name: str, model: str, config: BrainConfig):
        self.name = name
        self.model = model
        self.config = config

    def build_prompt(self, query: str, base_system: str, task_type: TaskType) -> str:
        """构建半球专用 system prompt（子类重写）"""
        raise NotImplementedError

    async def process(self, messages: list[dict]) -> HemisphereResult:
        """调用 LLM 进行推理"""
        start = time.time()
        client = get_llm_client()
        request = LLMRequest(
            messages=messages,
            model=self.model,
            temperature=self._get_temperature(),
            max_tokens=self._get_max_tokens(),
            stream=False,
        )
        response = await client.complete(request)
        latency = (time.time() - start) * 1000

        return HemisphereResult(
            content=response.content,
            hemisphere=self.name,
            model=self.model,
            latency_ms=latency,
            token_usage=response.usage,
        )

    def _get_temperature(self) -> float:
        raise NotImplementedError

    def _get_max_tokens(self) -> int:
        return 4096


class LeftHemisphere(Hemisphere):
    """
    左脑皮层 — GLM-4.7 推理模型

    特质: 逻辑推理、思维链分析、语言处理、序列推导、细节聚焦
    擅长: 代码、数学、事实验证、结构化分析、步骤推理
    优势: 具有 reasoning_content (思维链), 500K 上下文窗口
    """

    def __init__(self, config: BrainConfig):
        super().__init__(
            name="left",
            model=config.left_model,
            config=config,
        )

    def build_prompt(self, query: str, base_system: str, task_type: TaskType) -> str:
        role_hint = LEFT_BRAIN_HINTS.get(task_type, "")
        return LEFT_SYSTEM_TEMPLATE.format(base_system=base_system, role_hint=role_hint)

    def _get_temperature(self) -> float:
        return 0.3  # 逻辑推理需要更低温度确保精确性

    def _get_max_tokens(self) -> int:
        return 8192  # GLM-4.7 推理模型需要更多 tokens 输出思维链 + 实际内容


class RightHemisphere(Hemisphere):
    """
    右脑皮层 — Qwen-3-235B

    特质: 创意联想、全局视角、模式识别、类比思考、跨领域融合
    擅长: 写作、创意、方案设计、开放性问题、发散性思维
    优势: 235B 参数量(22B 活跃), 知识面最广
    """

    def __init__(self, config: BrainConfig):
        super().__init__(
            name="right",
            model=config.right_model,
            config=config,
        )

    def build_prompt(self, query: str, base_system: str, task_type: TaskType) -> str:
        role_hint = RIGHT_BRAIN_HINTS.get(task_type, "")
        return RIGHT_SYSTEM_TEMPLATE.format(base_system=base_system, role_hint=role_hint)

    def _get_temperature(self) -> float:
        return 0.7

    def _get_max_tokens(self) -> int:
        return 6144
