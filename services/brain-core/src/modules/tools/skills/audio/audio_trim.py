"""音频裁剪技能"""

import base64
import io

from pydub import AudioSegment
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class AudioTrimArgs(BaseModel):
    audio_b64: str = Field(..., description="Base64 编码的音频数据")
    format: str = Field("mp3", description="音频格式")
    start_ms: int = Field(0, description="起始时间 (毫秒)")
    end_ms: int = Field(0, description="结束时间 (毫秒), 0=到末尾")


class AudioTrimSkill(BaseSkill):
    name = "audio_trim"
    description = "裁剪音频片段 — 指定起止时间"
    category = "audio"
    tags = ["音频", "裁剪", "trim", "剪切"]
    args_schema = AudioTrimArgs

    async def execute(self, **kwargs) -> str:
        args = AudioTrimArgs(**kwargs)
        data = base64.b64decode(args.audio_b64)
        audio = AudioSegment.from_file(io.BytesIO(data), format=args.format)
        total = len(audio)

        start = max(0, args.start_ms)
        end = args.end_ms if args.end_ms > 0 else total
        end = min(end, total)

        if start >= end:
            return f"无效的时间范围: {start}ms - {end}ms (总时长: {total}ms)"

        trimmed = audio[start:end]
        buf = io.BytesIO()
        trimmed.export(buf, format=args.format)
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 裁剪完成\n"
            f"原时长: {total / 1000:.1f}s\n"
            f"裁剪范围: {start / 1000:.1f}s - {end / 1000:.1f}s\n"
            f"结果时长: {len(trimmed) / 1000:.1f}s\n"
            f"[BASE64_AUDIO]{out_b64}"
        )
