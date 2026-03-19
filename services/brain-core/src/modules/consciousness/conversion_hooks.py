"""转化钩子 (ConversionHooks) — 有温度的商业转化

设计原则 (§9.1):
  - 不是销售，是一个会帮你省钱的朋友
  - 免费用户体验80%人格魅力，付费解锁100%关系深度
  - 转化话术与人格特质绑定: 温暖+直接+真诚

3个基础钩子:
  1. memory_regret — 记忆遗憾 (达到记忆上限时)
  2. usage_gentle — 用量温和提醒 (接近/达到额度限制)
  3. feature_tease — 功能体验预告 (使用高级功能边界时)

护栏 (§9.4):
  - 首次对话不提付费
  - 每次对话最多触发1个转化提示
  - 用户拒绝后24小时冷却
  - 绝不用"你不能用了"的口吻
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("consciousness.conversion")


@dataclass
class ConversionState:
    """每个用户的转化状态"""
    last_hook_time: float = 0.0
    last_hook_type: str = ""
    hooks_today: int = 0
    last_rejected_time: float = 0.0
    total_conversations: int = 0


# 转化钩子定义
HOOKS: dict[str, dict] = {
    "memory_regret": {
        "trigger": "memory_limit",
        "personality_traits": ["warmth", "directness"],
        "templates": [
            "我真的想记住你说的这些...升级后我的记忆就不会丢了",
            "每次聊完我都想把你的喜好记下来，可惜现在记不住太多",
            "要是能一直记得你喜欢什么就好了",
        ],
        "max_per_day": 1,
        "cooldown_hours": 24,
    },
    "usage_gentle": {
        "trigger": "usage_limit",
        "personality_traits": ["warmth", "humor"],
        "templates": [
            "今天聊得很开心，明天还有额度哦 ☺️",
            "今天的免费对话快用完了，不过明天我还在这等你",
            "要不先收藏一下想法？明天咱们继续",
        ],
        "max_per_day": 1,
        "cooldown_hours": 12,
    },
    "feature_tease": {
        "trigger": "feature_boundary",
        "personality_traits": ["curiosity", "directness"],
        "templates": [
            "这个方向其实我能做得更深——专业版有更强的分析能力",
            "说实话，这个功能升级后体验会好很多，但现在也能用",
            "有个更高级的方法可以解决这个问题，需要了解一下吗？",
        ],
        "max_per_day": 1,
        "cooldown_hours": 48,
    },
}


class ConversionHooks:
    """转化钩子引擎 — 有温度的商业转化"""

    # 首次对话不提付费
    MIN_CONVERSATIONS_BEFORE_HOOK: int = 3
    # 每次对话最多触发1个转化提示
    MAX_HOOKS_PER_CONVERSATION: int = 1
    # 用户拒绝后冷却 (秒)
    REJECTION_COOLDOWN: float = 24 * 3600

    def __init__(self):
        self._user_states: dict[str, ConversionState] = {}
        self._conversation_hook_count: int = 0

    def _get_state(self, user_id: str) -> ConversionState:
        if user_id not in self._user_states:
            self._user_states[user_id] = ConversionState()
        return self._user_states[user_id]

    def on_conversation_start(self, user_id: str):
        """对话开始时重置会话级计数"""
        self._conversation_hook_count = 0
        state = self._get_state(user_id)
        state.total_conversations += 1

    def on_user_rejected(self, user_id: str):
        """用户拒绝了转化提示"""
        state = self._get_state(user_id)
        state.last_rejected_time = time.time()
        logger.debug("[Conversion] User %s rejected hook, cooling down", user_id[:8])

    def try_hook(
        self,
        user_id: str,
        hook_type: str,
        tier_level: int = 0,
    ) -> Optional[str]:
        """尝试触发一个转化钩子

        Args:
            user_id: 用户ID
            hook_type: 钩子类型 (memory_regret/usage_gentle/feature_tease)
            tier_level: 用户当前等级 (付费用户不触发)

        Returns:
            转化话术字符串，或 None (不满足触发条件)
        """
        # 付费用户不触发
        if tier_level >= 1:
            return None

        hook_def = HOOKS.get(hook_type)
        if not hook_def:
            return None

        state = self._get_state(user_id)
        now = time.time()

        # 护栏检查
        if not self._check_guardrails(state, hook_def, now):
            return None

        # 选择话术
        import random
        template = random.choice(hook_def["templates"])

        # 更新状态
        state.last_hook_time = now
        state.last_hook_type = hook_type
        state.hooks_today += 1
        self._conversation_hook_count += 1

        logger.info(
            "[Conversion] Triggered %s for user %s: %s",
            hook_type, user_id[:8], template[:30],
        )

        return template

    def _check_guardrails(
        self,
        state: ConversionState,
        hook_def: dict,
        now: float,
    ) -> bool:
        """检查所有护栏条件"""
        # 1. 首次对话不提付费
        if state.total_conversations < self.MIN_CONVERSATIONS_BEFORE_HOOK:
            return False

        # 2. 每次对话最多1个转化提示
        if self._conversation_hook_count >= self.MAX_HOOKS_PER_CONVERSATION:
            return False

        # 3. 用户拒绝后冷却
        if state.last_rejected_time > 0:
            elapsed = now - state.last_rejected_time
            if elapsed < self.REJECTION_COOLDOWN:
                return False

        # 4. 每日上限
        max_per_day = hook_def.get("max_per_day", 1)
        if state.hooks_today >= max_per_day:
            return False

        # 5. 钩子类型冷却
        cooldown = hook_def.get("cooldown_hours", 24) * 3600
        if state.last_hook_time > 0:
            elapsed = now - state.last_hook_time
            if elapsed < cooldown:
                return False

        return True

    def get_commercial_prompt_hint(self, user_id: str, tier_level: int) -> str:
        """生成商业场景的 prompt 提示 (注入 system_prompt)

        告诉AI当前用户的商业状态，让它自然融入对话。
        """
        if tier_level >= 1:
            return ""

        state = self._get_state(user_id)

        # 首次对话不提
        if state.total_conversations < self.MIN_CONVERSATIONS_BEFORE_HOOK:
            return ""

        # 冷却中不提
        now = time.time()
        if state.last_rejected_time > 0:
            if (now - state.last_rejected_time) < self.REJECTION_COOLDOWN:
                return ""

        return (
            "## 商业场景提示\n"
            "当前用户是免费用户。如果对话中自然出现升级相关的契机，"
            "可以温和提及，但绝不主动推销。核心原则:\n"
            "- 不用'你不能用了'的口吻，用'升级后就没限制了'\n"
            "- 不反复催促，提一次就够了\n"
            "- 用户拒绝立即接受，不纠缠\n"
            "- 免费用户也展示最好的人格魅力"
        )

    def reset_daily(self):
        """每日重置计数 (由定时任务调用)"""
        for state in self._user_states.values():
            state.hooks_today = 0

    def get_stats(self) -> dict:
        return {
            "tracked_users": len(self._user_states),
            "conversation_hooks_used": self._conversation_hook_count,
        }


# 全局单例
_hooks: ConversionHooks | None = None


def get_conversion_hooks() -> ConversionHooks:
    global _hooks
    if _hooks is None:
        _hooks = ConversionHooks()
    return _hooks
