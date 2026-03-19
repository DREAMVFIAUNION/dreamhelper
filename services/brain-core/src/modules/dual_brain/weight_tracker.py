"""动态权重追踪器 — 根据融合结果质量自适应调整权重

核心思路:
- 记录每种 TaskType 下不同权重配置的融合置信度
- 随着更多对话发生，逐步偏向产生更高置信度的权重组合
- 使用指数移动平均(EMA)平滑更新，避免单次异常值影响过大
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from .activation import TaskType

logger = logging.getLogger(__name__)


@dataclass
class WeightRecord:
    """某个 TaskType 下的权重追踪记录"""
    left_weight_sum: float = 0.0
    right_weight_sum: float = 0.0
    confidence_sum: float = 0.0
    count: int = 0
    ema_left: float = 0.0
    ema_right: float = 0.0
    last_updated: float = field(default_factory=time.time)


class DynamicWeightTracker:
    """
    动态权重追踪器

    工作流程:
    1. BrainEngine 完成一次融合后，调用 record() 记录结果
    2. 下次同类任务时，调用 get_adjusted_weights() 获取优化后的权重
    3. 权重调整幅度受 learning_rate 控制，避免剧烈波动

    设计约束:
    - 权重始终归一化: left + right = 1.0
    - 调整幅度上限 ±0.15（不会偏离默认值太远）
    - 至少 5 次记录后才启用自适应（冷启动保护）
    """

    def __init__(self, learning_rate: float = 0.1, min_samples: int = 5, max_drift: float = 0.15):
        self._records: dict[str, WeightRecord] = defaultdict(WeightRecord)
        self._learning_rate = learning_rate
        self._min_samples = min_samples
        self._max_drift = max_drift

    def record(
        self,
        task_type: TaskType,
        left_weight: float,
        right_weight: float,
        confidence: float,
        strategy: str = "",
    ):
        """记录一次融合结果"""
        key = task_type.value
        rec = self._records[key]

        # 用置信度加权: 高置信度的权重组合影响更大
        weighted_left = left_weight * confidence
        weighted_right = right_weight * confidence

        rec.left_weight_sum += weighted_left
        rec.right_weight_sum += weighted_right
        rec.confidence_sum += confidence
        rec.count += 1

        # EMA 更新
        alpha = self._learning_rate
        if rec.count == 1:
            rec.ema_left = left_weight
            rec.ema_right = right_weight
        else:
            rec.ema_left = alpha * left_weight * confidence + (1 - alpha) * rec.ema_left
            rec.ema_right = alpha * right_weight * confidence + (1 - alpha) * rec.ema_right

        rec.last_updated = time.time()

        logger.debug(
            "权重追踪: task=%s weights=%.2f/%.2f conf=%.2f count=%d ema=%.3f/%.3f",
            key, left_weight, right_weight, confidence, rec.count,
            rec.ema_left, rec.ema_right,
        )

    def get_adjusted_weights(
        self,
        task_type: TaskType,
        default_left: float,
        default_right: float,
    ) -> tuple[float, float]:
        """获取自适应调整后的权重

        Returns:
            (left_weight, right_weight) 归一化后的权重
        """
        key = task_type.value
        rec = self._records.get(key)

        # 冷启动: 样本不足时返回默认值
        if not rec or rec.count < self._min_samples:
            return default_left, default_right

        # 基于 EMA 计算建议权重
        total_ema = rec.ema_left + rec.ema_right
        if total_ema <= 0:
            return default_left, default_right

        suggested_left = rec.ema_left / total_ema
        suggested_right = rec.ema_right / total_ema

        # 限制漂移幅度
        adj_left = max(
            default_left - self._max_drift,
            min(default_left + self._max_drift, suggested_left),
        )
        adj_right = 1.0 - adj_left  # 保证归一化

        logger.debug(
            "权重调整: task=%s default=%.2f/%.2f → adjusted=%.2f/%.2f (samples=%d)",
            key, default_left, default_right, adj_left, adj_right, rec.count,
        )

        return round(adj_left, 3), round(adj_right, 3)

    def get_stats(self) -> dict:
        return {
            task: {
                "count": rec.count,
                "avg_confidence": round(rec.confidence_sum / rec.count, 3) if rec.count > 0 else 0,
                "ema_weights": {"left": round(rec.ema_left, 3), "right": round(rec.ema_right, 3)},
            }
            for task, rec in self._records.items()
        }
