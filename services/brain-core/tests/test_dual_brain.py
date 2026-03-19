"""双脑融合模块单元测试"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── BrainConfig ──

def test_brain_config_defaults():
    """BrainConfig 应从 settings 读取默认值"""
    from src.modules.dual_brain.brain_config import BrainConfig
    cfg = BrainConfig()
    assert cfg.left_model != ""
    assert cfg.right_model != ""
    assert cfg.judge_model != ""
    assert cfg.fusion_model != ""
    assert isinstance(cfg.enabled, bool)
    assert cfg.left_timeout > 0
    assert cfg.right_timeout > 0
    assert cfg.simple_query_threshold > 0
    assert cfg.min_confidence > 0


def test_brain_config_override():
    """BrainConfig 可手动覆盖字段"""
    from src.modules.dual_brain.brain_config import BrainConfig
    cfg = BrainConfig(left_model="test-left", right_model="test-right")
    assert cfg.left_model == "test-left"
    assert cfg.right_model == "test-right"


# ── BrainActivation ──

def test_activation_detect_code():
    """代码关键词应检测为 CODE 类型"""
    from src.modules.dual_brain.activation import BrainActivation, TaskType
    act = BrainActivation()
    assert act.detect_task_type("写一个Python函数") == TaskType.CODE
    assert act.detect_task_type("帮我调试这个bug") == TaskType.CODE


def test_activation_detect_writing():
    """写作关键词应检测为 WRITING 类型"""
    from src.modules.dual_brain.activation import BrainActivation, TaskType
    act = BrainActivation()
    assert act.detect_task_type("写一篇关于AI的文章") == TaskType.WRITING


def test_activation_detect_math():
    """数学关键词应检测为 MATH 类型"""
    from src.modules.dual_brain.activation import BrainActivation, TaskType
    act = BrainActivation()
    assert act.detect_task_type("计算这个方程的解") == TaskType.MATH


def test_activation_detect_chat_default():
    """无关键词命中应默认为 CHAT"""
    from src.modules.dual_brain.activation import BrainActivation, TaskType
    act = BrainActivation()
    assert act.detect_task_type("你好呀") == TaskType.CHAT


def test_activation_detect_complex():
    """多类型高分命中应检测为 COMPLEX"""
    from src.modules.dual_brain.activation import BrainActivation, TaskType
    act = BrainActivation()
    # 包含 CODE 关键词(代码+函数) + ANALYSIS 关键词(分析+为什么)
    result = act.detect_task_type("分析这段代码为什么函数报错，帮我调试")
    assert result in (TaskType.CODE, TaskType.COMPLEX)


def test_activation_weights():
    """权重应在 0-1 范围内，且左+右=1"""
    from src.modules.dual_brain.activation import BrainActivation, TaskType
    act = BrainActivation()
    for tt in TaskType:
        left, right = act.get_weights(tt)
        assert 0 <= left <= 1, f"{tt}: left={left}"
        assert 0 <= right <= 1, f"{tt}: right={right}"
        assert abs(left + right - 1.0) < 0.01, f"{tt}: sum={left+right}"


def test_activation_strategy_names():
    """每个 TaskType 应有对应的融合策略名称"""
    from src.modules.dual_brain.activation import BrainActivation, TaskType
    act = BrainActivation()
    valid_strategies = {"compete", "complement", "debate", "weighted"}
    for tt in TaskType:
        name = act.get_fusion_strategy_name(tt)
        assert name in valid_strategies, f"{tt}: strategy={name}"


# ── CorpusCallosum ──

def test_corpus_callosum_agreement():
    """一致性分数应在 0-1 范围"""
    from src.modules.dual_brain.corpus_callosum import CorpusCallosum
    from src.modules.dual_brain.hemisphere import HemisphereResult
    cc = CorpusCallosum()
    left = HemisphereResult(content="Python是一门编程语言", hemisphere="left", model="m1", latency_ms=100)
    right = HemisphereResult(content="Python是流行的编程语言", hemisphere="right", model="m2", latency_ms=200)
    score = cc.exchange(left, right)
    assert 0 <= score <= 1


def test_corpus_callosum_identical():
    """完全相同的内容应有高一致性"""
    from src.modules.dual_brain.corpus_callosum import CorpusCallosum
    from src.modules.dual_brain.hemisphere import HemisphereResult
    cc = CorpusCallosum()
    text = "这是完全相同的回答内容"
    left = HemisphereResult(content=text, hemisphere="left", model="m1", latency_ms=100)
    right = HemisphereResult(content=text, hemisphere="right", model="m2", latency_ms=200)
    score = cc.exchange(left, right)
    assert score == 1.0


def test_corpus_callosum_stats():
    """统计信息应正确累计"""
    from src.modules.dual_brain.corpus_callosum import CorpusCallosum
    from src.modules.dual_brain.hemisphere import HemisphereResult
    cc = CorpusCallosum()
    for _ in range(3):
        left = HemisphereResult(content="aaa bbb", hemisphere="left", model="m1", latency_ms=0)
        right = HemisphereResult(content="bbb ccc", hemisphere="right", model="m2", latency_ms=0)
        cc.exchange(left, right)
    stats = cc.get_stats()
    assert stats["total_exchanges"] == 3
    assert 0 < stats["avg_agreement"] < 1
    assert len(stats["recent_agreements"]) == 3


def test_corpus_callosum_debate_escalation():
    """严重分歧应建议升级为辩论"""
    from src.modules.dual_brain.corpus_callosum import CorpusCallosum
    from src.modules.dual_brain.hemisphere import HemisphereResult
    cc = CorpusCallosum()
    left = HemisphereResult(content="完全不同的内容甲", hemisphere="left", model="m1", latency_ms=0)
    right = HemisphereResult(content="totally different content B", hemisphere="right", model="m2", latency_ms=0)
    assert cc.should_escalate_to_debate(left, right) is True


# ── FusionStrategy ──

def test_fusion_strategy_enum():
    """FusionStrategy 枚举值应正确"""
    from src.modules.dual_brain.cortex import FusionStrategy
    assert FusionStrategy("compete") == FusionStrategy.COMPETE
    assert FusionStrategy("complement") == FusionStrategy.COMPLEMENT
    assert FusionStrategy("debate") == FusionStrategy.DEBATE
    assert FusionStrategy("weighted") == FusionStrategy.WEIGHTED


# ── BrainEngine 单例 ──

def test_brain_engine_singleton():
    """get_brain_engine 应返回同一个实例"""
    from src.modules.dual_brain import get_brain_engine
    e1 = get_brain_engine()
    e2 = get_brain_engine()
    assert e1 is e2


def test_brain_engine_reset():
    """reset_brain_engine 应创建新实例"""
    from src.modules.dual_brain import get_brain_engine, reset_brain_engine
    e1 = get_brain_engine()
    reset_brain_engine()
    e2 = get_brain_engine()
    assert e1 is not e2


def test_brain_engine_stats():
    """get_stats 应返回完整结构"""
    from src.modules.dual_brain import get_brain_engine, reset_brain_engine
    reset_brain_engine()
    brain = get_brain_engine()
    stats = brain.get_stats()
    assert "enabled" in stats
    assert "left_model" in stats
    assert "right_model" in stats
    assert "corpus_callosum" in stats
    assert "total_exchanges" in stats["corpus_callosum"]
    # C1 新增字段
    assert "fusion_cache" in stats
    assert "size" in stats["fusion_cache"]
    assert "hits" in stats["fusion_cache"]
    assert "weight_tracker" in stats
    assert isinstance(stats["weight_tracker"], dict)


# ── Prompts ──

def test_prompts_all_task_types_covered():
    """每个 TaskType 在 LEFT/RIGHT_BRAIN_HINTS 中都有对应项"""
    from src.modules.dual_brain.activation import TaskType
    from src.modules.dual_brain.prompts import LEFT_BRAIN_HINTS, RIGHT_BRAIN_HINTS
    for tt in TaskType:
        assert tt in LEFT_BRAIN_HINTS, f"Missing left hint for {tt}"
        assert tt in RIGHT_BRAIN_HINTS, f"Missing right hint for {tt}"
