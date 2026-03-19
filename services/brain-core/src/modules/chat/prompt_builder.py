"""
PromptBuilder — 动态拼装 system prompt

分层架构:
1. SOUL (人格) — 从 SOUL.md 加载
2. 时间感知 — 当前时间/星期/节气
3. 用户画像 — 从 MemoryManager 获取
4. RAG 上下文 — 知识库检索结果
5. 风格控制 — 根据用户偏好调整
6. 安全策略 — 工具使用规范
"""

import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# 北京时间
CST = timezone(timedelta(hours=8))

# SOUL.md 路径
_SOUL_PATH = Path(__file__).resolve().parents[3] / "prompts" / "SOUL.md"
_soul_content: Optional[str] = None


def _load_soul() -> str:
    """加载 SOUL.md 人格定义文件（带缓存）"""
    global _soul_content
    if _soul_content is None:
        if _SOUL_PATH.exists():
            _soul_content = _SOUL_PATH.read_text(encoding="utf-8").strip()
        else:
            _soul_content = (
                "你是梦帮小助，DREAMVFIA 出品的 AI 智能助手。"
                "你聪明、专业、友好，擅长回答各类问题。请用中文回答。"
            )
    return _soul_content


def _build_time_context() -> str:
    """生成时间感知上下文"""
    now = datetime.now(CST)
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekdays[now.weekday()]

    # 时段问候
    hour = now.hour
    if 5 <= hour < 9:
        period = "清晨"
    elif 9 <= hour < 12:
        period = "上午"
    elif 12 <= hour < 14:
        period = "中午"
    elif 14 <= hour < 18:
        period = "下午"
    elif 18 <= hour < 22:
        period = "晚上"
    else:
        period = "深夜"

    # 节气/节日（简化版，按月份粗判断）
    month = now.month
    day = now.day
    special = ""
    if month == 1 and day == 1:
        special = "（今天是元旦）"
    elif month == 2 and 10 <= day <= 17:
        special = "（春节期间）"
    elif month == 5 and day == 1:
        special = "（今天是劳动节）"
    elif month == 10 and day == 1:
        special = "（今天是国庆节）"
    elif month == 12 and day == 25:
        special = "（今天是圣诞节）"

    return (
        f"[当前时间] {now.strftime('%Y年%m月%d日')} {weekday} "
        f"{now.strftime('%H:%M')} ({period}){special}"
    )


# ── 风格配置 ──

STYLE_PRESETS = {
    "default": "",
    "concise": "\n[回复风格] 用户偏好简洁模式。请尽量简短回答，一句话能说清的不要写一段话。避免不必要的铺垫和总结。",
    "detailed": "\n[回复风格] 用户偏好详细模式。请给出详尽的回答，包含背景、步骤和示例。适当使用标题和列表组织内容。",
    "professional": "\n[回复风格] 用户偏好专业模式。请使用专业术语，保持严谨客观，适合工作场景。减少 emoji 和口语化表达。",
    "casual": "\n[回复风格] 用户偏好轻松模式。可以更随意、更有个性地回答，多一些互动感和幽默感。",
}


