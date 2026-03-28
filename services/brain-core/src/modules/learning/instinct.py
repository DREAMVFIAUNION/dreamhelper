"""Instinct 数据模型 — 从会话中提取的行为模式

Instinct 是一种带有置信度的行为观察:
- 置信度 < 0.3 → pending (30天后自动清理)
- 置信度 0.3 - 0.8 → confirmed (持续观察)
- 置信度 ≥ 0.8 → 可进化为 Skill
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class InstinctStatus(str, Enum):
    PENDING = "pending"          # 刚提取，低置信度
    CONFIRMED = "confirmed"      # 多次观察确认
    EVOLVED = "evolved"          # 已进化为 Skill
    PRUNED = "pruned"            # 已清理


@dataclass
class Instinct:
    """单条行为模式"""
    id: str                                  # UUID
    pattern: str                             # 模式描述 (如 "用户偏好用 TypeScript 写后端")
    category: str                            # 分类 (coding_style, preference, workflow, emotional)
    confidence: float = 0.3                  # 置信度 0.0 - 1.0
    status: InstinctStatus = InstinctStatus.PENDING
    evidence: list[str] = field(default_factory=list)   # 支持证据 (会话片段)
    source_sessions: list[str] = field(default_factory=list)  # 来源会话 ID
    created_at: str = ""
    updated_at: str = ""
    evolved_to: Optional[str] = None         # 进化后的 Skill 名称

    def __post_init__(self):
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def reinforce(self, evidence: str, session_id: str = ""):
        """强化模式：增加置信度"""
        self.confidence = min(1.0, self.confidence + 0.15)
        self.evidence.append(evidence[:200])
        if session_id:
            self.source_sessions.append(session_id)
        self.updated_at = datetime.now().isoformat()
        if self.confidence >= 0.3 and self.status == InstinctStatus.PENDING:
            self.status = InstinctStatus.CONFIRMED

    def decay(self, amount: float = 0.05):
        """衰减：随时间降低置信度"""
        self.confidence = max(0.0, self.confidence - amount)
        if self.confidence < 0.1:
            self.status = InstinctStatus.PRUNED

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pattern": self.pattern,
            "category": self.category,
            "confidence": round(self.confidence, 3),
            "status": self.status.value,
            "evidence_count": len(self.evidence),
            "source_sessions": len(self.source_sessions),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "evolved_to": self.evolved_to,
        }
