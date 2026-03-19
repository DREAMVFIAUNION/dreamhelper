"""共享限流器实例 — 供各路由模块使用 SlowAPI 装饰器"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# 全局限流器（基于客户端 IP）
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
