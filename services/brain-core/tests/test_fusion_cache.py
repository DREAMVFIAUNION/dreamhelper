"""融合缓存单元测试"""

import time
import pytest


def test_cache_put_and_get():
    """写入后应能命中"""
    from src.modules.dual_brain.fusion_cache import FusionCache
    cache = FusionCache(max_size=10, max_age=60)
    cache.put("hello", "compete", 0.6, 0.4, "result text", 0.85)
    entry = cache.get("hello", "compete", 0.6, 0.4)
    assert entry is not None
    assert entry.content == "result text"
    assert entry.confidence == 0.85


def test_cache_miss():
    """未缓存的查询应返回 None"""
    from src.modules.dual_brain.fusion_cache import FusionCache
    cache = FusionCache()
    assert cache.get("unknown", "compete", 0.5, 0.5) is None


def test_cache_different_strategy_miss():
    """不同策略应不命中"""
    from src.modules.dual_brain.fusion_cache import FusionCache
    cache = FusionCache()
    cache.put("hello", "compete", 0.6, 0.4, "result", 0.85)
    assert cache.get("hello", "complement", 0.6, 0.4) is None


def test_cache_low_confidence_skip():
    """低置信度结果不应被缓存"""
    from src.modules.dual_brain.fusion_cache import FusionCache
    cache = FusionCache()
    cache.put("low conf", "compete", 0.5, 0.5, "bad result", 0.3)
    assert cache.get("low conf", "compete", 0.5, 0.5) is None


def test_cache_lru_eviction():
    """超过容量应淘汰最旧条目"""
    from src.modules.dual_brain.fusion_cache import FusionCache
    cache = FusionCache(max_size=3, max_age=3600)
    for i in range(5):
        cache.put(f"query{i}", "compete", 0.5, 0.5, f"result{i}", 0.8)
    # 前两个应被淘汰
    assert cache.get("query0", "compete", 0.5, 0.5) is None
    assert cache.get("query1", "compete", 0.5, 0.5) is None
    # 后三个应在
    assert cache.get("query4", "compete", 0.5, 0.5) is not None


def test_cache_ttl_expiry():
    """过期条目应返回 None"""
    from src.modules.dual_brain.fusion_cache import FusionCache
    cache = FusionCache(max_size=10, max_age=0.01)  # 10ms TTL
    cache.put("expire", "compete", 0.5, 0.5, "old", 0.9)
    time.sleep(0.02)
    assert cache.get("expire", "compete", 0.5, 0.5) is None


def test_cache_hit_count():
    """命中计数应正确递增"""
    from src.modules.dual_brain.fusion_cache import FusionCache
    cache = FusionCache()
    cache.put("count", "compete", 0.5, 0.5, "result", 0.8)
    cache.get("count", "compete", 0.5, 0.5)
    cache.get("count", "compete", 0.5, 0.5)
    entry = cache.get("count", "compete", 0.5, 0.5)
    assert entry is not None
    assert entry.hit_count == 3


def test_cache_stats():
    """统计信息应正确"""
    from src.modules.dual_brain.fusion_cache import FusionCache
    cache = FusionCache(max_size=50)
    cache.put("a", "compete", 0.5, 0.5, "r", 0.8)
    cache.get("a", "compete", 0.5, 0.5)  # hit
    cache.get("b", "compete", 0.5, 0.5)  # miss
    stats = cache.get_stats()
    assert stats["size"] == 1
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.5


def test_cache_invalidate():
    """清空缓存"""
    from src.modules.dual_brain.fusion_cache import FusionCache
    cache = FusionCache()
    cache.put("x", "compete", 0.5, 0.5, "r", 0.8)
    cache.invalidate()
    assert cache.get("x", "compete", 0.5, 0.5) is None
    assert cache.get_stats()["size"] == 0


def test_cache_case_insensitive():
    """查询应大小写不敏感"""
    from src.modules.dual_brain.fusion_cache import FusionCache
    cache = FusionCache()
    cache.put("Hello World", "compete", 0.5, 0.5, "r", 0.8)
    assert cache.get("hello world", "compete", 0.5, 0.5) is not None
