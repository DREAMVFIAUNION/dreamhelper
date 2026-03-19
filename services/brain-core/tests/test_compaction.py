"""会话压缩 Compaction 测试"""

import pytest
from src.modules.chat.compaction import (
    should_compact,
    compact_history,
    _fallback_summary,
    estimate_tokens,
    COMPACT_THRESHOLD,
    KEEP_RECENT,
)


def _make_history(n: int) -> list[dict]:
    """生成 n 条交替的 user/assistant 消息"""
    msgs = []
    for i in range(n):
        role = "user" if i % 2 == 0 else "assistant"
        msgs.append({"role": role, "content": f"第 {i+1} 条消息内容"})
    return msgs


@pytest.mark.asyncio
async def test_should_compact_below_threshold():
    msgs = _make_history(10)
    assert await should_compact(msgs) is False


@pytest.mark.asyncio
async def test_should_compact_above_threshold():
    msgs = _make_history(20)
    assert await should_compact(msgs) is True


@pytest.mark.asyncio
async def test_should_compact_exact_threshold():
    msgs = _make_history(COMPACT_THRESHOLD)
    assert await should_compact(msgs) is True


@pytest.mark.asyncio
async def test_should_compact_ignores_system():
    msgs = [{"role": "system", "content": "sys"}] * 20
    assert await should_compact(msgs) is False


@pytest.mark.asyncio
async def test_compact_history_no_compress_needed():
    msgs = _make_history(6)
    result, summary = await compact_history(msgs, keep_recent=8)
    # 不需要压缩，应该原样返回
    assert result == msgs
    assert summary == ""


@pytest.mark.asyncio
async def test_compact_history_with_fallback():
    """LLM 不可用时应降级为 fallback 摘要"""
    msgs = _make_history(20)
    result, summary = await compact_history(msgs, keep_recent=8)
    # 结果应该包含最近 8 条 + 摘要
    chat_msgs = [m for m in result if m["role"] in ("user", "assistant")]
    assert len(chat_msgs) == 8
    # 应该有摘要
    assert summary != "" or any("[会话上下文摘要]" in m.get("content", "") for m in result)


@pytest.mark.asyncio
async def test_compact_history_preserves_system():
    msgs = [{"role": "system", "content": "You are helpful."}] + _make_history(20)
    result, summary = await compact_history(msgs, keep_recent=8)
    system_msgs = [m for m in result if m["role"] == "system"]
    # 原始 system + 可能的摘要 system
    assert len(system_msgs) >= 1


def test_fallback_summary():
    msgs = [
        {"role": "user", "content": "你好，请介绍一下Python"},
        {"role": "assistant", "content": "Python是一种高级编程语言..."},
        {"role": "user", "content": "它的优势是什么？"},
    ]
    summary = _fallback_summary(msgs)
    assert "用户问" in summary
    assert "Python" in summary


def test_fallback_summary_with_existing():
    existing = "之前讨论了JavaScript"
    msgs = [{"role": "user", "content": "现在讲讲Python"}]
    summary = _fallback_summary(msgs, existing_summary=existing)
    assert "JavaScript" in summary
    assert "Python" in summary


def test_fallback_summary_max_5():
    msgs = _make_history(20)
    summary = _fallback_summary(msgs)
    # 最多 5 条
    assert summary.count("用户问") <= 5


def test_estimate_tokens_chinese():
    msgs = [{"role": "user", "content": "你好世界"}]
    tokens = estimate_tokens(msgs)
    assert tokens > 0
    assert tokens == int(4 * 1.5)  # 4 个中文字


def test_estimate_tokens_empty():
    assert estimate_tokens([]) == 0
    assert estimate_tokens([{"role": "user", "content": ""}]) == 0
