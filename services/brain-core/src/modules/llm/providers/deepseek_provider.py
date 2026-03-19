"""DeepSeek 提供商 — 继承 OpenAI 兼容接口，改 base_url + 模型列表"""

from .openai_provider import OpenAIProvider


DEEPSEEK_MODELS = [
    "deepseek-chat",
    "deepseek-coder",
    "deepseek-reasoner",
]


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek API（OpenAI 兼容格式）"""

    name = "deepseek"

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        super().__init__(api_key=api_key, base_url=base_url)

    def supports_model(self, model: str) -> bool:
        return model in DEEPSEEK_MODELS
