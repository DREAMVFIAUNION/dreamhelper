"""SkillToolAdapter — 将 SkillEngine 100 技能暴露给 Agent 系统

解决架构断裂: SkillEngine 注册 100 技能，但 Agent 只能调用 ToolRegistry 中的工具。
本模块注册一个 `run_skill` 调度工具到 ToolRegistry，LLM 通过它调用任意技能。
用单个调度工具代替 100 个独立工具注册，避免系统提示词过长浪费 token。
"""

from typing import Any
from pydantic import BaseModel, Field

from .tool_registry import BaseTool, ToolRegistry
from .skills.skill_engine import SkillEngine


class RunSkillArgs(BaseModel):
    skill_name: str = Field(description="技能名称，如 calculator, password_generator, jwt_decoder 等")
    params: dict = Field(default={}, description="技能参数 (JSON 对象)，具体参数取决于技能")


class SkillDispatchTool(BaseTool):
    """调度工具 — 转发调用到 SkillEngine 中的任意技能"""

    name = "run_skill"
    args_schema = RunSkillArgs

    def __init__(self):
        self.description = self._build_description()

    def _build_description(self) -> str:
        cats = SkillEngine.categories()
        if not cats:
            return "调用技能库中的工具 (技能库未初始化)"

        total = sum(cats.values())
        lines = [f"调用技能库中的 {total} 个工具。可用技能按分类:"]
        for cat, count in sorted(cats.items()):
            skills = [s for s in SkillEngine._skills.values() if s.category == cat]
            names = ", ".join(s.name for s in skills)
            lines.append(f"  [{cat}]({count}个): {names}")
        lines.append("传入 skill_name 和 params 调用对应技能。不确定参数时可只传 skill_name 查看 schema。")
        return "\n".join(lines)

    async def execute(self, **kwargs: Any) -> str:
        skill_name = kwargs.get("skill_name", "").strip()
        if not skill_name:
            return self._list_all_skills()

        skill = SkillEngine.get(skill_name)
        if not skill:
            # 模糊搜索
            matches = SkillEngine.search(skill_name)
            if matches:
                suggestions = ", ".join(m["name"] for m in matches[:5])
                return f"技能 '{skill_name}' 不存在。你是否想调用: {suggestions}"
            return f"技能 '{skill_name}' 不存在。使用 run_skill 不带参数可查看全部技能列表。"

        params = kwargs.get("params", {})
        if isinstance(params, str):
            import json as _json
            try:
                params = _json.loads(params)
            except _json.JSONDecodeError:
                return f"params 不是合法 JSON: {params}"

        # 无参数时返回技能 schema 帮助
        if not params:
            schema = skill.to_schema()
            props = schema.get("parameters", {}).get("properties", {})
            required = schema.get("parameters", {}).get("required", [])
            param_lines = []
            for k, v in props.items():
                req_mark = " (必填)" if k in required else ""
                param_lines.append(f"  - {k}: {v.get('description', v.get('type', 'any'))}{req_mark}")
            return (
                f"技能 [{skill_name}]: {skill.description}\n"
                f"参数:\n" + "\n".join(param_lines) +
                f"\n\n请用 params 传入参数再次调用。"
            )

        result = await SkillEngine.execute(skill_name, **params)
        if result["success"]:
            return result["result"]
        return f"技能执行失败: {result.get('error', '未知错误')}"

    def _list_all_skills(self) -> str:
        cats = SkillEngine.categories()
        lines = [f"技能库共 {sum(cats.values())} 个技能:"]
        for cat, count in sorted(cats.items()):
            skills = [s for s in SkillEngine._skills.values() if s.category == cat]
            names = ", ".join(s.name for s in skills)
            lines.append(f"\n[{cat}] ({count}个):\n  {names}")
        return "\n".join(lines)


def bridge_skills_to_tools():
    """注册 run_skill 调度工具到 ToolRegistry，使 Agent 可调用全部技能"""
    if "run_skill" in ToolRegistry._tools:
        return  # 已注册
    ToolRegistry.register(SkillDispatchTool())
    print(f"  ✓ Bridged {len(SkillEngine._skills)} skills → ToolRegistry via run_skill dispatch tool")
