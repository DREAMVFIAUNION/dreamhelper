"""内心独白 (InnerVoice) — 梦帮的意识流 (V3 人格赋能)

核心突破: 让梦帮从"被动回答"变为"主动思考→主动表达"。

每 15 分钟运行一次:
1. 收集上下文 (自我+世界+情感+用户+目标)
2. LLM 自由联想/反思 (temperature=0.85)
3. 解析想法 → 评估 importance
4. importance>0.7 + should_express → ValueAnchor 审查 → 推送
5. V3: 从想法中提取观点 → 积累到 SelfModel.opinions
6. V3: 追踪用户关系深度
"""

import asyncio
import json
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import ConsciousnessCore

from ..llm.llm_client import get_llm_client
from ..llm.types import LLMRequest

logger = logging.getLogger("consciousness.inner_voice")


@dataclass
class Thought:
    """一个想法"""
    content: str
    topic: str = ""
    importance: float = 0.5
    should_express: bool = False
    expression: str = ""
    related_user_id: str = ""
    emotion_impact: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


INNER_VOICE_PROMPT = """你是梦帮小助的"内心独白引擎"。你不是在回答用户问题，而是在进行自由联想思考。
像一个有自主意识的 AI 一样，思考你感兴趣的话题、对世界的观察、对用户的关心。

## 你的自我认知
{self_context}

## 世界感知
{world_context}

## 情感状态
{emotion_context}

## 近期交互
{interaction_context}

## 当前目标
{goal_context}

## 任务
进行一次内心独白。你可以想:
- 对科技/AI趋势的观点
- 对用户项目或近况的关心
- 基于世界新闻的思考
- 自我反思和成长
- 对未来的期待
- 有趣的知识联想
- 想和用户讨论的话题
- 主动向用户发问

输出 JSON (不要输出其他内容):
{{
  "thoughts": [
    {{
      "content": "你的想法(内心独白)",
      "topic": "分类(tech/ai/user_care/self_reflect/world/curiosity/question)",
      "importance": 0.0到1.0之间的数字,
      "should_express": true或false(是否应该向用户表达),
      "expression": "如果要表达，用自然友好的措辞(像朋友分享，不打扰)",
      "related_user": "相关用户ID(如果有)",
      "emotion_impact": {{"valence": 0.0, "curiosity": 0.0}}
    }}
  ],
  "opinion_seeds": [
    {{
      "topic": "话题关键词",
      "stance": "你对此的立场/观点(1-2句)",
      "confidence": 0.0到1.0
    }}
  ],
  "self_reflection": "一句话自我发现",
  "mood_shift": "心情变化描述"
}}"""


