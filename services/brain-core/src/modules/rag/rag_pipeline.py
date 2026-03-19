"""RAG 流水线 — 内存文档库 + TF-IDF 检索（Phase 3）

Phase 3: 纯内存实现，零外部依赖
Phase 4+: 迁移到 Milvus(向量) + Elasticsearch(BM25)
"""

import math
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class RAGResult:
    answer: str
    sources: List[dict]
    confidence: float


@dataclass
class Document:
    """文档"""
    doc_id: str
    title: str
    content: str
    doc_type: str = "text"  # text, markdown, code, faq
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class Chunk:
    """文档分块"""
    chunk_id: str
    doc_id: str
    content: str
    index: int
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """检索结果"""
    chunk: Chunk
    score: float
    doc_title: str


def _tokenize(text: str) -> list[str]:
    """分词：中文用 jieba 词级分词，英文按词"""
    tokens = []
    # 英文单词
    for word in re.findall(r'[a-zA-Z]+', text.lower()):
        tokens.append(word)
    # 中文分词
    try:
        import jieba
        for word in jieba.cut(text):
            word = word.strip()
            if word and '\u4e00' <= word[0] <= '\u9fff':
                tokens.append(word)
    except ImportError:
        # fallback: 按字分
        for ch in text:
            if '\u4e00' <= ch <= '\u9fff':
                tokens.append(ch)
    return tokens


class InMemoryDocStore:
    """内存文档存储 + TF-IDF 检索"""

    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._documents: Dict[str, Document] = {}
        self._chunks: Dict[str, Chunk] = {}
        self._doc_chunks: Dict[str, List[str]] = defaultdict(list)  # doc_id → [chunk_id]
        # TF-IDF 索引
        self._chunk_tokens: Dict[str, list[str]] = {}  # chunk_id → tokens
        self._df: Counter = Counter()  # document frequency
        self._total_chunks: int = 0

    def add_document(self, doc: Document) -> int:
        """添加文档，自动分块并建立索引"""
        self._documents[doc.doc_id] = doc
        chunks = self._split_chunks(doc)
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk
            self._doc_chunks[doc.doc_id].append(chunk.chunk_id)
            # 建立 TF-IDF 索引
            tokens = _tokenize(chunk.content)
            self._chunk_tokens[chunk.chunk_id] = tokens
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self._df[t] += 1
            self._total_chunks += 1
        return len(chunks)

    def remove_document(self, doc_id: str):
        """删除文档及其分块"""
        chunk_ids = self._doc_chunks.pop(doc_id, [])
        for cid in chunk_ids:
            tokens = self._chunk_tokens.pop(cid, [])
            for t in set(tokens):
                self._df[t] -= 1
                if self._df[t] <= 0:
                    del self._df[t]
            self._chunks.pop(cid, None)
            self._total_chunks -= 1
        self._documents.pop(doc_id, None)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """TF-IDF 检索"""
        if not self._chunks:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scores: Dict[str, float] = {}
        N = max(self._total_chunks, 1)

        for chunk_id, chunk_tokens in self._chunk_tokens.items():
            if not chunk_tokens:
                continue
            tf_counter = Counter(chunk_tokens)
            score = 0.0
            for qt in query_tokens:
                tf = tf_counter.get(qt, 0) / len(chunk_tokens)
                df = self._df.get(qt, 0)
                idf = math.log((N + 1) / (df + 1)) + 1
                score += tf * idf
            if score > 0:
                scores[chunk_id] = score

        # 排序取 top_k
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for chunk_id, score in ranked:
            chunk = self._chunks[chunk_id]
            doc = self._documents.get(chunk.doc_id)
            results.append(SearchResult(
                chunk=chunk,
                score=score,
                doc_title=doc.title if doc else "",
            ))
        return results

    def _split_chunks(self, doc: Document) -> List[Chunk]:
        """将文档分块"""
        text = doc.content
        if doc.doc_type == "markdown":
            return self._split_markdown(doc)

        chunks = []
        # 先按段落分
        paragraphs = text.split("\n\n")
        current = ""
        idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) > self.chunk_size and current:
                chunks.append(Chunk(
                    chunk_id=f"{doc.doc_id}_c{idx}",
                    doc_id=doc.doc_id,
                    content=current.strip(),
                    index=idx,
                    metadata={"type": doc.doc_type},
                ))
                # 保留 overlap
                overlap_text = current[-self.chunk_overlap:] if len(current) > self.chunk_overlap else ""
                current = overlap_text + para + "\n\n"
                idx += 1
            else:
                current += para + "\n\n"

        if current.strip():
            chunks.append(Chunk(
                chunk_id=f"{doc.doc_id}_c{idx}",
                doc_id=doc.doc_id,
                content=current.strip(),
                index=idx,
                metadata={"type": doc.doc_type},
            ))

        return chunks if chunks else [Chunk(
            chunk_id=f"{doc.doc_id}_c0",
            doc_id=doc.doc_id,
            content=text[:self.chunk_size],
            index=0,
            metadata={"type": doc.doc_type},
        )]

    def _split_markdown(self, doc: Document) -> List[Chunk]:
        """按 Markdown 标题分块"""
        sections = re.split(r'\n(?=#{1,3}\s)', doc.content)
        chunks = []
        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
            # 如果段落太长，再按段落分
            if len(section) > self.chunk_size * 2:
                sub_chunks = self._split_long_section(doc.doc_id, section, len(chunks))
                chunks.extend(sub_chunks)
            else:
                chunks.append(Chunk(
                    chunk_id=f"{doc.doc_id}_c{len(chunks)}",
                    doc_id=doc.doc_id,
                    content=section,
                    index=len(chunks),
                    metadata={"type": "markdown"},
                ))
        return chunks or [Chunk(
            chunk_id=f"{doc.doc_id}_c0",
            doc_id=doc.doc_id,
            content=doc.content[:self.chunk_size],
            index=0,
            metadata={"type": "markdown"},
        )]

    def _split_long_section(self, doc_id: str, text: str, start_idx: int) -> List[Chunk]:
        """将过长的段落按 chunk_size 切分"""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk_text = text[i:i + self.chunk_size]
            if chunk_text.strip():
                chunks.append(Chunk(
                    chunk_id=f"{doc_id}_c{start_idx + len(chunks)}",
                    doc_id=doc_id,
                    content=chunk_text.strip(),
                    index=start_idx + len(chunks),
                ))
        return chunks

    def get_stats(self) -> dict:
        return {
            "documents": len(self._documents),
            "chunks": self._total_chunks,
            "vocab_size": len(self._df),
        }


