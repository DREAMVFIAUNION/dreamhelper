"""音频静音检测技能"""

import base64
import io

from pydub import AudioSegment
from pydub.silence import detect_silence
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class AudioSilenceDetectArgs(BaseModel):
    audio_b64: str = Field(..., description="Base64 编码的音频数据")
    format: str = Field("mp3", description="音频格式")
    silence_thresh: int = Field(-40, description="静音阈值 dBFS")
    min_silence_ms: int = Field(500, description="最短静音时长 (毫秒)")


class AudioSilenceDetectSkill(BaseSkill):
    name = "audio_silence_detect"
    description = "检测音频中的静音段"
    category = "audio"
    tags = ["音频", "静音", "检测", "silence"]
    args_schema = AudioSilenceDetectArgs

    async def execute(self, **kwargs) -> str:
        args = AudioSilenceDetectArgs(**kwargs)
        data = base64.b64decode(args.audio_b64)
        audio = AudioSegment.from_file(io.BytesIO(data), format=args.format)
        total_ms = len(audio)

        silent_ranges = detect_silence(
            audio,
            min_silence_len=args.min_silence_ms,
            silence_thresh=args.silence_thresh,
        )

        lines = [
            f"🔇 静音检测结果",
            f"总时长: {total_ms / 1000:.1f}s",
            f"阈值: {args.silence_thresh} dBFS",
            f"最短静音: {args.min_silence_ms}ms",
            f"检测到: {len(silent_ranges)} 段静音",
            "",
        ]

        total_silence_ms = 0
        for i, (start, end) in enumerate(silent_ranges):
            dur = end - start
            total_silence_ms += dur
            lines.append(
                f"  {i + 1}. {start / 1000:.2f}s - {end / 1000:.2f}s ({dur}ms)"
            )

        if silent_ranges:
            pct = total_silence_ms / total_ms * 100 if total_ms > 0 else 0
            lines.append("")
            lines.append(f"静音总时长: {total_silence_ms / 1000:.1f}s ({pct:.1f}%)")

        return "\n".join(lines)
