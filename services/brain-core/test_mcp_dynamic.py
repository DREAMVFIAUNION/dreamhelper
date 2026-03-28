import asyncio
from src.modules.mcp.mcp_tool_bridge import MCPDynamicSkill
from src.modules.tools.skills.skill_engine import SkillEngine

async def main():
    skill = MCPDynamicSkill("test-server", "test-tool", "Test Tool", {"type": "object", "properties": {"msg": {"type": "string"}}})
    SkillEngine.register(skill)
    ret = await SkillEngine.execute("mcp_test_server_test_tool", msg="hello world")
    print("Execution result: ", ret)

asyncio.run(main())