class RAGPipeline:
    """检索增强生成流水线

    支持三种模式 (RAG_MODE 环境变量):
    - memory: 内存 TF-IDF 检索 (默认, 零外部依赖)
    - vector: Milvus 向量检索
    - hybrid: Milvus 向量 + ES BM25 + RRF 融合
    """

    def __init__(self):
        from ...common.config import settings
        self.mode = settings.RAG_MODE
        self.doc_store = InMemoryDocStore()

    def add_document(self, doc_id: str, title: str, content: str,
                     doc_type: str = "text", metadata: dict | None = None) -> int:
        """添加文档到知识库 (memory 模式始终索引)"""
        doc = Document(
            doc_id=doc_id, title=title, content=content,
            doc_type=doc_type, metadata=metadata or {},
        )
        count = self.doc_store.add_document(doc)
        print(f"  📄 Indexed document '{title}' → {count} chunks (mode={self.mode})")
        return count

    def remove_document(self, doc_id: str):
        """删除文档"""
        self.doc_store.remove_document(doc_id)

    def retrieve(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """检索相关文档片段 (memory 模式)"""
        return self.doc_store.search(query, top_k)

    async def retrieve_advanced(self, query: str, top_k: int = 5) -> List[dict]:
        """高级检索 — 查询增强 + 多路召回 + Reranker 重排序"""
        # 查询增强: 生成多个查询变体
        from .retriever.query_enhancer import QueryEnhancer
        enhancer = QueryEnhancer(use_llm=False)  # 默认仅用关键词增强（快速）
        query_variants = await enhancer.enhance(query)

        # 多路召回: 每个查询变体独立检索, 合并去重
        candidates: List[dict] = []
        seen_contents: set[str] = set()
        fetch_k = min(top_k * 2, 20)

        for q in query_variants:
            if self.mode == "memory":
                results = self.retrieve(q, fetch_k)
                for r in results:
                    content_key = r.chunk.content[:100]
                    if content_key not in seen_contents:
                        seen_contents.add(content_key)
                        candidates.append({
                            "content": r.chunk.content, "title": r.doc_title,
                            "score": r.score, "source": "tfidf",
                        })
            else:
                from .retriever.hybrid_retriever import get_hybrid_retriever
                retriever = get_hybrid_retriever()
                if self.mode == "vector":
                    results = await retriever.retrieve_vector(q, fetch_k)
                else:  # hybrid
                    results = await retriever.retrieve(q, fetch_k)
                for r in results:
                    content_key = r.content[:100]
                    if content_key not in seen_contents:
                        seen_contents.add(content_key)
                        candidates.append({
                            "content": r.content, "title": r.title,
                            "score": r.score, "source": r.source,
                        })

        # 按分数排序
        candidates.sort(key=lambda x: x["score"], reverse=True)
        candidates = candidates[:fetch_k]

        # Reranker 重排序（候选 >= 2 时才有意义）
        if len(candidates) >= 2:
            try:
                from .reranker.cross_encoder_reranker import CrossEncoderReranker
                reranker = CrossEncoderReranker()
                docs = [c["content"] for c in candidates]
                reranked = await reranker.rerank(query, docs, top_k=top_k)
                # 按 reranker 顺序重建结果
                reranked_results = []
                for rr in reranked:
                    orig = candidates[rr.original_rank]
                    orig["rerank_score"] = rr.score
                    reranked_results.append(orig)
                return reranked_results
            except Exception:
                pass  # reranker 失败则返回原始结果

        return candidates[:top_k]

    def retrieve_context(self, query: str, top_k: int = 3, max_chars: int = 2000) -> str:
        """检索并格式化为可注入 system prompt 的上下文 (同步, memory 模式)"""
        results = self.retrieve(query, top_k)
        if not results:
            return ""

        lines = ["[知识库检索结果]"]
        total = 0
        for r in results:
            snippet = r.chunk.content[:500]
            if total + len(snippet) > max_chars:
                break
            source = f"(来源: {r.doc_title})" if r.doc_title else ""
            lines.append(f"---\n{snippet}\n{source}")
            total += len(snippet)

        return "\n".join(lines)

    async def retrieve_context_async(self, query: str, top_k: int = 3, max_chars: int = 2000) -> str:
        """异步检索上下文 — 支持所有 RAG 模式"""
        context, _ = await self.retrieve_with_sources(query, top_k, max_chars)
        return context

    # 组织认知关键词 — 命中时启用兜底检索
    _ORG_KEYWORDS = frozenset({
        "梦帮", "dreamvfia", "王森冉", "senran", "rnoise", "集团",
        "梦帮科技", "梦帮集团", "组织", "公司", "厂牌", "创始人",
        "qmyth", "seanpilot", "s.r beatz", "真实声音",
    })

    def _is_org_query(self, query: str) -> bool:
        """检测查询是否涉及组织认知"""
        q = query.lower()
        return any(kw in q for kw in self._ORG_KEYWORDS)

    async def retrieve_with_sources(self, query: str, top_k: int = 3, max_chars: int = 2000) -> tuple[str, list[dict]]:
        """检索上下文 + 来源元数据（用于前端引用溯源）

        Returns:
            tuple: (context_string, sources_list)
            sources_list: [{"title": str, "doc_id": str, "score": float, "snippet": str}]
        """
        sources: list[dict] = []

        # 相关性阈值: 低于此分数的结果视为不相关，不注入 prompt
        MIN_RELEVANCE_SCORE = 0.08

        if self.mode == "memory":
            results = self.retrieve(query, top_k)
            # 过滤低相关性结果
            results = [r for r in results if r.score >= MIN_RELEVANCE_SCORE]

            # 组织关键词兜底: 若查询命中组织关键词但无结果，强制注入 org-overview
            if not results and self._is_org_query(query):
                fallback = self.retrieve("DREAMVFIA 组织概况 梦帮 创始人", top_k=1)
                if fallback:
                    results = fallback

            if not results:
                return "", []

            lines = ["[知识库检索结果]"]
            total = 0
            for r in results:
                snippet = r.chunk.content[:500]
                if total + len(snippet) > max_chars:
                    break
                source_label = f"(来源: {r.doc_title})" if r.doc_title else ""
                lines.append(f"---\n{snippet}\n{source_label}")
                total += len(snippet)
                sources.append({
                    "title": r.doc_title,
                    "doc_id": r.chunk.doc_id,
                    "score": round(r.score, 3),
                    "snippet": snippet[:120],
                })
            return "\n".join(lines), sources

        results = await self.retrieve_advanced(query, top_k)
        if not results:
            return "", []

        lines = ["[知识库检索结果]"]
        total = 0
        for r in results:
            snippet = r["content"][:500]
            if total + len(snippet) > max_chars:
                break
            source_label = f"(来源: {r['title']})" if r.get("title") else ""
            lines.append(f"---\n{snippet}\n{source_label}")
            total += len(snippet)
            sources.append({
                "title": r.get("title", ""),
                "doc_id": r.get("doc_id", ""),
                "score": round(r.get("score", 0), 3),
                "snippet": snippet[:120],
            })

        return "\n".join(lines), sources

    async def query(self, question: str, top_k: int = 5) -> RAGResult:
        """执行 RAG 查询（返回结构化结果）"""
        results = await self.retrieve_advanced(question, top_k)
        sources = [
            {"title": r.get("title", ""), "content": r["content"][:200], "score": round(r["score"], 3)}
            for r in results
        ]
        context = await self.retrieve_context_async(question, top_k)
        confidence = results[0]["score"] if results else 0.0
        return RAGResult(answer=context, sources=sources, confidence=confidence)

    def get_stats(self) -> dict:
        stats = self.doc_store.get_stats()
        stats["mode"] = self.mode
        return stats


# 全局单例
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
