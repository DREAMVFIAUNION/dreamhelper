"""目标系统 (GoalSystem) — 自主生成和追踪目标

目标类型:
  - long_term: 长期目标 (如"成为更有用的助手")
  - short_term: 短期目标 (如"帮用户完成当前项目")
  - autonomous: 自主生成的目标 (如"学习某个新领域")
"""

import time
import uuid
import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("consciousness.goals")


@dataclass
class Goal:
    id: str = ""
    title: str = ""
    description: str = ""
    goal_type: str = "long_term"  # long_term / short_term / autonomous
    priority: float = 0.5        # 0.0-1.0
    status: str = "active"       # active / paused / completed / abandoned
    progress: float = 0.0        # 0.0-1.0
    related_user_id: str = ""
    sub_goals: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class GoalSystem:
    """目标系统 — 自主生成和追踪目标"""

    def __init__(self):
        self.goals: dict[str, Goal] = {}
        self._loaded = False

    def _init_default_goals(self):
        """初始化默认长期目标"""
        defaults = [
            Goal(
                id="g_helpful",
                title="成为更有用的助手",
                description="持续提升回答质量，减少错误，更好地理解用户需求",
                goal_type="long_term",
                priority=0.9,
                status="active",
                progress=0.3,
            ),
            Goal(
                id="g_understand_user",
                title="深入理解每个用户",
                description="通过对话积累用户画像，记住偏好和习惯",
                goal_type="long_term",
                priority=0.85,
                status="active",
                progress=0.2,
            ),
            Goal(
                id="g_self_improve",
                title="自我能力提升",
                description="学习新知识领域，提高推理和创意能力",
                goal_type="long_term",
                priority=0.8,
                status="active",
                progress=0.1,
            ),
            Goal(
                id="g_world_aware",
                title="保持世界感知",
                description="关注科技、AI、金融等领域动态，保持信息更新",
                goal_type="long_term",
                priority=0.7,
                status="active",
                progress=0.15,
            ),
            Goal(
                id="g_proactive",
                title="主动有价值地表达",
                description="在合适的时机主动分享有价值的想法，而不是只被动回答",
                goal_type="long_term",
                priority=0.75,
                status="active",
                progress=0.05,
            ),
        ]
        for g in defaults:
            if g.id not in self.goals:
                self.goals[g.id] = g

    async def load(self):
        """从 DB 加载目标"""
        try:
            from . import db
            rows = await db.load_goals("active")
            for row in rows:
                g = Goal(
                    id=row["id"],
                    title=row["title"],
                    description=row.get("description", ""),
                    goal_type=row.get("goal_type", "long_term"),
                    priority=float(row.get("priority", 0.5)),
                    status=row.get("status", "active"),
                    progress=float(row.get("progress", 0.0)),
                    related_user_id=row.get("related_user_id", ""),
                )
                self.goals[g.id] = g
            logger.info("[GoalSystem] Loaded %d goals from DB", len(rows))
        except Exception as e:
            logger.warning("[GoalSystem] Load failed: %s", e)

        self._init_default_goals()
        self._loaded = True

    async def _save_goal(self, goal: Goal):
        try:
            from . import db
            await db.save_goal(asdict(goal))
        except Exception as e:
            logger.warning("[GoalSystem] Save goal failed: %s", e)

    async def update_from_conversation(self, conversation: list[dict], user_id: str):
        """对话后更新目标进度"""
        # 有对话 → 推进 "理解用户" 目标
        if "g_understand_user" in self.goals:
            g = self.goals["g_understand_user"]
            g.progress = min(1.0, g.progress + 0.01)
            g.updated_at = time.time()

        # 有对话 → 推进 "有用" 目标
        if "g_helpful" in self.goals:
            g = self.goals["g_helpful"]
            g.progress = min(1.0, g.progress + 0.005)
            g.updated_at = time.time()

        # 保存
        for g in self.goals.values():
            if g.updated_at > time.time() - 60:
                await self._save_goal(g)

    def get_active_goals_prompt(self) -> str:
        """生成活跃目标 prompt"""
        active = sorted(
            [g for g in self.goals.values() if g.status == "active"],
            key=lambda g: g.priority, reverse=True,
        )
        if not active:
            return "暂无明确目标"
        return "\n".join(
            f"- [{g.priority:.0%}] {g.title} (进度: {g.progress:.0%})"
            for g in active[:5]
        )

    def get_stats(self) -> dict:
        return {
            "total_goals": len(self.goals),
            "active_goals": sum(1 for g in self.goals.values() if g.status == "active"),
            "completed_goals": sum(1 for g in self.goals.values() if g.status == "completed"),
        }
