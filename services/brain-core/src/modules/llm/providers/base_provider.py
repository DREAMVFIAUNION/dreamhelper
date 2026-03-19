"""提供商适配器基类（第三章 3.3）"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from ..types import LLMRequest, LLMResponse


class BaseProvider(ABC):
    """所有 LLM 提供商的基类"""

    name: str

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        ...

    @abstractmethod
    def supports_model(self, model: str) -> bool:
        ...
