"""文件哈希计算器 — 计算文本内容的多种哈希值"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import hashlib


class FileHashSchema(SkillSchema):
    content: str = Field(description="要计算哈希的文本内容")
    algorithm: str = Field(default="all", description="算法: md5/sha1/sha256/sha512/all")


class FileHasherSkill(BaseSkill):
    name = "file_hasher"
    description = "计算文本内容的哈希值 (MD5/SHA1/SHA256/SHA512)"
    category = "coding"
    args_schema = FileHashSchema
    tags = ["哈希", "hash", "MD5", "SHA", "校验"]

    async def execute(self, **kwargs: Any) -> str:
        content = kwargs["content"]
        algo = kwargs.get("algorithm", "all").lower()
        data = content.encode("utf-8")

        algos = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512,
        }

        if algo != "all" and algo not in algos:
            return f"不支持的算法: {algo}，可用: md5/sha1/sha256/sha512/all"

        lines = [f"哈希计算 ({len(data)} 字节):"]
        targets = algos if algo == "all" else {algo: algos[algo]}

        for name, func in targets.items():
            h = func(data).hexdigest()
            lines.append(f"  {name.upper()}: {h}")

        return "\n".join(lines)
