"""Hook 事件系统 — 声明式事件注册与异步分发"""

import asyncio
import logging
from enum import Enum
from typing import Any, Callable, Coroutine
from datetime import datetime, timezone


class HookEventType(str, Enum):
    SESSION_START = "session:start"
    SESSION_END = "session:end"
    MEMORY_UPDATE = "memory:update"
    CRON_FIRE = "cron:fire"
    TOOL_CALL = "tool:call"
    TOOL_RESULT = "tool:result"
    WEBHOOK_RECEIVE = "webhook:receive"
    AGENT_ROUTE = "agent:route"
    AGENT_BOOTSTRAP = "agent:bootstrap"
    COMPACTION = "compaction:done"
    SKILL_EXECUTE = "skill:execute"
    VISION_ANALYZE = "vision:analyze"
    BROWSER_ACTION = "browser:action"


class HookEvent:
    """事件载体"""

    def __init__(self, event_type: str, payload: dict[str, Any] | None = None):
        self.event_type = event_type
        self.payload = payload or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()


HandlerFn = Callable[[HookEvent], Coroutine[Any, Any, None]]


class HookRegistry:
    """全局 Hook 注册中心 — 支持装饰器注册 + 并行触发"""

    _handlers: dict[str, list[HandlerFn]] = {}
    _emit_count: int = 0

    @classmethod
    def on(cls, event_type: str):
        """装饰器: 注册事件处理器

        Usage:
            @HookRegistry.on("session:start")
            async def on_session_start(event: HookEvent):
                ...
        """
        def decorator(fn: HandlerFn) -> HandlerFn:
            if event_type not in cls._handlers:
                cls._handlers[event_type] = []
            cls._handlers[event_type].append(fn)
            return fn
        return decorator

    @classmethod
    def register(cls, event_type: str, handler: HandlerFn) -> None:
        """命令式注册"""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)

    @classmethod
    async def emit(cls, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """触发事件 — 并行执行所有处理器，单个失败不影响其他"""
        handlers = cls._handlers.get(event_type, [])
        if not handlers:
            return

        cls._emit_count += 1
        event = HookEvent(event_type, payload)

        tasks = [cls._safe_call(h, event) for h in handlers]
        await asyncio.gather(*tasks)

    @classmethod
    async def _safe_call(cls, handler: HandlerFn, event: HookEvent) -> None:
        """安全调用处理器，捕获异常"""
        try:
            await handler(event)
        except Exception:
            logging.getLogger(__name__).exception("Hook handler failed")

    @classmethod
    def get_stats(cls) -> dict:
        return {
            "registered_events": len(cls._handlers),
            "total_handlers": sum(len(h) for h in cls._handlers.values()),
            "emit_count": cls._emit_count,
            "events": {k: len(v) for k, v in cls._handlers.items()},
        }

    @classmethod
    def reset(cls) -> None:
        """清空所有注册（测试用）"""
        cls._handlers.clear()
        cls._emit_count = 0
