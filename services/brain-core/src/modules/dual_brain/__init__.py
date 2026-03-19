"""仿生大脑模块 — 丘脑(MiniMax路由) + 左脑皮层(GLM-5) + 右脑皮层(Qwen-3.5) + 脑干(MiniMax快速) + 小脑(Kimi-K2.5) + 视觉皮层(Nemotron-VL) + 海马体(Nemotron-30B) via NVIDIA NIM"""

from typing import Optional
from .brain_engine import BrainEngine, BrainOutput
from .brain_config import BrainConfig

# 全局单例
_brain_engine: Optional[BrainEngine] = None


def get_brain_engine() -> BrainEngine:
    """获取双脑引擎全局单例"""
    global _brain_engine
    if _brain_engine is None:
        _brain_engine = BrainEngine()
    return _brain_engine


def reset_brain_engine(config: Optional[BrainConfig] = None):
    """重置双脑引擎（配置更新时调用）"""
    global _brain_engine
    _brain_engine = BrainEngine(config=config)


__all__ = [
    "BrainEngine",
    "BrainOutput",
    "BrainConfig",
    "get_brain_engine",
    "reset_brain_engine",
]
