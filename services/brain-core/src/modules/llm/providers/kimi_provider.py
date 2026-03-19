"""Kimi 提供商 — 继承 OpenAI 兼容接口，对接 Moonshot AI (Kimi K2.5 Code)"""

from .openai_provider import OpenAIProvider


KIMI_MODELS = [
    "kimi-k2.5-code",
    "kimi-k2",
    "moonshot-v1-128k",
    "moonshot-v1-32k",
    "moonshot-v1-8k",
]


class KimiProvider(OpenAIProvider):
    """Kimi API（Moonshot AI，OpenAI 兼容格式）"""

    name = "kimi"

    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.cn/v1"):
        super().__init__(api_key=api_key, base_url=base_url)

    def supports_model(self, model: str) -> bool:
        return model in KIMI_MODELS
