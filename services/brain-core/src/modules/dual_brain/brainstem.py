"""脑干 (Brainstem) — 中枢神经系统，管理整个三脑神经元体系

职责:
1. PRE-ANALYZE  — 深度意图分析、策略选择、半球参数调优
2. POST-REVIEW  — 融合质量评估、元认知反思、输出增强

使用 GLM-5 744B MoE 推理模型 via NVIDIA NIM（128K 上下文 + 思维链推理）
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from .brain_config import BrainConfig
from ..llm.llm_client import get_llm_client
from ..llm.types import LLMRequest
from ...common.prompt_guard import wrap_user_input, INJECTION_GUARD

logger = logging.getLogger(__name__)


@dataclass
class BrainstemDirective:
    """脑干前处理指令 — 指导双脑如何协作"""
    task_complexity: str = "medium"       # simple / medium / complex / expert
    recommended_strategy: str = "complement"  # compete / complement / debate / weighted
    left_weight: float = 0.5
    right_weight: float = 0.5
    skip_dual_brain: bool = False         # True = 简单问题跳过双脑直接单脑
    focus_instructions: str = ""          # 给半球的额外聚焦指令
    reasoning_trace: str = ""             # GLM 推理过程（思维链）
    enhanced_query: str = ""              # 优化后的 query
    latency_ms: float = 0.0


# ── 脑干前处理 Prompt ──────────────────────────────────

PRE_ANALYZE_PROMPT = """你是三脑协作系统的**脑干/中枢神经**。你的职责是分析用户问题，为左脑（逻辑分析）和右脑（创意洞察）制定最优协作策略。

请分析以下用户问题，输出一个 JSON 对象（不要输出其他内容）：

```json
{{
  "task_complexity": "simple|medium|complex|expert",
  "recommended_strategy": "compete|complement|debate|weighted",
  "left_weight": 0.0-1.0,
  "right_weight": 0.0-1.0,
  "skip_dual_brain": true|false,
  "focus_instructions": "给两个半球的聚焦指令，告诉它们重点关注什么",
  "enhanced_query": "优化后的问题表述（如果原问题不够清晰）"
}}
```

策略说明：
- **compete**: 让两脑竞争，选更好的。适合有明确正确答案的问题（数学/代码/事实）
- **complement**: 互补拼接，取各自精华。适合需要多角度的问题（分析/写作）
- **debate**: 辩论共识，深度讨论分歧。适合复杂/争议性问题
- **weighted**: 加权混合，按权重合成。适合日常对话/创意任务

权重规则：
- 代码/数学/事实 → 左脑权重高 (0.6-0.8)
- 写作/创意/情感 → 右脑权重高 (0.6-0.8)
- 复杂分析 → 均衡 (0.5/0.5)
- 简单问候 → skip_dual_brain=true

用户问题: {query}"""


# ── 脑干后处理 Prompt ──────────────────────────────────

POST_REVIEW_PROMPT = """你是三脑协作系统的**脑干/中枢神经**，负责最终质量把关。

以下是三脑协作的结果：
- **用户原始问题**: {query}
- **左脑输出** (逻辑分析，模型: GLM-5): {left_summary}
- **右脑输出** (创意洞察，模型: Qwen-3.5): {right_summary}
- **皮层融合结果**: {fused_content}

请评估融合结果的质量，判断是否需要增强。输出 JSON：

```json
{{
  "quality_score": 1-10,
  "needs_enhancement": true|false,
  "issues": ["遗漏点1", "遗漏点2"],
  "enhancement": "如果需要增强，写出增强后的完整回答。如果不需要，留空"
}}
```

评估标准：
- 完整性：是否回答了用户所有问题
- 准确性：是否有矛盾或错误
- 深度：是否足够深入（不能太浅显）
- 可读性：结构是否清晰

