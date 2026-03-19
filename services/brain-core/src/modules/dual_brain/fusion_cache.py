"""融合结果缓存 — LRU缓存避免相同/相似查询重复调用LLM

策略:
1. 精确匹配: query + strategy + weights 完全一致 → 直接命中
2. TTL过期: 缓存条目超过 max_age 秒后失效
3. 容量限制: 超过 max_size 时淘汰最久未使用的条目
"""

import hashlib
import time
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    content: str
    confidence: float
    fusion_strategy: str
    left_weight: float
    right_weight: float
    created_at: float = field(default_factory=time.time)
    hit_count: int = 0


class FusionCache:
    """
    融合结果 LRU 缓存

    缓存键 = hash(query + strategy + round(left_weight, 1) + round(right_weight, 1))
    适用场景:
    - 用户连续发送相同问题（重试/刷新）
    - 多会话中的高频通用问题
    """

    def __init__(self, max_size: int = 200, max_age: float = 1800.0):
        """
        Args:
            max_size: 最大缓存条目数
            max_age: 条目最大存活时间(秒), 默认30分钟
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._max_age = max_age
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _make_key(query: str, strategy: str, left_weight: float, right_weight: float) -> str:
        """生成缓存键"""
        raw = f"{query.strip().lower()}|{strategy}|{round(left_weight, 1)}|{round(right_weight, 1)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    # P3-#13: 时效敏感关键词 — 命中时跳过缓存
    _TIME_SENSITIVE_KEYWORDS = frozenset([
        "现在", "今天", "天气", "股价", "实时", "几点", "当前",
        "最新", "刚才", "此刻", "行情", "币价", "汇率",
    ])

    def _is_time_sensitive(self, query: str) -> bool:
        return any(kw in query for kw in self._TIME_SENSITIVE_KEYWORDS)

    def get(self, query: str, strategy: str, left_weight: float, right_weight: float) -> Optional[CacheEntry]:
        """查找缓存"""
        if self._is_time_sensitive(query):
            self._misses += 1
            return None

        key = self._make_key(query, strategy, left_weight, right_weight)
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        # TTL 检查
        if time.time() - entry.created_at > self._max_age:
            self._cache.pop(key, None)
            self._misses += 1
            return None

        # LRU: 移到末尾（最近使用）
        self._cache.move_to_end(key)
        entry.hit_count += 1
        self._hits += 1

        logger.debug("融合缓存命中: key=%s hits=%d", key[:8], entry.hit_count)
        return entry

    def put(
        self,
        query: str,
        strategy: str,
        left_weight: float,
        right_weight: float,
        content: str,
        confidence: float,
    ):
        """写入缓存"""
        key = self._make_key(query, strategy, left_weight, right_weight)

        # 低置信度结果不缓存
        if confidence < 0.5:
            return

        # 容量淘汰
        while len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)  # 淘汰最久未使用

        self._cache[key] = CacheEntry(
            content=content,
            confidence=confidence,
            fusion_strategy=strategy,
            left_weight=left_weight,
            right_weight=right_weight,
        )

    def invalidate(self):
        """清空缓存"""
        self._cache.clear()

    def get_stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0.0,
        }
