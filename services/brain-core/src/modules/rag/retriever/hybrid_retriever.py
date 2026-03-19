"""混合检索器 — 向量(Milvus) + BM25(ES) + RRF 融合"""

from dataclasses import dataclass
from typing import List, Dict, Optional

from ..vectorstore.milvus_store import get_milvus_store
from ..indexer.es_indexer import get_es_indexer
from ...llm.embedding.embedding_provider import get_embedding_provider


@dataclass
class RetrievalResult:
    chunk_id: str
    doc_id: str
    content: str
    title: str
    score: float
    source: str
    metadata: dict


class HybridRetriever:
    """融合向量检索（Milvus）+ BM25（ES）+ RRF 排序"""

    def __init__(self, vector_weight: float = 0.6, bm25_weight: float = 0.4, rrf_k: int = 60):
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k

    async def retrieve_vector(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        """仅向量检索"""
        embedder = get_embedding_provider()
        query_vec = await embedder.embed_single(query)
        store = get_milvus_store()
        if not store.available:
            return []

        hits = store.search(query_vec, top_k=top_k)
        return [
            RetrievalResult(
                chunk_id=h["chunk_id"],
                doc_id=h["doc_id"],
                content=h["text"],
                title="",
                score=h["score"],
                source="vector",
                metadata={},
            )
            for h in hits
        ]

    async def retrieve_bm25(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        """仅 BM25 检索"""
        es = get_es_indexer()
        if not es.available:
            return []

        hits = es.search(query, top_k=top_k)
        return [
            RetrievalResult(
                chunk_id=h["chunk_id"],
                doc_id=h["doc_id"],
                content=h["content"],
                title=h.get("title", ""),
                score=h["score"],
                source="bm25",
                metadata={},
            )
            for h in hits
        ]

    async def retrieve(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        """混合检索 + RRF 融合"""
        vector_results = await self.retrieve_vector(query, top_k=top_k * 2)
        bm25_results = await self.retrieve_bm25(query, top_k=top_k * 2)

        if not vector_results and not bm25_results:
            return []
        if not vector_results:
            return bm25_results[:top_k]
        if not bm25_results:
            return vector_results[:top_k]

        # RRF (Reciprocal Rank Fusion)
        scores: Dict[str, float] = {}
        chunk_map: Dict[str, RetrievalResult] = {}

        for rank, r in enumerate(vector_results):
            rrf_score = self.vector_weight / (self.rrf_k + rank + 1)
            scores[r.chunk_id] = scores.get(r.chunk_id, 0) + rrf_score
            chunk_map[r.chunk_id] = r

        for rank, r in enumerate(bm25_results):
            rrf_score = self.bm25_weight / (self.rrf_k + rank + 1)
            scores[r.chunk_id] = scores.get(r.chunk_id, 0) + rrf_score
            if r.chunk_id not in chunk_map:
                chunk_map[r.chunk_id] = r

        # 按 RRF 分数排序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for chunk_id, score in ranked:
            r = chunk_map[chunk_id]
            results.append(RetrievalResult(
                chunk_id=r.chunk_id,
                doc_id=r.doc_id,
                content=r.content,
                title=r.title,
                score=score,
                source="hybrid",
                metadata=r.metadata,
            ))
        return results


# 全局单例
_hybrid_retriever: Optional[HybridRetriever] = None


def get_hybrid_retriever() -> HybridRetriever:
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever
