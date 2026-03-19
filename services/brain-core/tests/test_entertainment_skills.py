"""娱乐类技能测试 — 12个"""

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


class TestEntertainmentSkills:

    @pytest.mark.asyncio
    async def test_coin_flipper(self):
        r = await SkillEngine.execute("coin_flipper", times=5)
        assert r["success"] is True
        assert "正面" in r["result"] or "反面" in r["result"]

    @pytest.mark.asyncio
    async def test_fortune_teller(self):
        r = await SkillEngine.execute("fortune_teller", name="测试用户")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_name_generator(self):
        r = await SkillEngine.execute("name_generator", type="chinese")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_lorem_ipsum(self):
        r = await SkillEngine.execute("lorem_ipsum", paragraphs=2)
        assert r["success"] is True
        assert len(r["result"]) > 50

    @pytest.mark.asyncio
    async def test_ascii_art(self):
        r = await SkillEngine.execute("ascii_art", text="HI")
        assert r["success"] is True
        assert "#" in r["result"] or "*" in r["result"] or "|" in r["result"]

    @pytest.mark.asyncio
    async def test_number_trivia(self):
        r = await SkillEngine.execute("number_trivia", number=42)
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_emoji_art(self):
        r = await SkillEngine.execute("emoji_art", text="hi")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_maze_generator(self):
        r = await SkillEngine.execute("maze_generator", width=5, height=5)
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_sudoku_solver(self):
        puzzle = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
        r = await SkillEngine.execute("sudoku_solver", puzzle=puzzle)
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_anagram_solver(self):
        r = await SkillEngine.execute("anagram_solver", word="listen")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_word_game(self):
        r = await SkillEngine.execute("word_game", mode="riddle")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_rock_paper_scissors(self):
        r = await SkillEngine.execute("rock_paper_scissors", choice="rock", rounds=3)
        assert r["success"] is True
        assert "石头" in r["result"]
