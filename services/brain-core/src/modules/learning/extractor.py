"""Instinct 提取器 — 从会话对话中自动提取行为模式

使用 LLM 分析对话记录，提取用户的:
- 编码风格偏好 (语言/框架/命名习惯)
- 工作流模式 (先测试后实现/先原型后优化)
- 情感倾向 (乐观/焦虑/完美主义)
- 沟通偏好 (简洁/详细/需要示例)
"""

import json
import uuid
import logging
from typing import Optional

from .instinct import Instinct
from ..llm.llm_client import get_llm_client
from ..llm.types import LLMRequest

logger = logging.getLogger("learning.extractor")

EXTRACTION_PROMPT = """分析以下对话记录，提取用户的行为模式和偏好。

## 提取维度
1. **coding_style**: 编码风格偏好 (框架/语言/命名/代码组织)
2. **preference**: 个人偏好 (回复长度/语气/emoji)
3. **workflow**: 工作流模式 (TDD/原型优先/文档优先)
4. **emotional**: 情感倾向 (工作压力/兴趣点/成就感来源)

## 对话记录
{conversation}

## 输出要求
返回 JSON 数组，每个元素包含:
- pattern: 模式描述 (简短精确)
- category: 分类 (coding_style / preference / workflow / emotional)
- confidence: 置信度 0.1-0.6 (首次提取不应太高)
- evidence: 从对话中提取的支持证据

如果没有发现明显模式，返回空数组 []。

示例:
[
  {{"pattern": "用户偏好 TypeScript 而非 JavaScript", "category": "coding_style", "confidence": 0.4, "evidence": "用户三次主动选择 TypeScript"}},
  {{"pattern": "用户希望回复简洁直接", "category": "preference", "confidence": 0.3, "evidence": "用户说'简短点'"}}
]"""


async def extract_instincts(
    conversation: list[dict],
    session_id: str = "",
    max_messages: int = 30,
) -> list[Instinct]:
    """从对话历史中提取 Instinct

    Args:
        conversation: 消息列表 [{"role": "user/assistant", "content": "..."}]
        session_id: 当前会话 ID
        max_messages: 最多分析的消息数

    Returns:
        提取到的 Instinct 列表
    """
    if not conversation or len(conversation) < 4:
        return []  # 对话太短，不值得提取

    # 截取最近的消息
    recent = conversation[-max_messages:]
    conv_text = "\n".join(
        f"[{msg.get('role', 'unknown')}]: {msg.get('content', '')[:300]}"
        for msg in recent
    )

    try:
        client = get_llm_client()
        request = LLMRequest(
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(conversation=conv_text),
            }],
            temperature=0.3,
            max_tokens=2048,
            stream=False,
        )
        response = await client.complete(request)
        raw = response.content.strip()

        # 解析 JSON 数组
        if "```json" in raw:
            raw = raw[raw.index("```json")+7:raw.rindex("```")]
        # 找到数组
        start = raw.index("[")
        end = raw.rindex("]") + 1
        patterns = json.loads(raw[start:end])

        instincts = []
        for p in patterns:
            if not isinstance(p, dict) or "pattern" not in p:
                continue
            inst = Instinct(
                id=str(uuid.uuid4()),
                pattern=p["pattern"][:200],
                category=p.get("category", "preference"),
                confidence=max(0.1, min(0.6, float(p.get("confidence", 0.3)))),
                evidence=[p.get("evidence", "")[:200]] if p.get("evidence") else [],
                source_sessions=[session_id] if session_id else [],
            )
            instincts.append(inst)

        logger.info("从会话 %s 中提取了 %d 个 Instinct", session_id[:8] if session_id else "?", len(instincts))
        return instincts

    except Exception as e:
        logger.warning("Instinct 提取失败: %s", e)
        return []
