"""Instinct 存储层 — 内存 + 文件持久化

开发环境使用 JSON 文件存储，支持增删查改和批量操作。
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from .instinct import Instinct, InstinctStatus

logger = logging.getLogger("learning.store")

# 默认存储路径
_DEFAULT_STORE_PATH = os.getenv(
    "INSTINCT_STORE_PATH",
    str(Path(__file__).parent.parent.parent.parent / "data" / "instincts.json"),
)


class InstinctStore:
    """Instinct 持久化存储"""

    _instance: Optional["InstinctStore"] = None
    _instincts: dict[str, Instinct] = {}

    def __init__(self, store_path: str = _DEFAULT_STORE_PATH):
        self._store_path = store_path
        self._load()

    @classmethod
    def get_instance(cls) -> "InstinctStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self):
        """从文件加载"""
        if not os.path.exists(self._store_path):
            self._instincts = {}
            return
        try:
            with open(self._store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._instincts = {}
            for item in data:
                inst = Instinct(
                    id=item["id"],
                    pattern=item["pattern"],
                    category=item.get("category", "preference"),
                    confidence=item.get("confidence", 0.3),
                    status=InstinctStatus(item.get("status", "pending")),
                    evidence=item.get("evidence", []),
                    source_sessions=item.get("source_sessions", []),
                    created_at=item.get("created_at", ""),
                    updated_at=item.get("updated_at", ""),
                    evolved_to=item.get("evolved_to"),
                )
                self._instincts[inst.id] = inst
            logger.info("Loaded %d instincts from %s", len(self._instincts), self._store_path)
        except Exception as e:
            logger.warning("Failed to load instincts: %s", e)
            self._instincts = {}

    def _save(self):
        """保存到文件"""
        os.makedirs(os.path.dirname(self._store_path), exist_ok=True)
        data = [
            {
                "id": inst.id,
                "pattern": inst.pattern,
                "category": inst.category,
                "confidence": inst.confidence,
                "status": inst.status.value,
                "evidence": inst.evidence[-10:],  # 只保留最近10条证据
                "source_sessions": inst.source_sessions[-20:],
                "created_at": inst.created_at,
                "updated_at": inst.updated_at,
                "evolved_to": inst.evolved_to,
            }
            for inst in self._instincts.values()
        ]
        with open(self._store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, instinct: Instinct):
        """添加新 Instinct"""
        # 检查是否有相似的已存在 Instinct（简单文本匹配）
        for existing in self._instincts.values():
            if existing.status == InstinctStatus.PRUNED:
                continue
            if _is_similar(existing.pattern, instinct.pattern):
                existing.reinforce(
                    evidence=instinct.evidence[0] if instinct.evidence else "",
                    session_id=instinct.source_sessions[0] if instinct.source_sessions else "",
                )
                self._save()
                logger.info("Reinforced existing instinct: %s (confidence: %.2f)", existing.pattern[:50], existing.confidence)
                return
        self._instincts[instinct.id] = instinct
        self._save()

    def get(self, instinct_id: str) -> Optional[Instinct]:
        return self._instincts.get(instinct_id)

    def list_all(self, status: Optional[InstinctStatus] = None) -> list[Instinct]:
        results = list(self._instincts.values())
        if status:
            results = [i for i in results if i.status == status]
        return sorted(results, key=lambda i: i.confidence, reverse=True)

    def list_by_category(self, category: str) -> list[Instinct]:
        return [i for i in self._instincts.values() if i.category == category and i.status != InstinctStatus.PRUNED]

    def prune_expired(self, max_age_days: int = 30) -> int:
        """清理过期的低置信度 Instinct"""
        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()
        pruned = 0
        for inst in list(self._instincts.values()):
            if inst.status == InstinctStatus.PENDING and inst.updated_at < cutoff:
                inst.status = InstinctStatus.PRUNED
                pruned += 1
        if pruned:
            self._save()
        return pruned

    def get_stats(self) -> dict:
        by_status = {}
        by_category = {}
        for inst in self._instincts.values():
            by_status[inst.status.value] = by_status.get(inst.status.value, 0) + 1
            if inst.status != InstinctStatus.PRUNED:
                by_category[inst.category] = by_category.get(inst.category, 0) + 1
        return {
            "total": len(self._instincts),
            "by_status": by_status,
            "by_category": by_category,
        }


def _is_similar(a: str, b: str, threshold: float = 0.6) -> bool:
    """简单相似度检测（基于词重叠）"""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b)
    return overlap / max(len(words_a), len(words_b)) >= threshold
