"""Base64 编解码技能"""

import base64
from typing import Any

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class Base64Schema(SkillSchema):
    action: str = Field(description="操作: 'encode'(编码), 'decode'(解码)")
    text: str = Field(description="要编码或解码的文本")


class Base64CodecSkill(BaseSkill):
    name = "base64_codec"
    description = "Base64 编码/解码工具"
    category = "coding"
    args_schema = Base64Schema
    tags = ["base64", "编码", "解码", "encode", "decode"]

    async def execute(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "encode")
        text = kwargs.get("text", "")
        if not text:
            return "请输入文本"

        if action == "encode":
            result = base64.b64encode(text.encode("utf-8")).decode("ascii")
            return f"Base64 编码结果:\n{result}"
        elif action == "decode":
            try:
                result = base64.b64decode(text).decode("utf-8")
                return f"Base64 解码结果:\n{result}"
            except Exception as e:
                return f"解码失败: {e}"
        return f"未知操作: {action}"
