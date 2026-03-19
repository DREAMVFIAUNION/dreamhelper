"""RAG Pipeline 测试 — 文档添加/删除/检索/模式"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.modules.rag.rag_pipeline import RAGPipeline


class TestRAGPipeline:
    """RAG Pipeline 内存模式测试"""

    def setup_method(self):
        self.pipeline = RAGPipeline()

    def test_add_document(self):
        count = self.pipeline.add_document(
            doc_id="test-1",
            title="测试文档",
            content="这是一个测试文档的内容。Python 是一种流行的编程语言。",
        )
        assert count >= 1

    def test_add_and_retrieve(self):
        self.pipeline.add_document(
            doc_id="doc-py",
            title="Python 简介",
            content="Python 是一种广泛使用的高级编程语言，由 Guido van Rossum 创建。",
        )
        results = self.pipeline.retrieve("Python 编程", top_k=3)
        assert len(results) >= 1
        assert "Python" in results[0].chunk.content

    def test_retrieve_context(self):
        self.pipeline.add_document(
            doc_id="doc-ai",
            title="人工智能",
            content="人工智能是计算机科学的一个分支，旨在创建能够模拟人类智能的系统。",
        )
        ctx = self.pipeline.retrieve_context("人工智能是什么", top_k=2)
        assert "人工智能" in ctx
        assert "[知识库检索结果]" in ctx

    def test_remove_document(self):
        self.pipeline.add_document(doc_id="to-delete", title="临时", content="临时内容")
        self.pipeline.remove_document("to-delete")
        stats = self.pipeline.get_stats()
        # Document should be removed
        assert stats["documents"] == 0

    def test_empty_retrieve(self):
        results = self.pipeline.retrieve("不存在的内容", top_k=3)
        assert len(results) == 0

    def test_retrieve_context_empty(self):
        ctx = self.pipeline.retrieve_context("不存在的查询")
        assert ctx == ""

    def test_get_stats(self):
        self.pipeline.add_document(doc_id="s1", title="统计测试", content="短文本")
        stats = self.pipeline.get_stats()
        assert "documents" in stats
        assert "chunks" in stats
        assert "mode" in stats
        assert stats["mode"] == "memory"

    def test_multiple_documents(self):
        self.pipeline.add_document(doc_id="d1", title="文档一", content="FastAPI 是一个现代 Python Web 框架")
        self.pipeline.add_document(doc_id="d2", title="文档二", content="React 是一个 JavaScript UI 库")
        self.pipeline.add_document(doc_id="d3", title="文档三", content="PostgreSQL 是一个强大的关系数据库")
        stats = self.pipeline.get_stats()
        assert stats["documents"] == 3

    @pytest.mark.asyncio
    async def test_query(self):
        self.pipeline.add_document(
            doc_id="q1",
            title="DreamHelp",
            content="DreamHelp 是一个智能助手平台，支持多模型对话和知识库检索。",
        )
        result = await self.pipeline.query("DreamHelp 是什么", top_k=3)
        assert result.answer != ""
        assert len(result.sources) >= 1

    @pytest.mark.asyncio
    async def test_retrieve_advanced_memory(self):
        self.pipeline.add_document(
            doc_id="adv1",
            title="高级检索",
            content="混合检索结合了向量检索和全文检索的优势。",
        )
        results = await self.pipeline.retrieve_advanced("混合检索", top_k=3)
        assert len(results) >= 1
        assert results[0]["source"] == "tfidf"
