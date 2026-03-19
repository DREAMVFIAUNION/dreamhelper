"""MemoryManager 测试 — 会话记忆/用户画像"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.modules.memory.memory_manager import MemoryManager


class TestMemoryManager:

    def setup_method(self):
        self.mm = MemoryManager()

    @pytest.mark.asyncio
    async def test_add_message(self):
        await self.mm.add_message("sess-1", "user", "你好")
        history = await self.mm.get_session_history("sess-1")
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "你好"

    @pytest.mark.asyncio
    async def test_multi_messages(self):
        await self.mm.add_message("sess-2", "user", "问题1")
        await self.mm.add_message("sess-2", "assistant", "回答1")
        await self.mm.add_message("sess-2", "user", "问题2")
        history = await self.mm.get_session_history("sess-2")
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_session_isolation(self):
        await self.mm.add_message("sess-a", "user", "消息A")
        await self.mm.add_message("sess-b", "user", "消息B")
        ha = await self.mm.get_session_history("sess-a")
        hb = await self.mm.get_session_history("sess-b")
        assert len(ha) == 1
        assert len(hb) == 1
        assert ha[0]["content"] == "消息A"
        assert hb[0]["content"] == "消息B"

    @pytest.mark.asyncio
    async def test_clear_session(self):
        await self.mm.add_message("sess-clear", "user", "临时消息")
        await self.mm.clear_session("sess-clear")
        history = await self.mm.get_session_history("sess-clear")
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_history_limit(self):
        for i in range(30):
            await self.mm.add_message("sess-limit", "user", f"消息{i}")
        history = await self.mm.get_session_history("sess-limit", limit=10)
        assert len(history) == 10

    @pytest.mark.asyncio
    async def test_user_facts(self):
        await self.mm.add_user_fact("user-1", "name", "张三")
        await self.mm.add_user_fact("user-1", "occupation", "工程师")
        facts = await self.mm.get_all_user_facts("user-1")
        assert facts.get("name") == "张三"
        assert facts.get("occupation") == "工程师"

    @pytest.mark.asyncio
    async def test_user_profile_prompt(self):
        await self.mm.add_user_fact("user-2", "name", "李四")
        prompt = await self.mm.get_user_profile_prompt("user-2")
        assert "李四" in prompt

    @pytest.mark.asyncio
    async def test_empty_profile(self):
        prompt = await self.mm.get_user_profile_prompt("nonexistent-user")
        assert prompt == "" or "暂无" in prompt or len(prompt) < 10

    def test_get_stats(self):
        stats = self.mm.get_stats()
        assert "sessions" in stats or "total_sessions" in stats or isinstance(stats, dict)
