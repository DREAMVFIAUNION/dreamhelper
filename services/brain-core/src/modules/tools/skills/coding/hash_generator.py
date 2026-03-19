"""哈希生成器技能 — 支持多种哈希算法"""

import hashlib
from typing import Any

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema

ALGORITHMS = ["md5", "sha1", "sha256", "sha384", "sha512", "sha3_256", "sha3_512", "blake2b"]


class HashGenSchema(SkillSchema):
    text: str = Field(description="要计算哈希的文本")
    algorithm: str = Field(default="sha256", description=f"哈希算法: {', '.join(ALGORITHMS)}")


class HashGeneratorSkill(BaseSkill):
    name = "hash_generator"
    description = "哈希生成器：支持 MD5/SHA1/SHA256/SHA512/SHA3/BLAKE2 等算法"
    category = "coding"
    args_schema = HashGenSchema
    tags = ["hash", "哈希", "MD5", "SHA", "摘要"]

    async def execute(self, **kwargs: Any) -> str:
        text = kwargs.get("text", "")
        algo = kwargs.get("algorithm", "sha256").lower()

        if not text:
            return "请输入文本"

        if algo == "all":
            lines = [f"文本: {text[:50]}{'...' if len(text) > 50 else ''}\n"]
            for a in ALGORITHMS:
                try:
                    h = hashlib.new(a, text.encode("utf-8")).hexdigest()
                    lines.append(f"  {a.upper():>10}: {h}")
                except ValueError:
                    pass
            return "\n".join(lines)

        if algo not in ALGORITHMS:
            return f"不支持的算法: {algo}\n支持: {', '.join(ALGORITHMS)}"

        try:
            h = hashlib.new(algo, text.encode("utf-8")).hexdigest()
            return f"{algo.upper()} 哈希结果:\n{h}\n\n输入长度: {len(text)} 字符\n哈希长度: {len(h)} 字符 ({len(h)*4} bits)"
        except Exception as e:
            return f"哈希计算失败: {e}"
