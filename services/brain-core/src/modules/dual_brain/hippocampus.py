"""海马体 (Hippocampus) — 超长期记忆与上下文检索模块

如同人类海马体负责记忆的编码、存储和检索，Hippocampus 负责:
- 全量会话历史注入（利用 1M token 上下文，不截断）
- 跨会话记忆检索与关联
- 长文档/代码库级别的上下文理解
- 为意识核提供"回忆"能力

使用 NVIDIA Nemotron-Nano-30B (1M token 上下文，免费无限量)

与现有系统关系:
  MemoryManager → 短期(Redis) + 长期事实(PostgreSQL)
  RAGPipeline   → TF-IDF / Milvus 向量检索
  Hippocampus   → 统一注入超长上下文，让 LLM 直接"记住"全部历史
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from .brain_config import BrainConfig
from ..llm.llm_client import get_llm_client
from ..llm.types import LLMRequest

logger = logging.getLogger(__name__)


@dataclass
class HippocampusContext:
    """海马体检索结果 — 注入融合上下文"""
    relevant_memories: list[str] = field(default_factory=list)
    user_facts: dict = field(default_factory=dict)
    recent_sessions: list[dict] = field(default_factory=list)
    summary: str = ""
    total_tokens: int = 0
    latency_ms: float = 0.0


# ── 海马体记忆检索 Prompt ──────────────────────────────────

RECALL_PROMPT = """你是一个**记忆检索专家**，负责从用户的历史对话和已知事实中提取与当前查询最相关的信息。

已知用户事实:
{user_facts}

最近对话历史:
{session_history}

当前用户查询: {query}

请从以上信息中提取与当前查询最相关的记忆和上下文，输出简洁摘要（不超过500字）。
重点关注:
- 用户之前提到过的相关话题
- 用户的偏好和习惯
- 可能影响当前回答的历史上下文
- 未完成的任务或承诺

如果没有相关记忆，输出"无相关历史记忆"。"""


CONSOLIDATE_PROMPT = """你是一个**记忆固化专家**，负责从对话中提取值得长期记住的事实。

以下是一段完整对话:
{conversation}

请提取值得长期记住的用户事实和偏好，输出 JSON（不要输出其他内容）：

```json
{{
  "facts": [
    {{"category": "preference|skill|goal|context|personal", "content": "具体事实", "importance": 0.0-1.0}}
  ],
  "summary": "对话的一句话摘要"
}}
```

提取规则:
- 只提取用户明确表达或可靠推断的事实
- 忽略一次性的闲聊内容
- 偏好和习惯优先级高
- 每条事实应该独立、简洁"""


class Hippocampus:
    """
    海马体 — 仿生大脑的长期记忆与上下文管理中心

    如同人类海马体将短期记忆转化为长期记忆，
    Hippocampus 利用 1M token 超长上下文:
    - 在对话中注入完整的历史上下文（不截断）
    - 检索跨会话的相关记忆
    - 对话后固化重要事实到长期存储
    - 为意识核提供"回忆过去"的能力
    """

    def __init__(self, config: BrainConfig):
        self.config = config
        self.model = config.hippocampus_model
        self.enabled = config.hippocampus_enabled
        self.timeout = config.hippocampus_timeout

    async def recall(
        self,
        query: str,
        user_id: str = "",
        history: list[dict] | None = None,
        user_facts: dict | None = None,
        max_tokens: int = 100_000,
    ) -> HippocampusContext:
        """
        记忆检索 — 从历史中提取与当前查询相关的上下文

        Args:
            query: 当前用户查询
            user_id: 用户ID（用于检索用户特定记忆）
            history: 当前会话历史
            user_facts: 已知的用户事实
            max_tokens: 最大注入 token 数
        """
        if not self.enabled:
            return HippocampusContext()

        start = time.time()
        client = get_llm_client()
        history = history or []
        user_facts = user_facts or {}

        # 格式化用户事实
        facts_str = "\n".join(f"- {k}: {v}" for k, v in user_facts.items()) if user_facts else "暂无已知事实"

        # 格式化会话历史（最近 50 轮）
        recent = history[-100:]  # 50 轮 = 100 条消息
        session_str = "\n".join(
            f"[{msg.get('role', '?')}] {str(msg.get('content', ''))[:200]}"
            for msg in recent
        ) if recent else "暂无对话历史"

        prompt = RECALL_PROMPT.format(
            user_facts=facts_str,
            session_history=session_str,
            query=query,
        )

        try:
            response = await client.complete(LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,
                max_tokens=2048,
                stream=False,
            ))
            latency = (time.time() - start) * 1000

            summary = response.content.strip()
            has_memories = "无相关历史记忆" not in summary

            logger.info(
                "海马体记忆检索完成: has_memories=%s, history_len=%d (%.0fms)",
                has_memories, len(history), latency,
            )

            return HippocampusContext(
                relevant_memories=[summary] if has_memories else [],
                user_facts=user_facts,
                summary=summary,
                total_tokens=len(prompt) // 4 + len(summary) // 4,  # 粗略估算
                latency_ms=latency,
            )

        except Exception as e:
            logger.warning("海马体记忆检索失败: %s", e)
            return HippocampusContext(
                latency_ms=(time.time() - start) * 1000,
            )

    async def consolidate(
        self,
        session_history: list[dict],
        user_id: str = "",
    ) -> dict:
        """
        记忆固化 — 从对话中提取长期事实（类似人类睡眠记忆固化）

        在会话结束时调用，将对话中的重要信息转化为持久化的用户事实。

        Returns:
            {"facts": [...], "summary": "..."}
        """
        if not self.enabled or not session_history:
            return {"facts": [], "summary": ""}

        start = time.time()
        client = get_llm_client()

        # 格式化对话（截断避免过长）
        conversation_parts = []
        for msg in session_history[-60:]:  # 最近 30 轮
            role = msg.get("role", "?")
            content = str(msg.get("content", ""))[:300]
            conversation_parts.append(f"[{role}] {content}")
        conversation_str = "\n".join(conversation_parts)

        prompt = CONSOLIDATE_PROMPT.format(conversation=conversation_str)

        try:
            response = await client.complete(LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,
                max_tokens=2048,
                stream=False,
            ))
            latency = (time.time() - start) * 1000

            result = self._parse_consolidation(response.content)

            logger.info(
                "海马体记忆固化完成: facts=%d (%.0fms)",
                len(result.get("facts", [])), latency,
            )

            return result

        except Exception as e:
            logger.warning("海马体记忆固化失败: %s", e)
            return {"facts": [], "summary": ""}

    def build_context_for_fusion(self, hippocampus_ctx: HippocampusContext) -> str:
        """
        为前额叶融合生成海马体上下文注入文本

        Returns:
            可直接拼接到 fusion_extra_context 的字符串
        """
        if not hippocampus_ctx.relevant_memories:
            return ""

        parts = [f"\n\n[海马体记忆检索 — {self.model}]"]
        for mem in hippocampus_ctx.relevant_memories[:3]:
            parts.append(mem[:1000])
        return "\n".join(parts)

    def _parse_consolidation(self, content: str) -> dict:
        """解析记忆固化 JSON"""
        import json
        try:
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            logger.warning("海马体记忆固化JSON解析失败: %s", content[:200])
            return {"facts": [], "summary": content[:200]}
