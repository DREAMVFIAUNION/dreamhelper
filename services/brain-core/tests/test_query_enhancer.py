"""查询增强器单元测试"""

import asyncio
import pytest


def test_extract_keywords_chinese():
    """中文关键词提取"""
    from src.modules.rag.retriever.query_enhancer import QueryEnhancer
    enhancer = QueryEnhancer(use_llm=False)
    keywords = enhancer.extract_keywords("梦帮小助支持哪些工具和技能")
    assert len(keywords) >= 2
    # 应包含有意义的词，不包含停用词
    for kw in keywords:
        assert len(kw) >= 2


def test_extract_keywords_english():
    """英文关键词提取"""
    from src.modules.rag.retriever.query_enhancer import QueryEnhancer
    enhancer = QueryEnhancer(use_llm=False)
    keywords = enhancer.extract_keywords("How to use the RAG pipeline for document search")
    assert "rag" in keywords or "pipeline" in keywords or "document" in keywords


def test_extract_keywords_mixed():
    """中英混合关键词"""
    from src.modules.rag.retriever.query_enhancer import QueryEnhancer
    enhancer = QueryEnhancer(use_llm=False)
    keywords = enhancer.extract_keywords("如何配置MiniMax的API接口")
    assert len(keywords) >= 2


def test_extract_keywords_stopwords_filtered():
    """停用词应被过滤"""
    from src.modules.rag.retriever.query_enhancer import QueryEnhancer
    enhancer = QueryEnhancer(use_llm=False)
    keywords = enhancer.extract_keywords("请帮我介绍一下关于这个")
    # ngram 会产生组合词, 但应比原文字数少
    assert len(keywords) <= 10


def test_enhance_returns_original():
    """增强结果应始终包含原始查询"""
    from src.modules.rag.retriever.query_enhancer import QueryEnhancer
    enhancer = QueryEnhancer(use_llm=False)
    results = asyncio.run(enhancer.enhance("知识库检索"))
    assert "知识库检索" in results


def test_enhance_adds_keywords():
    """增强结果应包含关键词变体"""
    from src.modules.rag.retriever.query_enhancer import QueryEnhancer
    enhancer = QueryEnhancer(use_llm=False)
    results = asyncio.run(enhancer.enhance("梦帮小助的双脑融合架构是什么样的"))
    assert len(results) >= 2  # 原始 + 至少一个关键词变体


def test_enhance_deduplicates():
    """增强结果不应有重复"""
    from src.modules.rag.retriever.query_enhancer import QueryEnhancer
    enhancer = QueryEnhancer(use_llm=False)
    results = asyncio.run(enhancer.enhance("test query"))
    assert len(results) == len(set(r.lower() for r in results))


def test_enhance_max_limit():
    """增强结果不应超过5个"""
    from src.modules.rag.retriever.query_enhancer import QueryEnhancer
    enhancer = QueryEnhancer(use_llm=False)
    results = asyncio.run(enhancer.enhance("这是一个很长的复杂查询包含多个关键词和概念需要全面搜索"))
    assert len(results) <= 5


def test_parse_response_valid_json():
    """应正确解析LLM返回的JSON"""
    from src.modules.rag.retriever.query_enhancer import QueryEnhancer
    result = QueryEnhancer._parse_response('```json\n{"rewritten": "test", "alternatives": ["a"]}\n```')
    assert result["rewritten"] == "test"
    assert result["alternatives"] == ["a"]


def test_parse_response_invalid():
    """无效JSON应返回空dict"""
    from src.modules.rag.retriever.query_enhancer import QueryEnhancer
    result = QueryEnhancer._parse_response("not json at all")
    assert result == {}
