"""RAG API 路由 — 文档摄入 + 查询"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

from ...common.rate_limit import limiter
from .rag_pipeline import get_rag_pipeline
from .indexer.document_indexer import get_document_indexer

router = APIRouter(prefix="/rag", tags=["rag"])


class IngestRequest(BaseModel):
    doc_id: str
    title: str
    content: str
    type: str = "text"


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


@router.post("/ingest")
@limiter.limit("10/minute")
async def ingest_document(request: Request, req: IngestRequest):
    """接收前端上传的文档并加入 RAG 索引"""
    pipeline = get_rag_pipeline()

    # memory 模式: 内存 TF-IDF 索引
    chunk_count = pipeline.add_document(
        doc_id=req.doc_id,
        title=req.title,
        content=req.content,
        doc_type=req.type,
    )

    # vector/hybrid 模式: 额外写入 Milvus + ES
    indexer = get_document_indexer()
    ext_chunks = await indexer.index_document(
        doc_id=req.doc_id,
        title=req.title,
        content=req.content,
        doc_type=req.type,
    )

    stats = pipeline.get_stats()
    return {
        "success": True,
        "doc_id": req.doc_id,
        "chunks": chunk_count,
        "vector_chunks": ext_chunks,
        "mode": stats.get("mode", "memory"),
        "total_docs": stats.get("documents", 0),
        "total_chunks": stats.get("chunks", 0),
    }


@router.post("/query")
@limiter.limit("10/minute")
async def query_rag(request: Request, req: QueryRequest):
    """RAG 检索查询"""
    pipeline = get_rag_pipeline()
    result = await pipeline.query(req.question, req.top_k)
    return {
        "success": True,
        "answer": result.answer,
        "sources": result.sources,
        "confidence": result.confidence,
    }


@router.post("/sync")
@limiter.limit("3/minute")
async def sync_from_db(request: Request):
    """从 PostgreSQL 重新同步用户文档到 RAG 内存索引"""
    from .setup import sync_documents_from_db
    await sync_documents_from_db()
    pipeline = get_rag_pipeline()
    return {"success": True, **pipeline.get_stats()}


@router.delete("/document/{doc_id}")
@limiter.limit("10/minute")
async def delete_document(request: Request, doc_id: str):
    """从 RAG 索引中删除文档"""
    pipeline = get_rag_pipeline()
    pipeline.remove_document(doc_id)

    # vector/hybrid 模式也删除外部索引
    indexer = get_document_indexer()
    await indexer.delete_document(doc_id)

    return {"success": True, "doc_id": doc_id}


@router.get("/stats")
@limiter.limit("30/minute")
async def rag_stats(request: Request):
    """RAG 统计信息"""
    pipeline = get_rag_pipeline()
    return pipeline.get_stats()
