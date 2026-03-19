"""意识核配置 — 从全局 settings 读取环境变量，支持 .env 控制"""

import logging
from dataclasses import dataclass

logger = logging.getLogger("consciousness.config")


@dataclass
class ConsciousnessConfig:
    """意识核配置参数 — __post_init__ 从 settings 读取环境变量覆盖默认值"""
    enabled: bool = True

    # LLM 模型
    consciousness_model: str = ""            # 内心独白/反思用模型（留空=LLM 默认路由）
    world_model_name: str = ""               # 世界模型推理用模型（预留）

    # 内心独白
    inner_voice_interval: int = 900          # 内心独白间隔(秒), 默认15分钟
    inner_voice_temperature: float = 0.85    # 创意思考温度

    # 世界模型
    world_observe_interval: int = 3600       # 世界观察间隔(秒), 默认1小时
    world_news_enabled: bool = True
    world_weather_city: str = "深圳"          # 默认观察城市

    # 情感
    emotion_decay_rate: float = 0.05         # 每小时衰减5%向基线回归
    emotion_event_driven: bool = True

    # 表达控制
    max_expressions_per_user_per_2h: int = 1  # 每用户每2小时最多主动表达1次
    max_daily_expressions_per_user: int = 5   # 每用户每天最多5次
    expression_importance_threshold: float = 0.7  # 想法重要度>此值才考虑表达

    # 自我反思
    self_reflect_after_conversation: bool = True
    self_reflect_min_messages: int = 3        # 至少3轮对话后才触发反思

    # 进化追踪
    evolution_enabled: bool = True
    evolution_self_assess_interval: int = 86400  # 自评间隔(秒), 默认24小时

    def __post_init__(self):
        """从全局 settings 读取环境变量覆盖默认值"""
        try:
            from ...common.config import settings
            self.enabled = settings.CONSCIOUSNESS_ENABLED
            self.consciousness_model = settings.CONSCIOUSNESS_MODEL
            self.world_model_name = settings.CONSCIOUSNESS_WORLD_MODEL
            self.inner_voice_interval = settings.CONSCIOUSNESS_THINK_INTERVAL

            # 智能模型回退: 检查配置的模型是否有可用的 Provider
            self.consciousness_model = self._resolve_model(settings, self.consciousness_model)

            logger.info(
                "[ConsciousnessConfig] loaded: enabled=%s, model=%s, interval=%ds",
                self.enabled, self.consciousness_model or "(default)", self.inner_voice_interval,
            )
        except Exception as e:
            logger.warning("[ConsciousnessConfig] Failed to read settings, using defaults: %s", e)

    @staticmethod
    def _resolve_model(settings, model: str) -> str:
        """检查模型对应的 Provider 是否有 API Key, 否则回退到可用的模型"""
        # 模型前缀 → 所需 API Key 映射
        prefix_key_map = {
            "nvidia/": settings.NVIDIA_API_KEY,
            "moonshotai/": settings.KIMI_API_KEY,
            "qwen/": settings.QWEN_API_KEY,
        }
        for prefix, key in prefix_key_map.items():
            if model.startswith(prefix) and not key:
                # 按优先级回退: GLM > Qwen > MiniMax > 留空(LLM默认路由)
                fallback_chain = [
                    (settings.GLM_API_KEY, "glm-4.7"),
                    (settings.QWEN_API_KEY, "qwen-plus"),
                    (settings.MINIMAX_API_KEY, "MiniMax-M1"),
                ]
                for fb_key, fb_model in fallback_chain:
                    if fb_key:
                        logger.warning(
                            "[ConsciousnessConfig] Model '%s' provider unavailable, falling back to '%s'",
                            model, fb_model,
                        )
                        return fb_model
                logger.warning(
                    "[ConsciousnessConfig] Model '%s' provider unavailable, no fallback found — using LLM default",
                    model,
                )
                return ""
        return model
