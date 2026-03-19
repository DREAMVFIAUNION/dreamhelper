"""胼胝体 — 连接左右脑的信息高速通道"""

import hashlib
import time
from dataclasses import dataclass, field
from collections import deque
from .hemisphere import HemisphereResult


@dataclass
class ExchangeRecord:
    """一次双脑交换记录"""
    query_hash: str
    left_content: str
    right_content: str
    agreement_score: float
    timestamp: float = 0.0


class CorpusCallosum:
    """
    胼胝体 — 双脑信息交换与一致性监控

    职责:
    1. 记录双脑的历史输出对
    2. 监测一致性: 如果两脑经常冲突 → 可能需要调整策略
    3. 冲突检测: 当两脑输出矛盾时触发辩论策略
    """

    def __init__(self, max_history: int = 100):
        self._history: deque[ExchangeRecord] = deque(maxlen=max_history)
        self._agreement_sum = 0.0
        self._exchange_count = 0

    def exchange(self, left: HemisphereResult, right: HemisphereResult) -> float:
        """记录一次双脑交换，返回一致性分数"""
        agreement = self._compute_agreement(left.content, right.content)

        record = ExchangeRecord(
            query_hash=hashlib.md5(
                (left.content[:50] + right.content[:50]).encode()
            ).hexdigest(),
            left_content=left.content[:500],
            right_content=right.content[:500],
            agreement_score=agreement,
            timestamp=time.time(),
        )
        self._history.append(record)
        self._agreement_sum += agreement
        self._exchange_count += 1

        return agreement

    def _compute_agreement(self, left_text: str, right_text: str) -> float:
        """
        计算两个回答的一致性分数 (Jaccard 相似度)

        简易方法: 基于关键词重叠率
        高级方法: 可用 Embedding 余弦相似度（Phase 5 进化）
        """
        left_words = set(left_text.split())
        right_words = set(right_text.split())

        if not left_words or not right_words:
            return 0.0

        intersection = left_words & right_words
        union = left_words | right_words

        return len(intersection) / len(union)

    def get_avg_agreement(self) -> float:
        """获取历史平均一致性"""
        if self._exchange_count == 0:
            return 0.0
        return self._agreement_sum / self._exchange_count

    def should_escalate_to_debate(self, left: HemisphereResult, right: HemisphereResult) -> bool:
        """
        当两脑输出严重分歧时，建议升级为辩论策略

        阈值: 一致性 < 0.2 → 强烈冲突
        """
        agreement = self._compute_agreement(left.content, right.content)
        return agreement < 0.2

    def get_stats(self) -> dict:
        """胼胝体统计"""
        return {
            "total_exchanges": self._exchange_count,
            "avg_agreement": round(self.get_avg_agreement(), 3),
            "recent_agreements": [
                round(r.agreement_score, 3) for r in list(self._history)[-10:]
            ],
        }
