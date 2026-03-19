"""密码生成器技能 — 生成安全随机密码 + 强度评估"""

import secrets
import string
import math
from typing import Any

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class PasswordGenSchema(SkillSchema):
    length: int = Field(default=16, description="密码长度，8-64")
    include_upper: bool = Field(default=True, description="包含大写字母")
    include_lower: bool = Field(default=True, description="包含小写字母")
    include_digits: bool = Field(default=True, description="包含数字")
    include_symbols: bool = Field(default=True, description="包含特殊符号")
    count: int = Field(default=1, description="生成数量，1-5")


def _assess_strength(password: str) -> str:
    pool = 0
    if any(c in string.ascii_lowercase for c in password):
        pool += 26
    if any(c in string.ascii_uppercase for c in password):
        pool += 26
    if any(c in string.digits for c in password):
        pool += 10
    if any(c in string.punctuation for c in password):
        pool += 32
    entropy = len(password) * math.log2(pool) if pool > 0 else 0
    if entropy >= 80:
        return f"极强 (熵值: {entropy:.0f} bits)"
    elif entropy >= 60:
        return f"强 (熵值: {entropy:.0f} bits)"
    elif entropy >= 40:
        return f"中等 (熵值: {entropy:.0f} bits)"
    else:
        return f"弱 (熵值: {entropy:.0f} bits)"


class PasswordGeneratorSkill(BaseSkill):
    name = "password_generator"
    description = "生成安全随机密码，可配置长度和字符类型，附带强度评估"
    category = "daily"
    args_schema = PasswordGenSchema
    tags = ["密码", "安全", "随机", "password"]

    async def execute(self, **kwargs: Any) -> str:
        length = max(8, min(64, int(kwargs.get("length", 16))))
        count = max(1, min(5, int(kwargs.get("count", 1))))

        charset = ""
        if kwargs.get("include_lower", True):
            charset += string.ascii_lowercase
        if kwargs.get("include_upper", True):
            charset += string.ascii_uppercase
        if kwargs.get("include_digits", True):
            charset += string.digits
        if kwargs.get("include_symbols", True):
            charset += "!@#$%^&*()-_=+[]{}|;:,.<>?"

        if not charset:
            charset = string.ascii_letters + string.digits

        lines = [f"生成 {count} 个 {length} 位密码:\n"]
        for i in range(count):
            pwd = "".join(secrets.choice(charset) for _ in range(length))
            strength = _assess_strength(pwd)
            lines.append(f"  {i+1}. {pwd}")
            lines.append(f"     强度: {strength}")

        return "\n".join(lines)
