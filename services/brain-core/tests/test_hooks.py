"""Hook 事件系统测试"""

import pytest
from src.modules.hooks.hook_registry import HookRegistry, HookEventType, HookEvent


@pytest.fixture(autouse=True)
def reset_hooks():
    """每个测试前重置 Hook 注册"""
    HookRegistry.reset()
    yield
    HookRegistry.reset()


def test_hook_event_types():
    assert HookEventType.SESSION_START == "session:start"
    assert HookEventType.SESSION_END == "session:end"
    assert HookEventType.AGENT_BOOTSTRAP == "agent:bootstrap"
    assert HookEventType.COMPACTION == "compaction:done"
    assert HookEventType.VISION_ANALYZE == "vision:analyze"
    assert HookEventType.BROWSER_ACTION == "browser:action"
    assert HookEventType.SKILL_EXECUTE == "skill:execute"


def test_hook_event_payload():
    event = HookEvent("test:event", {"key": "value"})
    assert event.event_type == "test:event"
    assert event.payload == {"key": "value"}
    assert event.timestamp  # 非空


def test_hook_event_empty_payload():
    event = HookEvent("test:event")
    assert event.payload == {}


@pytest.mark.asyncio
async def test_register_and_emit():
    results = []

    @HookRegistry.on("test:event")
    async def handler(event: HookEvent):
        results.append(event.payload)

    await HookRegistry.emit("test:event", {"data": 42})
    assert len(results) == 1
    assert results[0]["data"] == 42


@pytest.mark.asyncio
async def test_multiple_handlers():
    results = []

    @HookRegistry.on("multi:event")
    async def handler1(event: HookEvent):
        results.append("h1")

    @HookRegistry.on("multi:event")
    async def handler2(event: HookEvent):
        results.append("h2")

    await HookRegistry.emit("multi:event")
    assert set(results) == {"h1", "h2"}


@pytest.mark.asyncio
async def test_emit_unregistered_event():
    # 不应报错
    await HookRegistry.emit("unknown:event", {"x": 1})


@pytest.mark.asyncio
async def test_handler_error_isolated():
    results = []

    @HookRegistry.on("error:event")
    async def bad_handler(event: HookEvent):
        raise ValueError("boom")

    @HookRegistry.on("error:event")
    async def good_handler(event: HookEvent):
        results.append("ok")

    await HookRegistry.emit("error:event")
    # 好的 handler 不受影响
    assert results == ["ok"]


@pytest.mark.asyncio
async def test_imperative_register():
    results = []

    async def my_handler(event: HookEvent):
        results.append(event.payload.get("val"))

    HookRegistry.register("imp:event", my_handler)
    await HookRegistry.emit("imp:event", {"val": 99})
    assert results == [99]


def test_get_stats():
    @HookRegistry.on("stat:a")
    async def h1(e): pass

    @HookRegistry.on("stat:a")
    async def h2(e): pass

    @HookRegistry.on("stat:b")
    async def h3(e): pass

    stats = HookRegistry.get_stats()
    assert stats["registered_events"] == 2
    assert stats["total_handlers"] == 3
    assert stats["events"]["stat:a"] == 2
    assert stats["events"]["stat:b"] == 1


@pytest.mark.asyncio
async def test_emit_count():
    @HookRegistry.on("count:event")
    async def h(e): pass

    await HookRegistry.emit("count:event")
    await HookRegistry.emit("count:event")
    assert HookRegistry.get_stats()["emit_count"] == 2


def test_reset():
    @HookRegistry.on("reset:event")
    async def h(e): pass

    assert HookRegistry.get_stats()["total_handlers"] == 1
    HookRegistry.reset()
    assert HookRegistry.get_stats()["total_handlers"] == 0
    assert HookRegistry.get_stats()["emit_count"] == 0
