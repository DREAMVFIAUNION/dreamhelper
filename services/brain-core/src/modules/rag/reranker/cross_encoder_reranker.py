"""Cross-Encoder 重排序 — 双策略（Phase 11）

策略优先级:
1. sentence-transformers Cross-Encoder 本地模型（精度高、速度快）
2. LLM 打分重排序（零额外依赖、使用现有 LLM Client）
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import CrossEncoder as _CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False


@dataclass
class RerankResult:
    content: str
    score: float
    original_rank: int


# 全局模型实例（懒加载）
_model: Optional[object] = None
_model_name: str = "BAAI/bge-reranker-v2-m3"


def _get_model():
    """懒加载 Cross-Encoder 模型"""
    global _model
    if _model is None and HAS_CROSS_ENCODER:
        logger.info(f"Loading Cross-Encoder model: {_model_name}")
        _model = _CrossEncoder(_model_name, max_length=512)
        logger.info("Cross-Encoder model loaded")
    return _model


class CrossEncoderReranker:
    """使用 Cross-Encoder 模型或 LLM 对检索结果重排序"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        global _model_name
        _model_name = model_name
        self.model_name = model_name

    async def rerank(
        self, query: str, documents: List[str], top_k: int = 5
    ) -> List[RerankResult]:
        """重排序: Cross-Encoder → LLM fallback"""
        if not documents:
            return []

        # 策略 1: 本地 Cross-Encoder
        if HAS_CROSS_ENCODER:
            return await self._rerank_cross_encoder(query, documents, top_k)

        # 策略 2: LLM 打分
        return await self._rerank_llm(query, documents, top_k)

    async def _rerank_cross_encoder(
        self, query: str, documents: List[str], top_k: int
    ) -> List[RerankResult]:
        """使用 Cross-Encoder 模型打分"""
        model = _get_model()
        if model is None:
            return await self._rerank_llm(query, documents, top_k)

        try:
            pairs = [(query, doc) for doc in documents]
            scores = model.predict(pairs)  # type: ignore

            results = []
            for i, (doc, score) in enumerate(zip(documents, scores)):
                results.append(RerankResult(
                    content=doc,
                    score=float(score),
                    original_rank=i,
                ))

            results.sort(key=lambda r: r.score, reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.warning(f"Cross-Encoder rerank failed: {e}")
            return await self._rerank_llm(query, documents, top_k)

    async def _rerank_llm(
        self, query: str, documents: List[str], top_k: int
    ) -> List[RerankResult]:
        """使用 LLM 逐对打分（0-10 分），然后按分数排序"""
        try:
            from ...llm.llm_client import get_llm_client
            llm = get_llm_client()
        except Exception:
            # LLM 也不可用，降级为原始顺序 + 衰减分数
            return [
                RerankResult(content=doc, score=1.0 / (i + 1), original_rank=i)
                for i, doc in enumerate(documents[:top_k])
            ]

        # 批量构建打分请求（单次 LLM 调用）
        doc_list = "\n".join(
            f"[文档{i+1}] {doc[:300]}"
            for i, doc in enumerate(documents)
        )

        prompt = f"""你是一个相关性评分器。给定一个查询和多个候选文档，请为每个文档的相关性打分（0-10分，10=完全相关）。

查询: {query}

候选文档:
{doc_list}

请严格按以下 JSON 格式返回每个文档的分数:
[{{"doc": 1, "score": 8}}, {{"doc": 2, "score": 3}}, ...]

只返回 JSON 数组。"""

        try:
            response = await llm.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=512,
            )

            scores = self._parse_scores(response, len(documents))

            results = []
            for i, doc in enumerate(documents):
                results.append(RerankResult(
                    content=doc,
                    score=scores.get(i, 0.0),
                    original_rank=i,
                ))

            results.sort(key=lambda r: r.score, reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.warning(f"LLM rerank failed: {e}")
            return [
                RerankResult(content=doc, score=1.0 / (i + 1), original_rank=i)
                for i, doc in enumerate(documents[:top_k])
            ]

    def _parse_scores(self, response: str, n: int) -> dict[int, float]:
        """从 LLM 响应中解析文档分数"""
        import json
        import re

        scores: dict[int, float] = {}
        json_match = re.search(r'\[[\s\S]*?\]', response)
        if json_match:
            try:
                data = json.loads(json_match.group())
                for item in data:
                    doc_idx = int(item.get("doc", 0)) - 1  # 1-indexed → 0-indexed
                    score = float(item.get("score", 0))
                    if 0 <= doc_idx < n:
                        scores[doc_idx] = score / 10.0  # 归一化到 0-1
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        return scores


def get_reranker_status() -> dict:
    """获取 Reranker 状态"""
    return {
        "cross_encoder_available": HAS_CROSS_ENCODER,
        "model": _model_name if HAS_CROSS_ENCODER else None,
        "model_loaded": _model is not None,
        "fallback": "llm-scoring",
    }
