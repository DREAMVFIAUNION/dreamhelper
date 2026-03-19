"""文本加密器 — Caesar/ROT13/XOR 加密解密"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class EncryptSchema(SkillSchema):
    text: str = Field(description="要加密/解密的文本")
    method: str = Field(default="rot13", description="方法: caesar/rot13/xor/reverse")
    key: int = Field(default=3, description="密钥(caesar位移数 或 xor密钥)")


class TextEncryptorSkill(BaseSkill):
    name = "text_encryptor"
    description = "文本加密解密: Caesar、ROT13、XOR、逆序"
    category = "document"
    args_schema = EncryptSchema
    tags = ["加密", "解密", "Caesar", "ROT13", "XOR"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs["text"]
        method = kwargs.get("method", "rot13").lower()
        key = int(kwargs.get("key", 3))

        if method == "caesar":
            result = []
            for c in text:
                if c.isalpha():
                    base = ord('A') if c.isupper() else ord('a')
                    result.append(chr((ord(c) - base + key) % 26 + base))
                else:
                    result.append(c)
            encrypted = "".join(result)
            return f"Caesar 加密 (位移={key}):\n  原文: {text}\n  密文: {encrypted}"

        elif method == "rot13":
            result = []
            for c in text:
                if c.isalpha():
                    base = ord('A') if c.isupper() else ord('a')
                    result.append(chr((ord(c) - base + 13) % 26 + base))
                else:
                    result.append(c)
            encrypted = "".join(result)
            return f"ROT13:\n  原文: {text}\n  结果: {encrypted}"

        elif method == "xor":
            result = []
            for c in text:
                result.append(chr(ord(c) ^ (key & 0xFF)))
            encrypted = "".join(result)
            hex_out = " ".join(f"{ord(c):02x}" for c in encrypted[:50])
            return f"XOR 加密 (密钥={key}):\n  原文: {text}\n  HEX: {hex_out}"

        elif method == "reverse":
            return f"逆序:\n  原文: {text}\n  结果: {text[::-1]}"

        return f"不支持的方法: {method}，可用: caesar/rot13/xor/reverse"
