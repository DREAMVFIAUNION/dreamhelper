"""音频合并技能"""

import base64
import io

from pydub import AudioSegment
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class AudioMergeArgs(BaseModel):
    audios_b64: list[str] = Field(..., description="Base64 编码的音频列表 (2-10个)")
    format: str = Field("mp3", description="音频格式")
    crossfade_ms: int = Field(0, description="交叉淡入淡出时长 (毫秒), 0=无")
    gap_ms: int = Field(0, description="片段间静音间隔 (毫秒)")


class AudioMergeSkill(BaseSkill):
    name = "audio_merge"
    description = "合并多段音频 — 支持交叉淡入淡出和间隔"
    category = "audio"
    tags = ["音频", "合并", "merge", "拼接"]
    args_schema = AudioMergeArgs

    async def execute(self, **kwargs) -> str:
        args = AudioMergeArgs(**kwargs)
        if len(args.audios_b64) < 2:
            return "至少需要 2 段音频"
        if len(args.audios_b64) > 10:
            return "最多支持 10 段音频"

        segments = []
        for b64 in args.audios_b64:
            data = base64.b64decode(b64)
            seg = AudioSegment.from_file(io.BytesIO(data), format=args.format)
            segments.append(seg)

        result = segments[0]
        for seg in segments[1:]:
            if args.gap_ms > 0:
                result += AudioSegment.silent(duration=args.gap_ms)
            if args.crossfade_ms > 0:
                max_cf = min(len(result), len(seg), args.crossfade_ms)
                result = result.append(seg, crossfade=max_cf)
            else:
                result += seg

        buf = io.BytesIO()
        result.export(buf, format=args.format)
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        durations = [f"{len(s) / 1000:.1f}s" for s in segments]
        return (
            f"✅ 合并完成\n"
            f"片段数: {len(segments)}\n"
            f"各段时长: {', '.join(durations)}\n"
            f"总时长: {len(result) / 1000:.1f}s\n"
            f"交叉淡入: {args.crossfade_ms}ms\n"
            f"[BASE64_AUDIO]{out_b64}"
        )
