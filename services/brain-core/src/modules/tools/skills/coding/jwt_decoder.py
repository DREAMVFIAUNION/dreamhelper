"""JWT 解码器技能 — 解析 JWT token 结构（不验证签名）"""

import base64
import json
from typing import Any
from datetime import datetime, timezone

from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema


class JwtDecodeSchema(SkillSchema):
    token: str = Field(description="JWT token 字符串")


def _decode_part(part: str) -> dict:
    """Base64url 解码 JWT 段"""
    padding = 4 - len(part) % 4
    if padding != 4:
        part += "=" * padding
    decoded = base64.urlsafe_b64decode(part)
    return json.loads(decoded)


class JwtDecoderSkill(BaseSkill):
    name = "jwt_decoder"
    description = "JWT 解码器：解析 token 的 header、payload，显示过期时间等信息（不验证签名）"
    category = "coding"
    args_schema = JwtDecodeSchema
    tags = ["JWT", "token", "解码", "认证"]

    async def execute(self, **kwargs: Any) -> str:
        token = kwargs.get("token", "").strip()
        if not token:
            return "请输入 JWT token"

        parts = token.split(".")
        if len(parts) != 3:
            return f"无效 JWT: 应有 3 段 (header.payload.signature)，收到 {len(parts)} 段"

        try:
            header = _decode_part(parts[0])
            payload = _decode_part(parts[1])
        except Exception as e:
            return f"JWT 解码失败: {e}"

        lines = [
            "JWT 解码结果:\n",
            "Header:",
            json.dumps(header, indent=2, ensure_ascii=False),
            "\nPayload:",
            json.dumps(payload, indent=2, ensure_ascii=False),
            f"\nSignature: {parts[2][:20]}...",
        ]

        # 解析时间字段
        now_ts = datetime.now(timezone.utc).timestamp()
        for field, label in [("iat", "签发时间"), ("exp", "过期时间"), ("nbf", "生效时间")]:
            if field in payload:
                ts = payload[field]
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                status = ""
                if field == "exp":
                    status = " (已过期)" if ts < now_ts else f" (剩余 {int((ts - now_ts) / 60)} 分钟)"
                lines.append(f"\n{label}: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}{status}")

        if "sub" in payload:
            lines.append(f"Subject: {payload['sub']}")
        if "iss" in payload:
            lines.append(f"Issuer: {payload['iss']}")

        return "\n".join(lines)
