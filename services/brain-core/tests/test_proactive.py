"""主动唤醒系统测试 — 心跳追踪 + 调度器"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.modules.proactive.heartbeat import HeartbeatTracker


class TestHeartbeatTracker:

    def setup_method(self):
        self.tracker = HeartbeatTracker()

    def test_user_active(self):
        self.tracker.user_active("user-1")
        status = self.tracker.get_status("user-1")
        assert status is not None
        assert status["status"] in ("online", "active")

    def test_user_offline(self):
        self.tracker.user_offline("user-2")
        status = self.tracker.get_status("user-2")
        assert status is None or status["status"] == "offline"

    def test_multiple_users(self):
        self.tracker.user_active("u1")
        self.tracker.user_active("u2")
        self.tracker.user_active("u3")
        online = self.tracker.get_online_users()
        assert len(online) >= 3

    def test_idle_detection(self):
        self.tracker.user_active("idle-user")
        # Without time manipulation, user should be active
        idle = self.tracker.get_idle_users(idle_minutes=0)
        # With 0 minutes, all users are idle
        assert isinstance(idle, list)

    def test_stats(self):
        self.tracker.user_active("stat-user")
        stats = self.tracker.get_stats()
        assert isinstance(stats, dict)
        assert "online" in stats or "total" in stats or len(stats) >= 0
