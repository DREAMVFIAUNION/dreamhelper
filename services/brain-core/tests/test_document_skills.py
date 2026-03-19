"""文档类技能测试 — 13个"""

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


class TestDocumentSkills:

    @pytest.mark.asyncio
    async def test_markdown_processor_to_html(self):
        r = await SkillEngine.execute("markdown_processor", text="# Hello\n**bold**", mode="to_html")
        assert r["success"] is True
        assert "<h1>" in r["result"]

    @pytest.mark.asyncio
    async def test_text_statistics(self):
        r = await SkillEngine.execute("text_statistics", text="Hello world 你好世界 test")
        assert r["success"] is True
        assert "字符" in r["result"] or "字" in r["result"]

    @pytest.mark.asyncio
    async def test_text_diff(self):
        r = await SkillEngine.execute("text_diff", text1="hello world", text2="hello Python")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_regex_builder(self):
        r = await SkillEngine.execute("regex_builder", pattern_type="email")
        assert r["success"] is True
        assert "@" in r["result"]

    @pytest.mark.asyncio
    async def test_template_engine(self):
        r = await SkillEngine.execute("template_engine", template="Hello {{name}}!", variables="name=World")
        assert r["success"] is True
        assert "World" in r["result"]

    @pytest.mark.asyncio
    async def test_csv_to_table(self):
        r = await SkillEngine.execute("csv_to_table", data="name,age\nAlice,30\nBob,25")
        assert r["success"] is True
        assert "Alice" in r["result"]

    @pytest.mark.asyncio
    async def test_json_to_csv(self):
        r = await SkillEngine.execute("json_to_csv", json_text='[{"name":"Alice","age":30},{"name":"Bob","age":25}]')
        assert r["success"] is True
        assert "Alice" in r["result"]

    @pytest.mark.asyncio
    async def test_xml_parser(self):
        r = await SkillEngine.execute("xml_parser", xml_text="<root><item>hello</item></root>")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_html_cleaner(self):
        r = await SkillEngine.execute("html_cleaner", html="<p>Hello <b>World</b></p><script>alert(1)</script>")
        assert r["success"] is True
        assert "Hello" in r["result"]

    @pytest.mark.asyncio
    async def test_text_encryptor_caesar(self):
        r = await SkillEngine.execute("text_encryptor", text="hello", method="caesar", shift=3)
        assert r["success"] is True
        assert "khoor" in r["result"].lower()

    @pytest.mark.asyncio
    async def test_text_translator_dict(self):
        r = await SkillEngine.execute("text_translator_dict", text="hello", direction="en2zh")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_word_counter(self):
        r = await SkillEngine.execute("word_counter", text="Hello 你好 world 世界 test")
        assert r["success"] is True
        assert "英文词" in r["result"] or "单词" in r["result"]

    @pytest.mark.asyncio
    async def test_text_summarizer(self):
        r = await SkillEngine.execute("text_summarizer", text="Python是一种广泛使用的解释型编程语言。它由Guido van Rossum创建。Python的设计哲学强调代码的可读性。")
        assert r["success"] is True
