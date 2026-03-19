"""日常类技能测试 — 15个"""

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


class TestDailySkills:

    @pytest.mark.asyncio
    async def test_calculator(self):
        r = await SkillEngine.execute("calculator", expression="(2+3)*4")
        assert r["success"] is True
        assert "20" in r["result"]

    @pytest.mark.asyncio
    async def test_calculator_division(self):
        r = await SkillEngine.execute("calculator", expression="100/3")
        assert r["success"] is True
        assert "33" in r["result"]

    @pytest.mark.asyncio
    async def test_unit_converter(self):
        r = await SkillEngine.execute("unit_converter", value=1, from_unit="km", to_unit="m")
        assert r["success"] is True
        assert "1000" in r["result"]

    @pytest.mark.asyncio
    async def test_password_generator(self):
        r = await SkillEngine.execute("password_generator", length=20)
        assert r["success"] is True
        assert len(r["result"]) > 0

    @pytest.mark.asyncio
    async def test_bmi_calculator(self):
        r = await SkillEngine.execute("bmi_calculator", weight=70, height=175)
        assert r["success"] is True
        assert "BMI" in r["result"]

    @pytest.mark.asyncio
    async def test_random_generator(self):
        r = await SkillEngine.execute("random_generator", min_val=1, max_val=100)
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_countdown_timer(self):
        r = await SkillEngine.execute("countdown_timer", target_date="2030-01-01")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_color_converter(self):
        r = await SkillEngine.execute("color_converter", color="#FF0000")
        assert r["success"] is True
        assert "255" in r["result"]

    @pytest.mark.asyncio
    async def test_morse_code_encode(self):
        r = await SkillEngine.execute("morse_code", text="SOS", mode="encode")
        assert r["success"] is True
        assert "..." in r["result"]

    @pytest.mark.asyncio
    async def test_zodiac_lookup(self):
        r = await SkillEngine.execute("zodiac_lookup", month=3, day=15)
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_calorie_calculator(self):
        r = await SkillEngine.execute("calorie_calculator", weight=70, height=175, age=25, gender="male")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_tip_calculator(self):
        r = await SkillEngine.execute("tip_calculator", amount=100, tip_percent=15)
        assert r["success"] is True
        assert "15" in r["result"]

    @pytest.mark.asyncio
    async def test_decision_maker(self):
        r = await SkillEngine.execute("decision_maker", options="吃火锅,吃烧烤,吃面条")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_datetime_calc(self):
        r = await SkillEngine.execute("datetime_calc", date="2024-01-01", days=30)
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_habit_tracker(self):
        r = await SkillEngine.execute("habit_tracker", action="add", habit="跑步")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_dice_roller(self):
        r = await SkillEngine.execute("dice_roller", notation="2d6")
        assert r["success"] is True
