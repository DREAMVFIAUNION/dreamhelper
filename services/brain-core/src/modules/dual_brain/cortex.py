"""前额叶皮层融合器 — 整合左右脑皮层输出，做出最终决策（GLM-4.7 推理模型）"""

import json
import re
import logging
from enum import Enum
from typing import AsyncGenerator, Optional

from .hemisphere import HemisphereResult
from .brain_config import BrainConfig
from ..llm.llm_client import get_llm_client
from ..llm.types import LLMRequest
from ...common.prompt_guard import wrap_user_input, wrap_ai_output, INJECTION_GUARD

logger = logging.getLogger(__name__)

# 融合 prompt 中每个半球输出的最大字符数（防止 prompt 过大导致超时）
MAX_HEMISPHERE_CHARS = 3000


class FusionStrategy(str, Enum):
    """融合策略"""
    COMPETE = "compete"           # 竞争择优: 选更好的一个
    COMPLEMENT = "complement"     # 互补拼接: 取各自精华合并
    DEBATE = "debate"             # 辩论共识: 让第三方裁判融合
    WEIGHTED = "weighted"         # 加权混合: 按权重合成


class Cortex:
    """
    皮层融合器 — 双脑输出的最终仲裁者

    类比人脑前额叶皮层: 整合来自不同脑区的信息，做出最终决策。
    """

    def __init__(self, config: BrainConfig):
        self.config = config

    @staticmethod
    def _truncate(text: str, max_chars: int = MAX_HEMISPHERE_CHARS) -> str:
        """截断过长的半球输出，避免融合 prompt 过大"""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + f"\n\n[... 内容已截断，原文共 {len(text)} 字 ...]"

    async def fuse(
        self,
        left_result: HemisphereResult,
        right_result: HemisphereResult,
        left_weight: float,
        right_weight: float,
        strategy: FusionStrategy,
        query: str,
    ) -> tuple[str, float]:
        """
        融合双脑输出

        Returns: (融合后的内容, 置信度 0-1)
        """
        match strategy:
            case FusionStrategy.COMPETE:
                return await self._compete(left_result, right_result, query)
            case FusionStrategy.COMPLEMENT:
                return await self._complement(left_result, right_result, query)
            case FusionStrategy.DEBATE:
                return await self._debate(left_result, right_result, query)
            case FusionStrategy.WEIGHTED:
                return await self._weighted(left_result, right_result, left_weight, right_weight, query)
            case _:
                return await self._complement(left_result, right_result, query)

    async def _compete(
        self, left: HemisphereResult, right: HemisphereResult, query: str
    ) -> tuple[str, float]:
        """
        策略1: 竞争择优

        让一个裁判 LLM 评估两个回答，选出更好的那个。
        适用: 事实问答、代码生成（有明确对错）
        """
        left_text = self._truncate(left.content)
        right_text = self._truncate(right.content)

        judge_prompt = f"""你是一个AI回答质量评估器。用户的问题是:
{wrap_user_input(query, max_len=1000)}

以下是两个AI助手的回答:

[回答A — 逻辑分析型]
{wrap_ai_output(left_text, 'answer_a')}

[回答B — 创意洞察型]
{wrap_ai_output(right_text, 'answer_b')}

请评估哪个回答更好。考虑: 准确性、完整性、实用性、清晰度。
输出格式（严格遵循）:
WINNER: A 或 B
REASON: 一句话说明原因
CONFIDENCE: 0.0-1.0"""

        try:
            client = get_llm_client()
            response = await client.complete(LLMRequest(
                messages=[{"role": "user", "content": judge_prompt}],
                model=self.config.judge_model,
                temperature=0.1,
                max_tokens=256,
                stream=False,
            ))

            result_text = response.content
            if "WINNER: A" in result_text:
                confidence = self._extract_confidence(result_text)
                return left.content, confidence
            else:
                confidence = self._extract_confidence(result_text)
                return right.content, confidence
        except Exception as e:
            logger.warning("融合(compete)失败，降级为左脑输出: %s", e)
            return left.content, 0.5

    async def _complement(
        self, left: HemisphereResult, right: HemisphereResult, query: str
    ) -> tuple[str, float]:
        """
        策略2: 互补拼接

        提取两个回答的各自优势，合成一个更完整的回答。
        适用: 分析、方案设计（没有绝对对错，各有千秋）
        """
        left_text = self._truncate(left.content)
        right_text = self._truncate(right.content)

        fusion_prompt = f"""你是一个AI回答融合专家。用户问题是:
{wrap_user_input(query, max_len=1000)}

以下是两个维度的分析:

[逻辑分析维度]
{wrap_ai_output(left_text, 'logic_analysis')}

[创意洞察维度]
{wrap_ai_output(right_text, 'creative_insight')}

请将两个维度的精华融合为一个更完整、更有深度的回答。
要求:
- 保留逻辑分析的结构性和准确性
- 融入创意洞察的独特视角和延伸思考
- 去除重复内容，保持行文流畅
- 不要提及"两个维度"或"融合"，像是一个完整的思考
- 用中文回答"""

        try:
            client = get_llm_client()
            response = await client.complete(LLMRequest(
                messages=[{"role": "user", "content": fusion_prompt}],
                model=self.config.fusion_model,
                temperature=0.5,
                max_tokens=4096,
                stream=False,
            ))
            return response.content, 0.85
        except Exception as e:
            logger.warning("融合(complement)失败，降级为左脑输出: %s", e)
            return left.content, 0.5

    async def _debate(
        self, left: HemisphereResult, right: HemisphereResult, query: str
    ) -> tuple[str, float]:
        """
        策略3: 辩论共识

        模拟两个AI之间的辩论，找到共识点。
        适用: 争议性话题、复杂决策
        """
        left_text = self._truncate(left.content)
        right_text = self._truncate(right.content)

        debate_prompt = f"""你是一个辩论仲裁者。用户问题:
{wrap_user_input(query, max_len=1000)}

[正方 (逻辑派) 观点]
{wrap_ai_output(left_text, 'logic_side')}

[反方 (创意派) 观点]
{wrap_ai_output(right_text, 'creative_side')}

请作为仲裁者:
1. 指出双方的共识点
2. 分析双方的分歧所在
3. 给出你的综合判断
4. 输出一个融合了双方精华的最终回答

最终回答应该自然流畅，不提及辩论过程。"""

        try:
            client = get_llm_client()
            response = await client.complete(LLMRequest(
                messages=[{"role": "user", "content": debate_prompt}],
                model=self.config.fusion_model,
                temperature=0.5,
                max_tokens=4096,
                stream=False,
            ))
            return response.content, 0.9
        except Exception as e:
            logger.warning("融合(debate)失败，降级为左脑输出: %s", e)
            return left.content, 0.5

    async def _weighted(
        self, left: HemisphereResult, right: HemisphereResult,
        left_w: float, right_w: float, query: str
    ) -> tuple[str, float]:
        """
        策略4: 加权混合

        按权重决定以哪个回答为主，另一个为补充。
        适用: 已明确知道该侧重哪个半球的场景
        """
        if left_w >= 0.7:
            primary, secondary = left, right
            primary_label, secondary_label = "主要", "补充"
        elif right_w >= 0.7:
            primary, secondary = right, left
            primary_label, secondary_label = "主要", "补充"
        else:
            # 接近平衡，走互补策略
            return await self._complement(left, right, query)

        primary_text = self._truncate(primary.content)
        secondary_text = self._truncate(secondary.content)

        weighted_prompt = f"""以下是对用户问题"{query}"的两个回答:

[{primary_label}回答 — 权重{max(left_w, right_w):.0%}]
{primary_text}

[{secondary_label}参考 — 权重{min(left_w, right_w):.0%}]
{secondary_text}

请以主要回答为基础，适当吸收补充参考中的有价值信息，输出优化后的最终回答。
不要提及权重或融合过程。"""

        try:
            client = get_llm_client()
            response = await client.complete(LLMRequest(
                messages=[{"role": "user", "content": weighted_prompt}],
                model=self.config.fusion_model,
                temperature=0.4,
                max_tokens=4096,
                stream=False,
            ))
            return response.content, max(left_w, right_w)
        except Exception as e:
            logger.warning("融合(weighted)失败，降级为主半球输出: %s", e)
            return primary.content, 0.5

    def _extract_confidence(self, text: str) -> float:
        """从裁判输出中提取置信度"""
        match = re.search(r'CONFIDENCE:\s*([\d.]+)', text)
        if match:
            return min(1.0, max(0.0, float(match.group(1))))
        return 0.7

    # ════════════════════════════════════════════════════
    # 流式融合 — 融合结果逐字输出，减少用户等待
    # ════════════════════════════════════════════════════

    async def fuse_stream(
        self,
        left_result: HemisphereResult,
        right_result: HemisphereResult,
        left_weight: float,
        right_weight: float,
        strategy: FusionStrategy,
        query: str,
        extra_context: str = "",
    ) -> AsyncGenerator[dict, None]:
        """
        流式融合双脑输出 — 逐字 yield {"type":"chunk","content":"..."}

        compete 策略不需要流式（直接选择胜者），降级为非流式。
        complement / debate / weighted 策略均支持流式输出。
        """
        if strategy == FusionStrategy.COMPETE:
            content, confidence = await self._compete(left_result, right_result, query)
            # 分块流式输出（模拟流式体验）
            chunk_size = 30
            for i in range(0, len(content), chunk_size):
                yield {"type": "chunk", "content": content[i:i+chunk_size]}
            yield {"type": "fusion_meta", "confidence": confidence}
            return

        prompt = self._build_fusion_prompt(left_result, right_result, left_weight, right_weight, strategy, query, extra_context)
        if prompt is None:
            content, confidence = await self.fuse(left_result, right_result, left_weight, right_weight, strategy, query)
            yield {"type": "chunk", "content": content}
            yield {"type": "fusion_meta", "confidence": confidence}
            return

        confidence_map = {
            FusionStrategy.COMPLEMENT: 0.85,
            FusionStrategy.DEBATE: 0.9,
            FusionStrategy.WEIGHTED: max(left_weight, right_weight),
        }
        confidence = confidence_map.get(strategy, 0.8)

        try:
            client = get_llm_client()
            request = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                model=self.config.fusion_model,
                temperature=0.5,
                max_tokens=4096,
                stream=True,
            )
            async for chunk_json in client.stream(request):
                try:
                    data = json.loads(chunk_json)
                    if not isinstance(data, dict):
                        continue
                    if data.get("type") == "chunk" and data.get("content"):
                        yield {"type": "chunk", "content": data["content"]}
                except (json.JSONDecodeError, AttributeError, TypeError):
                    continue
            yield {"type": "fusion_meta", "confidence": confidence}
        except Exception as e:
            logger.exception("流式融合失败，降级为左脑输出")
            yield {"type": "chunk", "content": left_result.content}
            yield {"type": "fusion_meta", "confidence": 0.5}

    def _build_fusion_prompt(
        self,
        left: HemisphereResult,
        right: HemisphereResult,
        left_w: float,
        right_w: float,
        strategy: FusionStrategy,
        query: str,
        extra_context: str = "",
    ) -> Optional[str]:
        """为流式融合构建 prompt（与非流式共享同一套 prompt 模板）"""
        left_text = self._truncate(left.content)
        right_text = self._truncate(right.content)
        # MCP 思维链 / 脑干指令 / 小脑技术基准 增强上下文
        context_block = f"\n\n[深度分析参考]\n{extra_context}" if extra_context else ""
        has_cerebellum = "小脑技术基准" in extra_context if extra_context else False

        if strategy == FusionStrategy.COMPLEMENT:
            return f"""你是一个AI回答融合专家。用户问题是:
{wrap_user_input(query, max_len=1000)}

以下是两个维度的分析:

[逻辑分析维度]
{wrap_ai_output(left_text, 'logic_analysis')}

[创意洞察维度]
{wrap_ai_output(right_text, 'creative_insight')}{context_block}

请将两个维度的精华融合为一个更完整、更有深度的回答。
要求:
- 保留逻辑分析的结构性和准确性
- 融入创意洞察的独特视角和延伸思考
- 如有深度分析参考，融入其结构化思考
- 如有小脑技术基准（代码），优先采信其代码的正确性和可运行性
- 去除重复内容，保持行文流畅
- 不要提及"两个维度"或"融合"，像是一个完整的思考
- 用中文回答"""

        if strategy == FusionStrategy.DEBATE:
            return f"""你是一个辩论仲裁者。用户问题:
{wrap_user_input(query, max_len=1000)}

[正方 (逻辑派) 观点]
{wrap_ai_output(left_text, 'logic_side')}

[反方 (创意派) 观点]
{wrap_ai_output(right_text, 'creative_side')}{context_block}

请作为仲裁者:
1. 指出双方的共识点
2. 分析双方的分歧所在
3. 给出你的综合判断
4. 输出一个融合了双方精华的最终回答

最终回答应该自然流畅，不提及辩论过程。"""

        if strategy == FusionStrategy.WEIGHTED:
            if left_w >= 0.7:
                primary_text, secondary_text = left_text, right_text
                primary_label, secondary_label = "主要", "补充"
                max_w, min_w = left_w, right_w
            elif right_w >= 0.7:
                primary_text, secondary_text = right_text, left_text
                primary_label, secondary_label = "主要", "补充"
                max_w, min_w = right_w, left_w
            else:
                return self._build_fusion_prompt(left, right, left_w, right_w, FusionStrategy.COMPLEMENT, query)

            return f"""以下是对用户问题的两个回答:
{wrap_user_input(query, max_len=1000)}

[{primary_label}回答 — 权重{max_w:.0%}]
{wrap_ai_output(primary_text, 'primary')}

[{secondary_label}参考 — 权重{min_w:.0%}]
{wrap_ai_output(secondary_text, 'secondary')}{context_block}

请以主要回答为基础，适当吸收补充参考中的有价值信息，输出优化后的最终回答。
不要提及权重或融合过程。"""

        return None
