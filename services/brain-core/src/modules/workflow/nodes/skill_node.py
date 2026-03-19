"""技能节点 — 调用已注册的 100 个技能（通过 SkillEngine）"""

from typing import Any

from ..base_node import BaseNode
from ..types import NodeData, NodeDescriptor


class SkillNode(BaseNode):
    def descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(
            type="skill",
            name="技能调用",
            description="调用已注册技能（计算器、CSV分析、密码生成等 100 个）",
            category="skill",
            icon="Wrench",
            color="#F59E0B",
            inputs=["input"],
            outputs=["output"],
            config_schema={
                "skill_id": {"type": "string", "label": "技能 ID", "default": "", "placeholder": "calculator"},
                "params": {"type": "json", "label": "参数 (JSON)", "default": "{}"},
                "use_input_as_params": {
                    "type": "boolean", "label": "使用上游数据作为参数", "default": False,
                },
            },
        )

    async def execute(self, input_data: NodeData, config: dict[str, Any]) -> NodeData:
        from ...tools.skills.skill_engine import SkillEngine

        skill_id = config.get("skill_id", "")
        if not skill_id:
            raise ValueError("技能 ID 不能为空")

        # 构造参数
        params = config.get("params", {})
        if isinstance(params, str):
            import json
            params = json.loads(params)

        if config.get("use_input_as_params") and input_data.items:
            params = {**params, **input_data.items[0]}

        result = await SkillEngine.execute(skill_id, **params)

        if not result["success"]:
            raise ValueError(f"技能 '{skill_id}' 执行失败: {result['error']}")

        return NodeData.single({"skill": skill_id, "result": result["result"]})
