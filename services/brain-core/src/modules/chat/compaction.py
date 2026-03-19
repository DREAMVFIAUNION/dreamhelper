"""会话压缩 Compaction — LLM 自动摘要长对话（Phase 12）

当会话历史超过阈值时，自动将早期消息压缩为摘要，减少 Token 消耗。

策略:
1. 保留最近 N 条消息原文（recency window）
2. 将更早的消息用 LLM 压缩为 2-3 句话摘要
3. 摘要作为 [会话上下文摘要] 注入 system prompt

触发条件:
- 会话消息数 >= compact_threshold (默认 16 条)
- 保留最近 keep_recent 条原文 (默认 8 条)
- 压缩其余为摘要
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 默认配置
COMPACT_THRESHOLD = 16   # 超过此数量触发压缩
KEEP_RECENT = 8          # 保留最近 N 条原文
MAX_SUMMARY_TOKENS = 512 # 摘要最大 token
MAX_CONVERSATION_CHARS = 8000  # 传入 LLM 的对话文本最大字符数
COMPACT_COOLDOWN_SEC = 60      # 同一 session 压缩冷却 60秒

# 压缩冷却记录 {session_id: last_compact_time}
_compact_cooldowns: dict[str, float] = {}

COMPACT_PROMPT = """你是一个对话摘要专家。请将以下多轮对话压缩为 2-3 句话的简洁摘要。

要求:
1. 保留关键信息（用户问题、AI 回答的核心要点、做出的决策）
2. 保留用户提到的专有名词、数字、日期
3. 不超过 150 字
4. 使用第三人称描述

对话内容:
{conversation}

请直接输出摘要，不要加任何前缀。"""


async def should_compact(messages: list[dict], threshold: int = COMPACT_THRESHOLD) -> bool:
    """判断是否需要压缩"""
    # 只计算 user/assistant 消息
    count = sum(1 for m in messages if m.get("role") in ("user", "assistant"))
    return count >= threshold


async def compact_history(
    messages: list[dict],
    keep_recent: int = KEEP_RECENT,
    existing_summary: str = "",
) -> tuple[list[dict], str]:
    """压缩会话历史

    Args:
        messages: 完整会话历史 [{"role": ..., "content": ...}]
        keep_recent: 保留最近 N 条原文
        existing_summary: 已有的摘要（增量压缩）

    Returns:
        (compacted_messages, new_summary)
        compacted_messages: 压缩后的消息列表（摘要 + 最近消息）
        new_summary: 新的摘要文本
    """
    # 分离 system 消息和对话消息
    system_msgs = [m for m in messages if m.get("role") == "system"]
    chat_msgs = [m for m in messages if m.get("role") in ("user", "assistant")]

    if len(chat_msgs) <= keep_recent:
        # 不需要压缩
        return messages, existing_summary

    # 需要压缩的部分 vs 保留的部分
    to_compress = chat_msgs[:-keep_recent]
    to_keep = chat_msgs[-keep_recent:]

    # 生成摘要
    summary = await _generate_summary(to_compress, existing_summary)

    # 重建消息列表: system + [摘要作为 system] + 最近消息
    result = list(system_msgs)
    if summary:
        result.append({
            "role": "system",
            "content": f"[会话上下文摘要]\n{summary}",
        })
    result.extend(to_keep)

    logger.info(
        f"[Compaction] {len(chat_msgs)} msgs → summary + {len(to_keep)} recent "
        f"(compressed {len(to_compress)} msgs)"
    )

    # Hook: 压缩完成事件
    try:
        from ..hooks.hook_registry import HookRegistry, HookEventType
        await HookRegistry.emit(HookEventType.COMPACTION, {
            "original_count": len(chat_msgs),
            "compressed_count": len(to_compress),
            "kept_count": len(to_keep),
            "summary_length": len(summary),
        })
    except Exception:
        pass

    return result, summary


async def _generate_summary(
    messages: list[dict],
    existing_summary: str = "",
) -> str:
    """用 LLM 生成对话摘要"""
    if not messages:
        return existing_summary

    # 构建对话文本
    lines = []
    if existing_summary:
        lines.append(f"[之前的摘要] {existing_summary}\n")
    for m in messages:
        role = "用户" if m["role"] == "user" else "助手"
        content = m.get("content", "")[:300]  # 截断过长消息
        lines.append(f"{role}: {content}")

    conversation_text = "\n".join(lines)
    # 安全: 截断过长对话文本防止超 context window
    if len(conversation_text) > MAX_CONVERSATION_CHARS:
        conversation_text = conversation_text[:MAX_CONVERSATION_CHARS] + "\n...(已截断)"

    try:
        from ..llm.llm_client import get_llm_client
        client = get_llm_client()

        response = await client.complete(
            messages=[
                {"role": "user", "content": COMPACT_PROMPT.format(conversation=conversation_text)},
            ],
            temperature=0.3,
            max_tokens=MAX_SUMMARY_TOKENS,
        )
        summary = response if isinstance(response, str) else response.content
        return summary.strip()
    except Exception as e:
        logger.warning(f"[Compaction] LLM summary failed: {e}")
        # 降级: 手动截取关键信息
        return _fallback_summary(messages, existing_summary)


def _fallback_summary(messages: list[dict], existing_summary: str = "") -> str:
    """降级摘要: 无 LLM 时取每轮对话首句"""
    parts = []
    if existing_summary:
        parts.append(existing_summary)
    for m in messages:
        content = m.get("content", "")
        first_line = content.split("\n")[0][:80]
        if m["role"] == "user":
            parts.append(f"用户问: {first_line}")
    # 最多保留 5 条
    return " | ".join(parts[-5:])


def estimate_tokens(messages: list[dict]) -> int:
    """估算消息列表的 Token 数（粗略: 1 中文字≈1.5 token, 1 英文词≈1 token）"""
    total = 0
    for m in messages:
        content = m.get("content", "")
        # 简单估算: 中文字数 * 1.5 + 英文词数
        chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        ascii_words = len(content.encode('ascii', 'ignore').split())
        total += int(chinese_chars * 1.5 + ascii_words)
    return total