只有当 quality_score < 7 时才需要增强。大多数情况下融合结果已经很好，不需要修改。"""


class Brainstem:
    """
    脑干 — 仿生大脑的基础反射与快速响应系统

    如同人类脑干控制呼吸、心跳等自主功能，不经大脑皮层的反射弧，
    Brainstem 负责：
    - 快速响应：简单查询不经大脑皮层直接回答（反射弧）
    - 深度分析：复杂查询的意图解析与策略制定（PRE）
    - 质量控制：融合后的元认知反思与输出增强（POST）
    """

    def __init__(self, config: BrainConfig):
        self.config = config
        self.model = config.brainstem_model
        self.response_model = config.brainstem_response_model or config.brainstem_model
        self.enabled = config.brainstem_enabled

    async def quick_respond_stream(
        self,
        query: str,
        system_prompt: str = "",
        history: list[dict] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """
        脑干快速响应 — 简单查询的反射弧路径

        不经过大脑皮层（左右脑），直接用 MiniMax 快速回答。
        适用：简单问候、闲聊、单句事实问答、简短定义。
        """
        history = history or []
        start = time.time()
        client = get_llm_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        messages.append({"role": "user", "content": query})

        try:
            request = LLMRequest(
                messages=messages,
                model=self.response_model,
                temperature=0.6,
                max_tokens=2048,
                stream=True,
            )
            async for chunk_json in client.stream(request):
                try:
                    data = json.loads(chunk_json)
                    if not isinstance(data, dict):
                        continue
                    if data.get("type") == "chunk" and data.get("content"):
                        yield {"type": "chunk", "content": data["content"]}
                    elif data.get("type") == "done":
                        break
                except json.JSONDecodeError:
                    continue

            latency = (time.time() - start) * 1000
            logger.info("脑干快速响应完成: %.0fms", latency)
            yield {"type": "brainstem_done", "latency_ms": round(latency, 1)}

        except Exception as e:
            logger.error("脑干快速响应失败: %s", e, exc_info=True)
            yield {"type": "error", "content": "处理请求时遇到问题，请稍后重试"}

    async def pre_analyze(self, query: str, history: list[dict] | None = None) -> BrainstemDirective:
        """
        前处理：深度分析用户意图 → 返回协作指令

        使用 GLM-5 推理能力分析问题复杂度、选择最优策略、
        调整半球权重，并生成聚焦指令。
        """
        if not self.enabled:
            return BrainstemDirective()

        start = time.time()
        client = get_llm_client()

        prompt = PRE_ANALYZE_PROMPT.format(query=wrap_user_input(query, max_len=3000))

        request = LLMRequest(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            temperature=0.3,
            max_tokens=4096,
            stream=False,
        )

        try:
            response = await client.complete(request)
            latency = (time.time() - start) * 1000

            # 提取推理过程（GLM-4.7 reasoning_content）
            reasoning_trace = getattr(response, 'thinking', '') or ''

            # 解析 JSON 指令
            directive = self._parse_directive(response.content, reasoning_trace)
            directive.latency_ms = latency

            logger.info(
                "脑干分析完成: complexity=%s strategy=%s weights=%.1f/%.1f skip=%s (%.0fms)",
                directive.task_complexity, directive.recommended_strategy,
                directive.left_weight, directive.right_weight,
                directive.skip_dual_brain, latency,
            )

            return directive

        except Exception as e:
            logger.warning("脑干前处理失败，使用默认指令: %s", e)
            return BrainstemDirective(
                latency_ms=(time.time() - start) * 1000,
                reasoning_trace=f"[分析失败: {e}]",
            )

    async def post_review_stream(
        self,
        fused_content: str,
        left_raw: str,
        right_raw: str,
        query: str,
        task_complexity: str = "medium",
    ) -> AsyncGenerator[dict, None]:
        """
        后处理：质量评估 + 增强（流式输出）

        仅在复杂/专家级任务中触发，简单任务跳过以节省 token。
        """
        # 简单/中等任务跳过后处理
        if not self.enabled or task_complexity in ("simple", "medium"):
            yield {"type": "review_skip", "reason": "task_complexity too low for review"}
            return

        client = get_llm_client()

        # 截断避免 prompt 过大
        left_summary = left_raw[:1500] if left_raw else "[无]"
        right_summary = right_raw[:1500] if right_raw else "[无]"
        fused_truncated = fused_content[:3000]

        prompt = POST_REVIEW_PROMPT.format(
            query=query,
            left_summary=left_summary,
            right_summary=right_summary,
            fused_content=fused_truncated,
        )

        request = LLMRequest(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            temperature=0.3,
            max_tokens=8192,
            stream=False,
        )

        try:
            response = await client.complete(request)
            review = self._parse_review(response.content)

            yield {
                "type": "review_result",
                "quality_score": review.get("quality_score", 8),
                "needs_enhancement": review.get("needs_enhancement", False),
                "issues": review.get("issues", []),
            }

            # 如果需要增强，流式输出增强内容
            if review.get("needs_enhancement") and review.get("enhancement"):
                enhancement = review["enhancement"]
                # 分块输出增强内容
                chunk_size = 20
                for i in range(0, len(enhancement), chunk_size):
                    yield {"type": "enhancement_chunk", "content": enhancement[i:i+chunk_size]}

        except Exception as e:
            logger.warning("脑干后处理失败: %s", e)
            yield {"type": "review_skip", "reason": f"review failed: {e}"}

    def _parse_directive(self, content: str, reasoning_trace: str = "") -> BrainstemDirective:
        """解析 GLM 返回的 JSON 指令"""
        directive = BrainstemDirective(reasoning_trace=reasoning_trace)

        try:
            # 提取 JSON（可能包裹在 ```json ``` 中）
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)

            directive.task_complexity = data.get("task_complexity", "medium")
            directive.recommended_strategy = data.get("recommended_strategy", "complement")
            directive.left_weight = float(data.get("left_weight", 0.5))
            directive.right_weight = float(data.get("right_weight", 0.5))
            directive.skip_dual_brain = bool(data.get("skip_dual_brain", False))
            directive.focus_instructions = data.get("focus_instructions", "")
            directive.enhanced_query = data.get("enhanced_query", "")

            # 归一化权重
            total = directive.left_weight + directive.right_weight
            if total > 0:
                directive.left_weight /= total
                directive.right_weight /= total

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("脑干指令解析失败: %s, content: %s", e, content[:200])

        return directive

    def _parse_review(self, content: str) -> dict:
        """解析后处理评审 JSON"""
        try:
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            logger.warning("脑干评审解析失败: %s", content[:200])
            return {"quality_score": 8, "needs_enhancement": False, "issues": []}