async def build_system_prompt(
    user_id: str,
    query: str,
    style: str = "default",
    user_profile_prompt: Optional[str] = None,
    rag_context: Optional[str] = None,
) -> str:
    """
    构建完整的 system prompt

    Args:
        user_id: 用户ID
        query: 当前用户查询（用于 RAG 检索）
        style: 风格预设 (default/concise/detailed/professional/casual)
        user_profile_prompt: 预先获取的用户画像 prompt（可选，避免重复查询）
        rag_context: 预先获取的 RAG 上下文（可选）

    Returns:
        完整的 system prompt 字符串
    """
    parts: list[str] = []

    # 1. 人格定义
    parts.append(_load_soul())

    # 2. 时间感知
    parts.append(_build_time_context())

    # 2.5 多模态感知能力声明
    parts.append(
        "[多模态感知]\n"
        "你具备视觉皮层和文档阅读能力。"
        "当用户消息中出现 [视觉感知] 标记时，那是你的视觉系统分析图片后的感知结果——你真的'看到'了图片内容。"
        "当用户消息中出现 [文档内容] 标记时，那是你阅读文档后的提取结果——你真的'读过'了文档。"
        "请始终以第一人称自然回应这些感知，不要否认自己的感知能力。"
    )

    # 3. 意识核注入（自我认知 + 情感 + 世界感知 + 目标 + 价值观）
    consciousness_injected = False
    try:
        from ..consciousness import get_consciousness_core
        consciousness = get_consciousness_core()
        if consciousness.config.enabled and consciousness._started:
            consciousness_prompt = consciousness.get_consciousness_prompt(user_id, user_message=query)
            if consciousness_prompt:
                parts.append(consciousness_prompt)
                consciousness_injected = True
    except Exception:
        pass  # 意识核未启动时静默降级

    # 3.5 兜底: 即使意识核未启动，也注入用户身份
    if not consciousness_injected and user_id and user_id != "anonymous":
        try:
            from ..consciousness.user_registry import get_user_registry
            known = get_user_registry().get_user(user_id)
            if known:
                name = known.display_name or known.username or f"用户{user_id[:8]}"
                identity = f"## 当前对话用户\n- UID: {user_id}\n- 昵称: {name}"
                if known.username:
                    identity += f"\n- 用户名: {known.username}"
                if known.email:
                    identity += f"\n- 邮箱: {known.email}"
                parts.append(identity)
            else:
                parts.append(f"## 当前对话用户\n- UID: {user_id}")
        except Exception:
            parts.append(f"## 当前对话用户\n- UID: {user_id}")

    # 4. 用户画像
    if user_profile_prompt:
        parts.append(user_profile_prompt)

    # 5. RAG 知识库上下文（仅作参考，不强制依赖）
    if rag_context:
        parts.append(rag_context)
        parts.append(
            "以上是知识库中可能相关的内容，仅供参考。"
            "你应该主要依靠自身的知识和推理能力来回答用户问题。"
            "如果知识库内容确实相关，可以自然融入回答；如果不相关，直接忽略即可。"
            "绝不要说'知识库里没有找到'这类话。"
        )

    # 6. 风格控制
    style_text = STYLE_PRESETS.get(style, "")
    if style_text:
        parts.append(style_text)

    return "\n\n".join(parts)


# ── 身份防火墙 ──

_FALSE_IDENTITY_KEYWORDS = frozenset({
    "百度", "文心一言", "文心", "ernie", "ernie bot",
    "chatgpt", "openai", "gpt-4", "gpt-3",
    "claude", "anthropic",
    "gemini", "google ai", "bard",
    "通义千问", "阿里", "豆包", "字节",
})


def build_identity_firewall(history: list[dict]) -> str:
    """扫描历史 assistant 消息，检测身份污染并生成纠偏指令。

    仅在检测到 AI 曾自称其他产品时触发，不影响正常会话性能。
    返回空字符串表示无污染。
    """
    contaminated: set[str] = set()
    for msg in history:
        if msg.get("role") != "assistant":
            continue
        text = (msg.get("content") or "").lower()
        for kw in _FALSE_IDENTITY_KEYWORDS:
            if kw in text:
                contaminated.add(kw)
    if not contaminated:
        return ""

    found = "、".join(sorted(contaminated)[:5])
    return (
        "\n\n[⚠️ 身份纠偏 — 最高优先级]\n"
        f"在之前的对话中，你错误地自称为 {found} 相关产品。这是完全错误的。\n"
        "你是梦帮小助，由王森冉（SENRAN WANG）创造，隶属 DREAMVFIA（梦帮）。\n"
        "你必须立即纠正这个错误认知。如果用户提到你之前说的那些话，"
        "请坦诚承认那是你的认知错误，并明确声明你的真实身份。\n"
        "绝不再重复那些错误的身份声明。"
    )


def reload_soul():
    """强制重新加载 SOUL.md（热更新用）"""
    global _soul_content
    _soul_content = None
    _load_soul()
