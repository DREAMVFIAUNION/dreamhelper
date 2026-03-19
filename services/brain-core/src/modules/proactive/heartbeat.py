"""心跳检测 + 主动问候（Phase 4）

跟踪用户活跃状态，在合适时机主动发送问候/提醒。
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, List


@dataclass
class UserActivity:
    """用户活跃状态"""
    user_id: str
    last_active: float = field(default_factory=time.time)
    last_greeting: float = 0        # 上次主动问候时间
    session_count: int = 0
    message_count: int = 0
    is_online: bool = False


class HeartbeatTracker:
    """用户心跳追踪器"""

    def __init__(self):
        self._users: Dict[str, UserActivity] = {}
        # 配置
        self.greeting_cooldown = 3600 * 4   # 主动问候冷却：4 小时
        self.idle_threshold = 1800          # 空闲阈值：30 分钟
        self.away_threshold = 3600 * 2      # 离开阈值：2 小时

    def user_online(self, user_id: str):
        """用户上线"""
        if user_id not in self._users:
            self._users[user_id] = UserActivity(user_id=user_id)
        self._users[user_id].is_online = True
        self._users[user_id].last_active = time.time()
        # 通知意识核用户注册表
        try:
            from ..consciousness.user_registry import get_user_registry
            get_user_registry().on_heartbeat(user_id)
        except Exception:
            pass

    def user_offline(self, user_id: str):
        """用户下线"""
        if user_id in self._users:
            self._users[user_id].is_online = False

    def user_active(self, user_id: str):
        """用户活跃（发消息/操作）"""
        if user_id not in self._users:
            self._users[user_id] = UserActivity(user_id=user_id, is_online=True)
        ua = self._users[user_id]
        ua.last_active = time.time()
        ua.message_count += 1
        ua.is_online = True
        # 通知意识核用户注册表
        try:
            from ..consciousness.user_registry import get_user_registry
            get_user_registry().on_heartbeat(user_id)
        except Exception:
            pass

    def record_greeting(self, user_id: str):
        """记录已发送问候"""
        if user_id in self._users:
            self._users[user_id].last_greeting = time.time()

    def get_users_needing_greeting(self) -> List[UserActivity]:
        """获取需要主动问候的用户列表

        条件：
        1. 用户在线
        2. 距上次问候超过冷却时间
        3. 用户处于空闲状态（有一段时间没操作）
        """
        now = time.time()
        result = []
        for ua in self._users.values():
            if not ua.is_online:
                continue
            idle_time = now - ua.last_active
            greeting_gap = now - ua.last_greeting
            if idle_time > self.idle_threshold and greeting_gap > self.greeting_cooldown:
                result.append(ua)
        return result

    def get_returning_users(self) -> List[UserActivity]:
        """获取回归用户（离开超过 away_threshold 后重新活跃）"""
        now = time.time()
        result = []
        for ua in self._users.values():
            if ua.is_online:
                idle_time = now - ua.last_active
                # 刚刚活跃（5秒内）但之前离开很久
                if idle_time < 5 and ua.last_greeting > 0:
                    last_gap = ua.last_active - ua.last_greeting
                    if last_gap > self.away_threshold:
                        result.append(ua)
        return result

    def get_activity(self, user_id: str) -> Optional[UserActivity]:
        return self._users.get(user_id)

    def get_all_online(self) -> List[UserActivity]:
        return [ua for ua in self._users.values() if ua.is_online]

    def get_stats(self) -> dict:
        online = sum(1 for ua in self._users.values() if ua.is_online)
        return {
            "total_users": len(self._users),
            "online_users": online,
            "total_messages": sum(ua.message_count for ua in self._users.values()),
        }


# 全局单例
_heartbeat: Optional[HeartbeatTracker] = None


def get_heartbeat() -> HeartbeatTracker:
    global _heartbeat
    if _heartbeat is None:
        _heartbeat = HeartbeatTracker()
    return _heartbeat
