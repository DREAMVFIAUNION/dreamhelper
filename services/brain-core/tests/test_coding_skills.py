"""编程类技能测试 — 15个"""

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


class TestCodingSkills:

    @pytest.mark.asyncio
    async def test_base64_encode(self):
        r = await SkillEngine.execute("base64_codec", text="hello world", mode="encode")
        assert r["success"] is True
        assert "aGVsbG8gd29ybGQ=" in r["result"]

    @pytest.mark.asyncio
    async def test_base64_decode(self):
        r = await SkillEngine.execute("base64_codec", text="aGVsbG8=", mode="decode")
        assert r["success"] is True
        assert "hello" in r["result"]

    @pytest.mark.asyncio
    async def test_url_codec_encode(self):
        r = await SkillEngine.execute("url_codec", text="hello world", mode="encode")
        assert r["success"] is True
        assert "hello%20world" in r["result"] or "hello+world" in r["result"]

    @pytest.mark.asyncio
    async def test_hash_generator_md5(self):
        r = await SkillEngine.execute("hash_generator", text="test", algorithm="md5")
        assert r["success"] is True
        assert "098f6bcd" in r["result"].lower()

    @pytest.mark.asyncio
    async def test_hash_generator_sha256(self):
        r = await SkillEngine.execute("hash_generator", text="test", algorithm="sha256")
        assert r["success"] is True
        assert "9f86d081" in r["result"].lower()

    @pytest.mark.asyncio
    async def test_uuid_generator(self):
        r = await SkillEngine.execute("uuid_generator", version=4)
        assert r["success"] is True
        assert "-" in r["result"]

    @pytest.mark.asyncio
    async def test_jwt_decoder(self):
        r = await SkillEngine.execute("jwt_decoder", token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U")
        assert r["success"] is True
        assert "1234567890" in r["result"]

    @pytest.mark.asyncio
    async def test_sql_formatter(self):
        r = await SkillEngine.execute("sql_formatter", sql="select a,b from t where c=1")
        assert r["success"] is True
        assert "SELECT" in r["result"] or "select" in r["result"].lower()

    @pytest.mark.asyncio
    async def test_json_validator(self):
        r = await SkillEngine.execute("json_validator", json_text='{"name":"test","value":42}')
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_json_validator_invalid(self):
        r = await SkillEngine.execute("json_validator", json_text='{invalid}')
        assert r["success"] is True  # Skill still succeeds, just reports invalid

    @pytest.mark.asyncio
    async def test_ip_calculator(self):
        r = await SkillEngine.execute("ip_calculator", ip="192.168.1.0/24")
        assert r["success"] is True
        assert "192.168" in r["result"]

    @pytest.mark.asyncio
    async def test_html_entity_codec(self):
        r = await SkillEngine.execute("html_entity_codec", text="<div>hello</div>", mode="encode")
        assert r["success"] is True
        assert "&lt;" in r["result"]

    @pytest.mark.asyncio
    async def test_env_parser(self):
        r = await SkillEngine.execute("env_parser", content="DB_HOST=localhost\nDB_PORT=5432")
        assert r["success"] is True
        assert "DB_HOST" in r["result"]

    @pytest.mark.asyncio
    async def test_code_formatter(self):
        r = await SkillEngine.execute("code_formatter", code="def f(x):return x+1", language="python")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_code_minifier(self):
        r = await SkillEngine.execute("code_minifier", code="function  add( a,  b ) {\n  return  a + b;\n}", language="javascript")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_file_hasher(self):
        r = await SkillEngine.execute("file_hasher", content="test file content", algorithm="sha256")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_diff_patch(self):
        r = await SkillEngine.execute("diff_patch", text1="hello world", text2="hello Python")
        assert r["success"] is True

    @pytest.mark.asyncio
    async def test_regex_tester(self):
        r = await SkillEngine.execute("regex_tester", pattern=r"\d+", text="abc123def456")
        assert r["success"] is True
        assert "123" in r["result"]
