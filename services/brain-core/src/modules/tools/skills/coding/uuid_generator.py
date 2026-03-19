"""UUID 生成器技能 — 支持 v1/v4/v5"""

import uuid
from typing import Any

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class UuidGenSchema(SkillSchema):
    version: int = Field(default=4, description="UUID 版本: 1(时间), 4(随机), 5(命名空间+SHA1)")
    count: int = Field(default=1, description="生成数量，1-10")
    name: str = Field(default="", description="命名 (version=5 时使用)")
    namespace: str = Field(default="dns", description="命名空间: dns/url/oid/x500 (version=5)")


_NS = {
    "dns": uuid.NAMESPACE_DNS,
    "url": uuid.NAMESPACE_URL,
    "oid": uuid.NAMESPACE_OID,
    "x500": uuid.NAMESPACE_X500,
}


class UuidGeneratorSkill(BaseSkill):
    name = "uuid_generator"
    description = "UUID 生成器：支持 v1(时间)、v4(随机)、v5(命名空间) 版本"
    category = "coding"
    args_schema = UuidGenSchema
    tags = ["UUID", "唯一ID", "uuid", "guid"]

    async def execute(self, **kwargs: Any) -> str:
        version = int(kwargs.get("version", 4))
        count = max(1, min(10, int(kwargs.get("count", 1))))

        results = []
        for _ in range(count):
            if version == 1:
                results.append(str(uuid.uuid1()))
            elif version == 4:
                results.append(str(uuid.uuid4()))
            elif version == 5:
                name = kwargs.get("name", "example")
                ns_key = kwargs.get("namespace", "dns").lower()
                ns = _NS.get(ns_key, uuid.NAMESPACE_DNS)
                results.append(str(uuid.uuid5(ns, name)))
            else:
                return f"不支持的版本: v{version}，支持 v1/v4/v5"

        lines = [f"UUID v{version} ({count} 个):"]
        for i, u in enumerate(results, 1):
            lines.append(f"  {i}. {u}")

        if version == 1:
            lines.append("\n说明: v1 基于时间+MAC地址，含时间戳信息")
        elif version == 4:
            lines.append("\n说明: v4 完全随机，最常用")
        elif version == 5:
            lines.append(f"\n说明: v5 基于命名空间({kwargs.get('namespace', 'dns')})+名称({kwargs.get('name', '')})")

        return "\n".join(lines)
