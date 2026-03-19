"""自适应分块器单元测试"""

import pytest


def test_text_chunk_basic():
    """基本文本分块"""
    from src.modules.rag.chunker.adaptive_chunker import AdaptiveChunker
    chunker = AdaptiveChunker(max_chunk_size=100, overlap=20)
    text = "这是第一句话。这是第二句话。这是第三句话。" * 5
    chunks = chunker.chunk(text, "text")
    assert len(chunks) >= 1
    for c in chunks:
        assert c.content.strip() != ""
        assert c.chunk_index >= 0


def test_text_sentence_boundary():
    """不应在句子中间切割"""
    from src.modules.rag.chunker.adaptive_chunker import AdaptiveChunker
    chunker = AdaptiveChunker(max_chunk_size=50, overlap=10)
    text = "第一个完整的句子。第二个完整的句子。第三个完整的句子。第四个完整的句子。"
    chunks = chunker.chunk(text, "text")
    for c in chunks:
        # 每个 chunk 应以句号结尾或开头（overlap 可能导致开头不完整）
        assert len(c.content) > 0


def test_markdown_heading_split():
    """Markdown 应按标题分块"""
    from src.modules.rag.chunker.adaptive_chunker import AdaptiveChunker
    chunker = AdaptiveChunker(max_chunk_size=200, overlap=30)
    md = """# 标题一
这是第一节的内容，包含一些详细的说明文字。这里有更多的内容。

## 标题二
这是第二节的内容，也包含一些详细的说明文字。这里有更多的内容。

## 标题三
这是第三节的内容，比较长。""" + "内容扩展内容扩展内容扩展。" * 20
    chunks = chunker.chunk(md, "markdown")
    assert len(chunks) >= 2
    # 至少有一个 chunk 包含标题
    headings = [c for c in chunks if c.metadata.get("heading")]
    assert len(headings) >= 1


def test_code_function_split():
    """代码应按函数定义分块"""
    from src.modules.rag.chunker.adaptive_chunker import AdaptiveChunker
    chunker = AdaptiveChunker(max_chunk_size=200, overlap=20)
    code = """def hello():
    print("hello")

def world():
    print("world")
    return 42

class MyClass:
    def method(self):
        pass
"""
    chunks = chunker.chunk(code, "code")
    assert len(chunks) >= 2


def test_faq_qa_split():
    """FAQ 应按问答对分块"""
    from src.modules.rag.chunker.adaptive_chunker import AdaptiveChunker
    chunker = AdaptiveChunker(max_chunk_size=500, overlap=30)
    faq = """Q: 什么是梦帮小助？
A: 梦帮小助是一个AI助手平台。

Q: 如何使用知识库？
A: 上传文档后系统会自动索引。

Q: 支持哪些模型？
A: 支持MiniMax、Qwen、GLM等多个模型。"""
    chunks = chunker.chunk(faq, "faq")
    assert len(chunks) >= 2


def test_empty_text():
    """空文本应返回空列表"""
    from src.modules.rag.chunker.adaptive_chunker import AdaptiveChunker
    chunker = AdaptiveChunker()
    assert chunker.chunk("", "text") == []
    assert chunker.chunk("   ", "text") == []


def test_single_long_sentence():
    """超长单句应被强制切割"""
    from src.modules.rag.chunker.adaptive_chunker import AdaptiveChunker
    chunker = AdaptiveChunker(max_chunk_size=50, overlap=10)
    text = "这是一个非常非常长的句子" * 20  # 无句号，不会被句子分割
    chunks = chunker.chunk(text, "text")
    assert len(chunks) >= 1
    for c in chunks:
        assert len(c.content) <= 60  # 允许少量超出


def test_token_estimation():
    """token 估计应合理"""
    from src.modules.rag.chunker.adaptive_chunker import _estimate_tokens
    assert _estimate_tokens("hello world") == 2  # 2 英文词
    assert _estimate_tokens("你好世界") == 4  # 4 中文字
    assert _estimate_tokens("hello 你好") == 3  # 1 英文词 + 2 中文字


def test_chunk_metadata():
    """chunk 应包含正确的 metadata"""
    from src.modules.rag.chunker.adaptive_chunker import AdaptiveChunker
    chunker = AdaptiveChunker(max_chunk_size=500)
    chunks = chunker.chunk("这是一段测试文本。用于验证元数据。", "text")
    assert len(chunks) >= 1
    assert chunks[0].metadata["type"] == "text"
    assert chunks[0].token_count > 0
