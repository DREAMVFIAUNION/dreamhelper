"""模板引擎 — 简单变量替换 + 条件 + 循环"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import re
import json


class TemplateSchema(SkillSchema):
    template: str = Field(description="模板文本，使用 {{变量名}} 占位，{{#if 条件}}...{{/if}}，{{#each 列表}}...{{/each}}")
    variables: str = Field(default="{}", description="变量 JSON 对象，如: {\"name\": \"张三\", \"items\": [\"A\",\"B\"]}")


class TemplateEngineSkill(BaseSkill):
    name = "template_engine"
    description = "简单模板引擎: 变量替换、条件判断、循环渲染"
    category = "document"
    args_schema = TemplateSchema
    tags = ["模板", "template", "渲染", "变量"]

    async def execute(self, **kwargs: Any) -> str:
        tpl = kwargs["template"]
        vars_str = kwargs.get("variables", "{}")

        try:
            variables = json.loads(vars_str)
        except json.JSONDecodeError:
            return "变量 JSON 格式错误"

        if not isinstance(variables, dict):
            return "变量必须是 JSON 对象"

        result = tpl

        # {{#each items}}...{{/each}}
        def replace_each(m: re.Match) -> str:
            key = m.group(1).strip()
            body = m.group(2)
            items = variables.get(key, [])
            if not isinstance(items, list):
                return ""
            parts = []
            for i, item in enumerate(items):
                line = body.replace("{{this}}", str(item)).replace("{{@index}}", str(i))
                parts.append(line)
            return "".join(parts)

        result = re.sub(r'\{\{#each\s+(\w+)\}\}([\s\S]*?)\{\{/each\}\}', replace_each, result)

        # {{#if var}}...{{/if}}
        def replace_if(m: re.Match) -> str:
            key = m.group(1).strip()
            body = m.group(2)
            val = variables.get(key)
            if val:
                return body
            return ""

        result = re.sub(r'\{\{#if\s+(\w+)\}\}([\s\S]*?)\{\{/if\}\}', replace_if, result)

        # {{variable}}
        def replace_var(m: re.Match) -> str:
            key = m.group(1).strip()
            return str(variables.get(key, f"[未定义:{key}]"))

        result = re.sub(r'\{\{(\w+)\}\}', replace_var, result)

        return f"渲染结果:\n{result}"
