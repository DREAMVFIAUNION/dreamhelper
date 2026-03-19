"""Cross-Encoder Reranker 测试"""

import pytest
from src.modules.rag.reranker.cross_encoder_reranker import (
    CrossEncoderReranker,
    RerankResult,
    get_reranker_status,
)


def test_rerank_result_dataclass():
    r = RerankResult(content="hello", score=0.95, original_rank=0)
    assert r.content == "hello"
    assert r.score == 0.95
    assert r.original_rank == 0


def test_reranker_status():
    status = get_reranker_status()
    assert "cross_encoder_available" in status
    assert "fallback" in status
    assert status["fallback"] == "llm-scoring"


@pytest.mark.asyncio
async def test_rerank_empty_documents():
    reranker = CrossEncoderReranker()
    results = await reranker.rerank("test query", [], top_k=3)
    assert results == []


@pytest.mark.asyncio
async def test_rerank_single_document():
    """单个文档不触发 reranker，直接返回"""
    reranker = CrossEncoderReranker()
    docs = ["这是一个测试文档"]
    results = await reranker.rerank("测试", docs, top_k=1)
    # 单文档应该直接返回（LLM不可用时降级为顺序分数）
    assert len(results) >= 1
    assert results[0].content == "这是一个测试文档"


@pytest.mark.asyncio
async def test_rerank_fallback_scores():
    """无 LLM/Cross-Encoder 时降级为衰减分数"""
    reranker = CrossEncoderReranker()
    docs = ["文档A关于Python", "文档B关于Java", "文档C关于Rust"]
    results = await reranker.rerank("Python编程", docs, top_k=2)
    # 降级模式：应返回 top_k 个结果
    assert len(results) <= 2
    for r in results:
        assert isinstance(r.score, float)
        assert r.original_rank in (0, 1, 2)


def test_parse_scores():
    reranker = CrossEncoderReranker()
    response = '[{"doc": 1, "score": 9}, {"doc": 2, "score": 3}, {"doc": 3, "score": 7}]'
    scores = reranker._parse_scores(response, 3)
    assert scores[0] == 0.9  # doc 1 → index 0, 9/10
    assert scores[1] == 0.3  # doc 2 → index 1, 3/10
    assert scores[2] == 0.7  # doc 3 → index 2, 7/10


def test_parse_scores_invalid_json():
    reranker = CrossEncoderReranker()
    scores = reranker._parse_scores("not json at all", 3)
    assert scores == {}


def test_parse_scores_out_of_range():
    reranker = CrossEncoderReranker()
    response = '[{"doc": 99, "score": 5}]'
    scores = reranker._parse_scores(response, 3)
    assert 98 not in scores  # out of range, should be skipped
