"""办公类技能测试 — 15个"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.modules.tools.skills.skill_engine import SkillEngine
from src.modules.tools.skills.setup import register_all_skills

@pytest.fixture(scope="module", autouse=True)
def setup_skills():
    SkillEngine._skills.clear()
    register_all_skills()


class TestOfficeSkills:

    @pytest.mark.asyncio
    async def test_todo_manager(self):
        r = await SkillEngine.execute("todo_manager", action="add", task="写报告")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_pomodoro_timer(self):
        r = await SkillEngine.execute("pomodoro_timer", action="start")
        assert r["success"] is True
        assert "番茄" in r["result"] or "pomodoro" in r["result"].lower()

    @pytest.mark.asyncio
    async def test_json_formatter(self):
        r = await SkillEngine.execute("json_formatter", json_text='{"a":1,"b":2}')
        assert r["success"] is True
        assert '"a"' in r["result"]

    @pytest.mark.asyncio
    async def test_cron_parser(self):
        r = await SkillEngine.execute("cron_parser", expression="0 9 * * 1-5")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_expense_tracker(self):
        r = await SkillEngine.execute("expense_tracker", action="add", amount=50, category="餐饮", note="午餐")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_csv_analyzer(self):
        r = await SkillEngine.execute("csv_analyzer", data="name,score\nAlice,90\nBob,85\nCarol,95")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_email_template(self):
        r = await SkillEngine.execute("email_template", template_type="meeting", recipient="张三")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_meeting_minutes(self):
        r = await SkillEngine.execute("meeting_minutes", title="周例会", attendees="张三,李四", content="讨论项目进度")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_yaml_processor(self):
        r = await SkillEngine.execute("yaml_processor", text="name: test\nage: 25", mode="to_json")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_schedule_planner(self):
        r = await SkillEngine.execute("schedule_planner", action="add", title="开会", time="14:00")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_time_tracker(self):
        r = await SkillEngine.execute("time_tracker", action="start", task="编码")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_invoice_generator(self):
        r = await SkillEngine.execute("invoice_generator", client="客户A", items="服务费:1000,材料费:500")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_kanban_board(self):
        r = await SkillEngine.execute("kanban_board", action="add", task="修复Bug", column="todo")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_gantt_chart(self):
        r = await SkillEngine.execute("gantt_chart", tasks="设计:2024-01-01:2024-01-10,开发:2024-01-11:2024-01-25")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_contact_manager(self):
        r = await SkillEngine.execute("contact_manager", action="add", name="张三", phone="13800138000")
        assert r["success"] is True
