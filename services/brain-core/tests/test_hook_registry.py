"""Hook 事件系统测试"""

import asyncio
import pytest
from src.modules.hooks.hook_registry import HookRegistry, HookEventType, HookEvent


@pytest.fixture(autouse=True)
def reset_registry():
    """每个测试前重置 Hook 注册表"""
    HookRegistry.reset()
    yield
    HookRegistry.reset()


def test_register_and_emit():
    """注册处理器并触发事件"""
    results = []

    async def handler(event: HookEvent):
        results.append(event.event_type)

    HookRegistry.register(HookEventType.SESSION_START, handler)
    asyncio.run(HookRegistry.emit(HookEventType.SESSION_START, {"session_id": "s1"}))

    assert len(results) == 1
    assert results[0] == "session:start"


def test_decorator_registration():
    """装饰器注册"""
    results = []

    @HookRegistry.on(HookEventType.SESSION_END)
    async def on_end(event: HookEvent):
        results.append(event.payload)

    asyncio.run(HookRegistry.emit(HookEventType.SESSION_END, {"user_id": "u1"}))
    assert len(results) == 1
    assert results[0]["user_id"] == "u1"


def test_multiple_handlers():
    """同一事件多个处理器并行触发"""
    results = []

    async def h1(event: HookEvent):
        results.append("h1")

    async def h2(event: HookEvent):
        results.append("h2")

    HookRegistry.register(HookEventType.TOOL_CALL, h1)
    HookRegistry.register(HookEventType.TOOL_CALL, h2)
    asyncio.run(HookRegistry.emit(HookEventType.TOOL_CALL, {}))

    assert set(results) == {"h1", "h2"}


def test_safe_call_no_crash():
    """处理器抛异常不影响其他处理器"""
    results = []

    async def bad_handler(event: HookEvent):
        raise ValueError("boom")

    async def good_handler(event: HookEvent):
        results.append("ok")

    HookRegistry.register(HookEventType.MEMORY_UPDATE, bad_handler)
    HookRegistry.register(HookEventType.MEMORY_UPDATE, good_handler)
    asyncio.run(HookRegistry.emit(HookEventType.MEMORY_UPDATE, {}))

    assert results == ["ok"]


def test_emit_no_handlers():
    """触发无处理器的事件不报错"""
    asyncio.run(HookRegistry.emit(HookEventType.CRON_FIRE, {"task": "test"}))


def test_event_payload():
    """事件载体包含 timestamp 和 payload"""
    captured = []

    async def handler(event: HookEvent):
        captured.append(event)

    HookRegistry.register(HookEventType.WEBHOOK_RECEIVE, handler)
    asyncio.run(HookRegistry.emit(HookEventType.WEBHOOK_RECEIVE, {"source": "github"}))

    assert len(captured) == 1
    assert captured[0].payload["source"] == "github"
    assert captured[0].timestamp  # ISO string


def test_get_stats():
    """统计信息"""
    async def noop(event: HookEvent):
        pass

    HookRegistry.register(HookEventType.SESSION_START, noop)
    HookRegistry.register(HookEventType.SESSION_END, noop)

    stats = HookRegistry.get_stats()
    assert stats["registered_events"] == 2
    assert stats["total_handlers"] == 2


def test_reset():
    """重置清空所有注册"""
    async def noop(event: HookEvent):
        pass

    HookRegistry.register(HookEventType.TOOL_CALL, noop)
    assert HookRegistry.get_stats()["total_handlers"] == 1

    HookRegistry.reset()
    assert HookRegistry.get_stats()["total_handlers"] == 0
    assert HookRegistry.get_stats()["emit_count"] == 0
