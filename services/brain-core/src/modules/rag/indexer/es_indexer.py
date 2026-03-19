"""Elasticsearch BM25 全文索引器"""

from typing import List, Optional, Dict, Any

from ....common.config import settings

ES_INDEX = "dreamhelp_chunks"

# 索引 mapping
INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "chunk_id": {"type": "keyword"},
            "doc_id": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "standard"},
            "content": {"type": "text", "analyzer": "standard"},
            "doc_type": {"type": "keyword"},
            "metadata": {"type": "object", "enabled": False},
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
}


class ESIndexer:
    """Elasticsearch BM25 全文检索"""

    def __init__(self):
        self._client = None
        self._connected = False

    def _ensure_connection(self):
        """延迟连接 ES"""
        if self._connected:
            return
        try:
            from elasticsearch import Elasticsearch

            self._client = Elasticsearch(
                settings.ELASTICSEARCH_URL,
                request_timeout=30,
                max_retries=2,
                retry_on_timeout=True,
            )

            if not self._client.ping():
                print("[ES] Ping failed")
                self._connected = False
                return

            if not self._client.indices.exists(index=ES_INDEX):
                self._client.indices.create(index=ES_INDEX, body=INDEX_MAPPING)
                print(f"  [ES] Created index '{ES_INDEX}'")

            self._connected = True
        except Exception as e:
            print(f"  [ES] Connection failed: {e}")
            self._connected = False

    def index_chunks(
        self,
        chunk_ids: List[str],
        doc_ids: List[str],
        titles: List[str],
        contents: List[str],
        doc_types: Optional[List[str]] = None,
    ) -> int:
        """批量索引分块"""
        self._ensure_connection()
        if not self._client or not self._connected:
            return 0

        if doc_types is None:
            doc_types = ["text"] * len(chunk_ids)

        actions = []
        for i in range(len(chunk_ids)):
            actions.append({"index": {"_index": ES_INDEX, "_id": chunk_ids[i]}})
            actions.append({
                "chunk_id": chunk_ids[i],
                "doc_id": doc_ids[i],
                "title": titles[i],
                "content": contents[i],
                "doc_type": doc_types[i],
            })

        if actions:
            self._client.bulk(body=actions, refresh=True)

        return len(chunk_ids)

    def search(self, query: str, top_k: int = 5, doc_id_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """BM25 全文检索"""
        self._ensure_connection()
        if not self._client or not self._connected:
            return []

        must = [{"multi_match": {"query": query, "fields": ["title^2", "content"], "type": "best_fields"}}]
        if doc_id_filter:
            must.append({"term": {"doc_id": doc_id_filter}})

        body = {
            "query": {"bool": {"must": must}},
            "size": top_k,
            "_source": ["chunk_id", "doc_id", "title", "content", "doc_type"],
        }

        resp = self._client.search(index=ES_INDEX, body=body)
        hits = []
        for hit in resp["hits"]["hits"]:
            src = hit["_source"]
            hits.append({
                "chunk_id": src.get("chunk_id"),
                "doc_id": src.get("doc_id"),
                "title": src.get("title", ""),
                "content": src.get("content", ""),
                "score": hit["_score"],
            })
        return hits

    def delete(self, doc_id: str) -> int:
        """删除指定文档的所有分块"""
        self._ensure_connection()
        if not self._client or not self._connected:
            return 0

        self._client.delete_by_query(
            index=ES_INDEX,
            body={"query": {"term": {"doc_id": doc_id}}},
            refresh=True,
        )
        return 1

    def count(self) -> int:
        """获取总分块数"""
        self._ensure_connection()
        if not self._client or not self._connected:
            return 0
        resp = self._client.count(index=ES_INDEX)
        return resp.get("count", 0)

    @property
    def available(self) -> bool:
        self._ensure_connection()
        return self._connected and self._client is not None


# 全局单例
_es_indexer: Optional[ESIndexer] = None


def get_es_indexer() -> ESIndexer:
    global _es_indexer
    if _es_indexer is None:
        _es_indexer = ESIndexer()
    return _es_indexer
