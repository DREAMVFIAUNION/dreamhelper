"""Milvus 向量存储 — 文档分块的向量索引与检索"""

from typing import List, Optional, Dict, Any

from ....common.config import settings

COLLECTION_NAME = "dreamhelp_chunks"


class MilvusStore:
    """Milvus 向量存储封装"""

    def __init__(self):
        self._collection = None
        self._connected = False
        self.dim = settings.EMBEDDING_DIM

    def _ensure_connection(self):
        """延迟连接 Milvus"""
        if self._connected:
            return
        try:
            from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
            )

            if utility.has_collection(COLLECTION_NAME):
                self._collection = Collection(COLLECTION_NAME)
                self._collection.load()
            else:
                fields = [
                    FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, is_primary=True, max_length=128),
                    FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=128),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=2048),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
                ]
                schema = CollectionSchema(fields=fields, description="DreamHelp RAG chunks")
                self._collection = Collection(name=COLLECTION_NAME, schema=schema)

                # 创建 IVF_FLAT 索引
                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128},
                }
                self._collection.create_index(field_name="embedding", index_params=index_params)
                self._collection.load()
                print(f"  [Milvus] Created collection '{COLLECTION_NAME}' (dim={self.dim})")

            self._connected = True
        except Exception as e:
            print(f"  [Milvus] Connection failed: {e}")
            self._connected = False

    def insert(
        self,
        chunk_ids: List[str],
        doc_ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[str]] = None,
    ) -> int:
        """插入分块向量"""
        self._ensure_connection()
        if not self._collection:
            return 0

        if metadatas is None:
            metadatas = ["{}"] * len(chunk_ids)

        # 截断超长文本
        texts = [t[:8000] if len(t) > 8000 else t for t in texts]
        metadatas = [m[:2000] if len(m) > 2000 else m for m in metadatas]

        data = [chunk_ids, doc_ids, texts, metadatas, embeddings]
        self._collection.insert(data)
        self._collection.flush()
        return len(chunk_ids)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        doc_id_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """向量相似度检索"""
        self._ensure_connection()
        if not self._collection:
            return []

        search_params = {"metric_type": "COSINE", "params": {"nprobe": 16}}
        expr = f'doc_id == "{doc_id_filter}"' if doc_id_filter else None

        results = self._collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["chunk_id", "doc_id", "text", "metadata"],
        )

        hits = []
        for hit in results[0]:
            hits.append({
                "chunk_id": hit.entity.get("chunk_id"),
                "doc_id": hit.entity.get("doc_id"),
                "text": hit.entity.get("text"),
                "metadata": hit.entity.get("metadata"),
                "score": hit.distance,
            })
        return hits

    def delete(self, doc_id: str) -> int:
        """删除指定文档的所有分块"""
        self._ensure_connection()
        if not self._collection:
            return 0

        expr = f'doc_id == "{doc_id}"'
        self._collection.delete(expr)
        self._collection.flush()
        return 1

    def count(self) -> int:
        """获取总分块数"""
        self._ensure_connection()
        if not self._collection:
            return 0
        return self._collection.num_entities

    @property
    def available(self) -> bool:
        """是否可用"""
        self._ensure_connection()
        return self._connected and self._collection is not None


# 全局单例
_milvus_store: Optional[MilvusStore] = None


def get_milvus_store() -> MilvusStore:
    global _milvus_store
    if _milvus_store is None:
        _milvus_store = MilvusStore()
    return _milvus_store
