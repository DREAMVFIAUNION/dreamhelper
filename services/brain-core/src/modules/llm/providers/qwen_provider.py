"""Qwen 提供商 — 继承 OpenAI 兼容接口，改 base_url + 模型列表"""

from .openai_provider import OpenAIProvider


QWEN_MODELS = [
    "qwen-plus",
    "qwen-turbo",
    "qwen-max",
    "qwen3-235b-a22b",
    "qwen3-30b-a3b",
    "qwen3-32b",
    "qwen3-14b",
    "qwen-plus-latest",
    "qwen-turbo-latest",
]


class QwenProvider(OpenAIProvider):
    """Qwen API（通义千问，OpenAI 兼容格式）"""

    name = "qwen"

    def __init__(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
        super().__init__(api_key=api_key, base_url=base_url)

    def supports_model(self, model: str) -> bool:
        return model in QWEN_MODELS
