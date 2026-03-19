"""限流器（第三章 3.7）"""

import time
from typing import Tuple


class TokenBucketRateLimiter:
    """令牌桶限流"""

    def __init__(self, rate: float = 10.0, capacity: float = 100.0):
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._last_refill = time.time()

    def _refill(self):
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def try_acquire(self, tokens: float = 1.0) -> Tuple[bool, float]:
        """尝试获取令牌，返回 (是否成功, 需等待秒数)"""
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True, 0.0
        wait_time = (tokens - self._tokens) / self.rate
        return False, wait_time
