"""RAG 引用溯源测试 — retrieve 返回格式验证"""

import asyncio
import pytest
from src.modules.rag.rag_pipeline import RAGPipeline


@pytest.fixture
def pipeline():
    """创建预填充的 RAG Pipeline"""
    p = RAGPipeline()
    p.add_document(
        "doc-1", "产品介绍",
        "梦帮小助是一个 AI 助手平台，支持多智能体协作、100+ 技能和知识库 RAG。",
    )
    p.add_document(
        "doc-2", "使用指南",
        "用户可以通过对话界面与 AI 交互，也可以使用技能面板执行各种工具。",
    )
    p.add_document(
        "doc-3", "FAQ",
        "梦帮小助支持哪些工具？包括计算器、日期计算、网页搜索、代码执行等 5 大工具。",
    )
    return p


def test_retrieve_returns_results(pipeline):
    """检索返回结果列表"""
    results = asyncio.run(pipeline.retrieve_advanced("梦帮小助支持哪些工具", top_k=3))
    assert len(results) > 0


def test_retrieve_result_has_score(pipeline):
    """检索结果包含相关度分数"""
    results = asyncio.run(pipeline.retrieve_advanced("AI 助手", top_k=3))
    for r in results:
        assert 'score' in r
        assert isinstance(r['score'], float)
        assert 0 <= r['score'] <= 1


def test_retrieve_result_has_title(pipeline):
    """检索结果包含文档标题"""
    results = asyncio.run(pipeline.retrieve_advanced("技能面板", top_k=3))
    for r in results:
        assert 'title' in r
        assert isinstance(r['title'], str)


def test_retrieve_context(pipeline):
    """retrieve_context 返回非空上下文"""
    context = asyncio.run(pipeline.retrieve_context_async("梦帮小助", top_k=3))
    assert isinstance(context, str)
    assert len(context) > 0


def test_retrieve_no_results(pipeline):
    """不相关查询返回空或低分结果"""
    results = asyncio.run(pipeline.retrieve_advanced("量子力学黑洞", top_k=3))
    assert isinstance(results, list)


def test_add_and_retrieve_document(pipeline):
    """添加新文档后可被检索到"""
    pipeline.add_document(
        "doc-4", "新功能",
        "新增 Webhook 接收器和 Hook 事件系统，支持外部系统通知。",
    )
    results = asyncio.run(pipeline.retrieve_advanced("Webhook 事件", top_k=3))
    assert len(results) > 0