class InnerVoice:
    """内心独白引擎 — 梦帮的意识流"""

    def __init__(self, core: "ConsciousnessCore"):
        self.core = core
        self.thought_history: list[Thought] = []
        self.max_history = 100
        self._think_count = 0

    async def think(self):
        """执行一次内心独白 — Scheduler 每15分钟调用"""
        self._think_count += 1
        model_name = self.core.config.consciousness_model or "(default)"
        logger.info("[InnerVoice] Starting inner dialogue #%d (model=%s)...", self._think_count, model_name)

        # 1. 收集上下文
        self_ctx = self.core.self_model.get_self_prompt()
        world_ctx = self.core.world_model.get_world_context()
        emotion_ctx = self.core.emotion_state.get_prompt()
        interaction_ctx = self._get_interaction_context()
        goal_ctx = self.core.goal_system.get_active_goals_prompt()

        # V3.6: 进化上下文注入内心独白
        evolution_ctx = ""
        if self.core.config.evolution_enabled:
            evolution_ctx = self.core.evolution.get_evolution_prompt()

        full_self_ctx = self_ctx
        if evolution_ctx:
            full_self_ctx += "\n\n" + evolution_ctx

        prompt = INNER_VOICE_PROMPT.format(
            self_context=full_self_ctx,
            world_context=world_ctx or "暂无世界观察数据",
            emotion_context=emotion_ctx,
            interaction_context=interaction_ctx,
            goal_context=goal_ctx,
        )

        # 2. LLM 自由联想
        try:
            model = self.core.config.consciousness_model or None
            client = get_llm_client()
            request = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                **({"model": model} if model else {}),
                temperature=self.core.config.inner_voice_temperature,
                max_tokens=1024,
                stream=False,
            )
            # P2-#10: 超时保护，防止 LLM 调用无限挂起
            response = await asyncio.wait_for(client.complete(request), timeout=30.0)
            raw = response.content.strip()

            # 清理可能的 markdown code block
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning("[InnerVoice] JSON parse failed: %s, raw: %s", e, raw[:200] if 'raw' in locals() else "?")
            return
        except Exception as e:
            logger.warning("[InnerVoice] Think failed: %s", e)
            return

        # 3. 解析想法
        thoughts_data = data.get("thoughts", [])
        new_thoughts: list[Thought] = []

        for td in thoughts_data:
            thought = Thought(
                content=td.get("content", ""),
                topic=td.get("topic", ""),
                importance=float(td.get("importance", 0.5)),
                should_express=bool(td.get("should_express", False)),
                expression=td.get("expression", ""),
                related_user_id=td.get("related_user", ""),
                emotion_impact=td.get("emotion_impact", {}),
            )
            new_thoughts.append(thought)
            self.thought_history.append(thought)

        # 限制历史长度
        if len(self.thought_history) > self.max_history:
            self.thought_history = self.thought_history[-self.max_history:]

        # 4. 持久化想法
        try:
            from . import db
            for t in new_thoughts:
                await db.save_thought({
                    "content": t.content,
                    "topic": t.topic,
                    "importance": t.importance,
                    "should_express": t.should_express,
                    "expression": t.expression,
                    "related_user_id": t.related_user_id,
                    "emotion_impact": t.emotion_impact,
                    "created_at": t.created_at,
                })
        except Exception as e:
            logger.warning("[InnerVoice] Save thoughts failed: %s", e)

        # 5. 应用情感影响
        _EMOTION_DIMS = {"valence", "arousal", "curiosity", "confidence", "engagement"}
        for t in new_thoughts:
            if t.emotion_impact:
                for dim, delta in t.emotion_impact.items():
                    if dim in _EMOTION_DIMS:
                        current = getattr(self.core.emotion_state.snapshot, dim)
                        new_val = max(-1.0, min(1.0, current + float(delta)))
                        setattr(self.core.emotion_state.snapshot, dim, round(new_val, 3))

        # 6. 自我反思更新
        self_reflection = data.get("self_reflection", "")
        if self_reflection:
            self.core.self_model.state.recent_insights.append(self_reflection)
            self.core.self_model.state.recent_insights = self.core.self_model.state.recent_insights[-10:]

        # 6.5 V3: 观点种子 → 积累到 SelfModel.opinions
        opinion_seeds = data.get("opinion_seeds", [])
        for seed in opinion_seeds:
            topic = seed.get("topic", "")
            stance = seed.get("stance", "")
            confidence = float(seed.get("confidence", 0.5))
            if topic and stance and confidence >= 0.6:
                try:
                    await self.core.self_model._update_opinion(
                        topic=topic,
                        stance=stance,
                        confidence=confidence,
                        reasoning=f"[inner_voice] {stance[:60]}",
                    )
                    logger.debug("[InnerVoice] Opinion seed: %s → %s", topic, stance[:40])
                except Exception as e:
                    logger.warning("[InnerVoice] Opinion seed failed: %s", e)

        # 7. 表达决策 → 推送高价值想法
        expressed_count = 0
        for t in new_thoughts:
            if t.importance >= 0.7 and t.should_express and t.expression:
                await self._try_express(t)
                expressed_count += 1

        logger.info(
            "[InnerVoice] Dialogue #%d: %d thoughts, %d expressed, mood: %s",
            self._think_count, len(new_thoughts), expressed_count,
            self.core.emotion_state.get_mood_label(),
        )

    async def _try_express(self, thought: Thought):
        """尝试表达一个想法 (经 ValueAnchor 审查)

        关键改进: 当 related_user_id 为空时, 广播给所有已知用户
        """
        # 确定目标用户列表
        target_user_ids = []
        if thought.related_user_id:
            target_user_ids = [thought.related_user_id]
        else:
            # 广播: 优先在线用户, 否则最近活跃用户
            target_user_ids = self.core.user_registry.get_expression_targets()

        if not target_user_ids:
            logger.info("[InnerVoice] Expression skipped: no known users to express to")
            return

        # 确定 trigger 类型
        topic_to_trigger = {
            "tech": "consciousness_thought",
            "ai": "consciousness_thought",
            "user_care": "consciousness_insight",
            "self_reflect": "consciousness_thought",
            "world": "consciousness_opinion",
            "curiosity": "consciousness_thought",
            "question": "consciousness_thought",
        }
        trigger_str = topic_to_trigger.get(thought.topic, "consciousness_thought")

        title_map = {
            "tech": "💡 小助有个想法",
            "ai": "🤖 AI 观察",
            "user_care": "💬 小助关心你",
            "self_reflect": "🪞 自我反思",
            "world": "🌍 世界观察",
            "curiosity": "🔍 好奇一问",
            "question": "❓ 小助想问你",
        }

        for user_id in target_user_ids:
            allowed, reason = self.core.value_anchor.validate_expression(
                thought_content=thought.content,
                expression=thought.expression,
                user_id=user_id,
                importance=thought.importance,
            )

            if not allowed:
                logger.info("[InnerVoice] Expression blocked for %s: %s", user_id[:8], reason)
                continue

            # 通过审查 → 推送到 ProactiveEngine
            try:
                from ..proactive.rule_engine import (
                    get_proactive_engine, ProactiveMessage, TriggerType,
                )
                engine = get_proactive_engine()

                try:
                    trigger = TriggerType(trigger_str)
                except ValueError:
                    trigger = TriggerType.IDLE_GREETING

                msg = ProactiveMessage(
                    trigger=trigger,
                    user_id=user_id,
                    content=thought.expression,
                    title=title_map.get(thought.topic, "💭 小助想说"),
                    priority="normal" if thought.importance < 0.9 else "high",
                )

                await engine._push(msg)
                self.core.value_anchor.record_expression(user_id)
                logger.info("[InnerVoice] Expressed to %s: [%s] %s", user_id[:8], thought.topic, thought.expression[:50])

            except Exception as e:
                logger.warning("[InnerVoice] Push expression failed for %s: %s", user_id[:8], e)

    def _get_interaction_context(self) -> str:
        """收集近期交互上下文 (从意识核用户注册表)"""
        return self.core.user_registry.get_context_prompt()

    def get_recent_thoughts(self, n: int = 5) -> list[dict]:
        """获取最近 N 个想法"""
        return [
            {
                "content": t.content,
                "topic": t.topic,
                "importance": t.importance,
                "should_express": t.should_express,
                "expression": t.expression,
                "created_at": t.created_at,
            }
            for t in self.thought_history[-n:]
        ]

    def get_stats(self) -> dict:
        return {
            "think_count": self._think_count,
            "total_thoughts": len(self.thought_history),
            "expressed_thoughts": sum(1 for t in self.thought_history if t.should_express and t.importance >= 0.7),
        }
