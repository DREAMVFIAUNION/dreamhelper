"""文档入库索引器 — 分块 → 嵌入 → Milvus + ES"""

import json
import uuid
from typing import List, Optional

from ..vectorstore.milvus_store import get_milvus_store
from .es_indexer import get_es_indexer
from ...llm.embedding.embedding_provider import get_embedding_provider
from ....common.config import settings


def _simple_chunk(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """简单文本分块"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


class DocumentIndexer:
    """将文档分块、向量化、存入 Milvus + ES"""

    async def index_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        doc_type: str = "text",
    ) -> int:
        """索引单个文档，返回分块数"""
        mode = settings.RAG_MODE

        if mode == "memory":
            return 0  # memory 模式由 RAGPipeline 内部处理

        # 1. 分块
        chunks = _simple_chunk(content)
        if not chunks:
            return 0

        chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        doc_ids = [doc_id] * len(chunks)
        titles = [title] * len(chunks)
        doc_types = [doc_type] * len(chunks)

        indexed = 0

        # 2. 向量索引 (Milvus)
        if mode in ("vector", "hybrid"):
            try:
                embedder = get_embedding_provider()
                embeddings = await embedder.embed(chunks)
                store = get_milvus_store()
                if store.available:
                    store.insert(chunk_ids, doc_ids, chunks, embeddings)
                    indexed += len(chunks)
                    print(f"  [Indexer] Milvus: {len(chunks)} chunks for '{title}'")
            except Exception as e:
                print(f"  [Indexer] Milvus indexing failed: {e}")

        # 3. 全文索引 (ES)
        if mode == "hybrid":
            try:
                es = get_es_indexer()
                if es.available:
                    es.index_chunks(chunk_ids, doc_ids, titles, chunks, doc_types)
                    print(f"  [Indexer] ES: {len(chunks)} chunks for '{title}'")
            except Exception as e:
                print(f"  [Indexer] ES indexing failed: {e}")

        return len(chunks)

    async def delete_document(self, doc_id: str):
        """删除文档索引"""
        mode = settings.RAG_MODE

        if mode in ("vector", "hybrid"):
            try:
                store = get_milvus_store()
                if store.available:
                    store.delete(doc_id)
            except Exception as e:
                print(f"  [Indexer] Milvus delete failed: {e}")

        if mode == "hybrid":
            try:
                es = get_es_indexer()
                if es.available:
                    es.delete(doc_id)
            except Exception as e:
                print(f"  [Indexer] ES delete failed: {e}")


# 全局单例
_document_indexer: Optional[DocumentIndexer] = None


def get_document_indexer() -> DocumentIndexer:
    global _document_indexer
    if _document_indexer is None:
        _document_indexer = DocumentIndexer()
    return _document_indexer
