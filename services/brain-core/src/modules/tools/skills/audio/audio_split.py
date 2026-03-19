"""音频分割技能"""

import base64
import io

from pydub import AudioSegment
from pydub.silence import detect_silence
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class AudioSplitArgs(BaseModel):
    audio_b64: str = Field(..., description="Base64 编码的音频数据")
    format: str = Field("mp3", description="音频格式")
    method: str = Field("duration", description="分割方式: duration(按时长) / silence(按静音)")
    chunk_ms: int = Field(30000, description="每段时长 (毫秒), 仅 duration 模式")
    silence_thresh: int = Field(-40, description="静音阈值 dBFS, 仅 silence 模式")
    min_silence_ms: int = Field(500, description="最短静音时长 (毫秒), 仅 silence 模式")


class AudioSplitSkill(BaseSkill):
    name = "audio_split"
    description = "分割音频 — 按时长或按静音段分割"
    category = "audio"
    tags = ["音频", "分割", "split", "切分"]
    args_schema = AudioSplitArgs

    async def execute(self, **kwargs) -> str:
        args = AudioSplitArgs(**kwargs)
        data = base64.b64decode(args.audio_b64)
        audio = AudioSegment.from_file(io.BytesIO(data), format=args.format)
        total_ms = len(audio)

        chunks: list[AudioSegment] = []

        if args.method == "silence":
            silent_ranges = detect_silence(
                audio,
                min_silence_len=args.min_silence_ms,
                silence_thresh=args.silence_thresh,
            )
            if not silent_ranges:
                chunks = [audio]
            else:
                start = 0
                for s_start, s_end in silent_ranges:
                    mid = (s_start + s_end) // 2
                    if mid > start:
                        chunks.append(audio[start:mid])
                    start = mid
                if start < total_ms:
                    chunks.append(audio[start:])
        else:
            # duration 模式
            for i in range(0, total_ms, args.chunk_ms):
                chunks.append(audio[i:i + args.chunk_ms])

        # 导出每个片段
        results = []
        for i, chunk in enumerate(chunks):
            buf = io.BytesIO()
            chunk.export(buf, format=args.format)
            b64 = base64.b64encode(buf.getvalue()).decode()
            results.append(b64)

        lines = [
            f"✅ 分割完成",
            f"方式: {args.method}",
            f"原时长: {total_ms / 1000:.1f}s",
            f"片段数: {len(chunks)}",
            "",
        ]
        for i, chunk in enumerate(chunks):
            lines.append(f"  片段 {i + 1}: {len(chunk) / 1000:.1f}s")

        lines.append("")
        for i, b64 in enumerate(results):
            lines.append(f"[BASE64_AUDIO_{i + 1}]{b64}")

        return "\n".join(lines)
