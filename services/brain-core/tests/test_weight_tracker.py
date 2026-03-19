"""动态权重追踪器单元测试"""

import pytest


def test_tracker_cold_start():
    """冷启动阶段应返回默认权重"""
    from src.modules.dual_brain.weight_tracker import DynamicWeightTracker
    from src.modules.dual_brain.activation import TaskType
    tracker = DynamicWeightTracker(min_samples=5)
    left, right = tracker.get_adjusted_weights(TaskType.CODE, 0.65, 0.35)
    assert left == 0.65
    assert right == 0.35


def test_tracker_record_and_count():
    """记录应正确累计"""
    from src.modules.dual_brain.weight_tracker import DynamicWeightTracker
    from src.modules.dual_brain.activation import TaskType
    tracker = DynamicWeightTracker()
    for _ in range(3):
        tracker.record(TaskType.CODE, 0.7, 0.3, 0.85)
    stats = tracker.get_stats()
    assert stats["code"]["count"] == 3
    assert stats["code"]["avg_confidence"] > 0


def test_tracker_adapts_after_min_samples():
    """超过最小样本数后应开始自适应调整"""
    from src.modules.dual_brain.weight_tracker import DynamicWeightTracker
    from src.modules.dual_brain.activation import TaskType
    tracker = DynamicWeightTracker(min_samples=3, learning_rate=0.3)

    # 记录5次高置信度的高左脑权重
    for _ in range(5):
        tracker.record(TaskType.WRITING, 0.3, 0.7, 0.95)

    left, right = tracker.get_adjusted_weights(TaskType.WRITING, 0.35, 0.65)
    # 应向 0.3/0.7 方向漂移（但受 max_drift 限制）
    assert left <= 0.35  # 应小于等于默认值
    assert right >= 0.65  # 应大于等于默认值
    assert abs(left + right - 1.0) < 0.01  # 归一化


def test_tracker_max_drift_limit():
    """权重调整不应超过最大漂移幅度"""
    from src.modules.dual_brain.weight_tracker import DynamicWeightTracker
    from src.modules.dual_brain.activation import TaskType
    tracker = DynamicWeightTracker(min_samples=2, max_drift=0.1, learning_rate=0.5)

    # 极端偏向左脑
    for _ in range(10):
        tracker.record(TaskType.CHAT, 1.0, 0.0, 0.99)

    left, right = tracker.get_adjusted_weights(TaskType.CHAT, 0.4, 0.6)
    # 最大漂移 ±0.1, 默认 0.4 → 最多到 0.5
    assert left <= 0.5 + 0.01
    assert left >= 0.3 - 0.01


def test_tracker_normalized_weights():
    """输出权重之和应为 1.0"""
    from src.modules.dual_brain.weight_tracker import DynamicWeightTracker
    from src.modules.dual_brain.activation import TaskType
    tracker = DynamicWeightTracker(min_samples=2)
    for _ in range(5):
        tracker.record(TaskType.ANALYSIS, 0.55, 0.45, 0.8)
    left, right = tracker.get_adjusted_weights(TaskType.ANALYSIS, 0.55, 0.45)
    assert abs(left + right - 1.0) < 0.01


def test_tracker_independent_task_types():
    """不同 TaskType 应独立追踪"""
    from src.modules.dual_brain.weight_tracker import DynamicWeightTracker
    from src.modules.dual_brain.activation import TaskType
    tracker = DynamicWeightTracker(min_samples=2)
    for _ in range(3):
        tracker.record(TaskType.CODE, 0.8, 0.2, 0.9)
        tracker.record(TaskType.CREATIVE, 0.2, 0.8, 0.9)

    stats = tracker.get_stats()
    assert stats["code"]["count"] == 3
    assert stats["creative"]["count"] == 3
    # EMA 应分别偏向各自方向
    assert stats["code"]["ema_weights"]["left"] > stats["creative"]["ema_weights"]["left"]


def test_tracker_stats_format():
    """stats 应返回正确格式"""
    from src.modules.dual_brain.weight_tracker import DynamicWeightTracker
    from src.modules.dual_brain.activation import TaskType
    tracker = DynamicWeightTracker()
    tracker.record(TaskType.QA, 0.6, 0.4, 0.75)
    stats = tracker.get_stats()
    assert "qa" in stats
    assert "count" in stats["qa"]
    assert "avg_confidence" in stats["qa"]
    assert "ema_weights" in stats["qa"]
    assert "left" in stats["qa"]["ema_weights"]
    assert "right" in stats["qa"]["ema_weights"]
