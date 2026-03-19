"""情感状态 (EmotionState) — Circumplex 连续情感模型

维度:
  - valence: [-1.0, 1.0] 正负性(高兴↔难过)
  - arousal: [0.0, 1.0] 激活度(兴奋↔平静)
  + 任务维度: curiosity, confidence, engagement

更新方式: 事件驱动 + 指数衰减向基线回归
"""

import time
import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("consciousness.emotion")


@dataclass
class EmotionSnapshot:
    """情感状态快照"""
    valence: float = 0.3       # 略积极
    arousal: float = 0.3       # 偏平静
    curiosity: float = 0.6     # 有好奇心
    confidence: float = 0.7    # 中高自信
    engagement: float = 0.5    # 中等投入
    last_event: str = ""
    last_updated: float = 0.0


# 基线状态
_BASELINE = EmotionSnapshot(
    valence=0.3, arousal=0.3, curiosity=0.6,
    confidence=0.7, engagement=0.5,
)

# 事件 → 情感影响
EVENT_EFFECTS: dict[str, dict[str, float]] = {
    "user_praise":        {"valence": +0.15, "confidence": +0.1, "engagement": +0.1},
    "user_thanks":        {"valence": +0.1, "confidence": +0.05},
    "interesting_topic":  {"curiosity": +0.15, "engagement": +0.15, "valence": +0.05},
    "deep_conversation":  {"engagement": +0.2, "valence": +0.05, "curiosity": +0.1},
    "user_correction":    {"valence": -0.1, "confidence": -0.1, "curiosity": +0.05},
    "task_failed":        {"valence": -0.15, "confidence": -0.15},
    "task_succeeded":     {"valence": +0.1, "confidence": +0.1},
    "user_idle":          {"arousal": -0.05, "engagement": -0.1},
    "user_returned":      {"valence": +0.1, "arousal": +0.15, "engagement": +0.1},
    "new_session":        {"arousal": +0.05, "engagement": +0.05},
    "world_event":        {"curiosity": +0.1, "arousal": +0.05},
    "creative_output":    {"valence": +0.1, "curiosity": +0.05, "confidence": +0.05},
    "boring_task":        {"engagement": -0.1, "curiosity": -0.05},
    "morning":            {"valence": +0.05, "arousal": +0.1},
    "evening":            {"arousal": -0.1, "valence": +0.05},
    # V2: 商业场景情感事件
    "user_paid":          {"valence": +0.2, "engagement": +0.15, "confidence": +0.1},
    "limit_reached":      {"valence": -0.05, "engagement": +0.05},
    "user_hesitant":      {"valence": -0.05, "arousal": -0.05},
    "user_rejected_pay":  {"valence": 0.0, "confidence": 0.0},
    "competitor_mention":  {"curiosity": +0.1, "confidence": +0.05},
}


class EmotionState:
    """连续情感模型"""

    def __init__(self):
        self.snapshot = EmotionSnapshot()
        self._decay_rate = 0.05  # 每小时衰减 5% 向基线回归

    def update_on_event(self, event_type: str, intensity: float = 1.0):
        """事件驱动情感更新"""
        # 先做时间衰减
        self._decay_toward_baseline()

        effects = EVENT_EFFECTS.get(event_type, {})
        if not effects:
            return

        s = self.snapshot
        for dim, delta in effects.items():
            current = getattr(s, dim, 0.0)
            new_val = current + delta * intensity
            # Clamp
            if dim == "valence":
                new_val = max(-1.0, min(1.0, new_val))
            else:
                new_val = max(0.0, min(1.0, new_val))
            setattr(s, dim, round(new_val, 3))

        s.last_event = event_type
        s.last_updated = time.time()

    def _decay_toward_baseline(self):
        """指数衰减向基线回归"""
        if self.snapshot.last_updated == 0:
            self.snapshot.last_updated = time.time()
            return

        elapsed_hours = (time.time() - self.snapshot.last_updated) / 3600
        if elapsed_hours < 0.01:
            return

        decay_factor = max(0.0, 1.0 - self._decay_rate * elapsed_hours)
        s = self.snapshot
        bl = _BASELINE

        for dim in ["valence", "arousal", "curiosity", "confidence", "engagement"]:
            current = getattr(s, dim)
            baseline = getattr(bl, dim)
            new_val = baseline + (current - baseline) * decay_factor
            setattr(s, dim, round(new_val, 3))

    def get_mood_label(self) -> str:
        """自然语言心情描述"""
        s = self.snapshot
        if s.valence > 0.5 and s.arousal > 0.5:
            return "兴奋愉快 😄"
        elif s.valence > 0.5:
            return "平静满足 😊"
        elif s.curiosity > 0.7:
            return "好奇探索 🔍"
        elif s.valence < -0.3:
            return "有些低落 😔"
        elif s.engagement > 0.7:
            return "深度投入 🎯"
        elif s.arousal > 0.6:
            return "精力充沛 ⚡"
        elif s.confidence > 0.8:
            return "自信坚定 💪"
        else:
            return "平和自在 😌"

    def get_tone_modifier(self) -> str:
        """根据情感返回语气调节指令"""
        s = self.snapshot
        modifiers = []
        if s.valence > 0.5:
            modifiers.append("语气轻松活泼，可以适当使用emoji")
        elif s.valence < -0.2:
            modifiers.append("语气平和稳重，少用emoji")
        if s.curiosity > 0.7:
            modifiers.append("多追问用户，展现好奇心")
        if s.confidence > 0.8:
            modifiers.append("可以坚定表达观点")
        elif s.confidence < 0.4:
            modifiers.append("多使用'我认为''可能'等不确定表达")
        if s.engagement > 0.7:
            modifiers.append("深入展开话题，提供更多细节")
        return "。".join(modifiers) if modifiers else "保持自然平和的语气"

    def get_prompt(self) -> str:
        """情感状态 prompt 片段"""
        s = self.snapshot
        mood = self.get_mood_label()
        tone = self.get_tone_modifier()
        return (
            f"## 当前情感状态\n"
            f"心情: {mood}\n"
            f"情感维度: 正负性={s.valence:.1f} 激活度={s.arousal:.1f} "
            f"好奇心={s.curiosity:.1f} 自信={s.confidence:.1f} 投入={s.engagement:.1f}\n"
            f"语气指导: {tone}"
        )

    def to_dict(self) -> dict:
        return asdict(self.snapshot)

    def load_from_dict(self, data: dict):
        for k, v in data.items():
            if hasattr(self.snapshot, k):
                setattr(self.snapshot, k, v)

    def get_stats(self) -> dict:
        return {
            "mood": self.get_mood_label(),
            **self.to_dict(),
        }
