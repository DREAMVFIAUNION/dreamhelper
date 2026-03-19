"""音频格式转换技能"""

import base64
import io

from pydub import AudioSegment
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill

SUPPORTED = {"mp3", "wav", "ogg", "flac", "aac", "webm"}


class AudioConvertArgs(BaseModel):
    audio_b64: str = Field(..., description="Base64 编码的音频数据")
    source_format: str = Field("mp3", description="源格式: mp3/wav/ogg/flac/aac/webm")
    target_format: str = Field("wav", description="目标格式: mp3/wav/ogg/flac/aac")
    bitrate: str = Field("192k", description="输出比特率 (仅有损格式有效)")


class AudioConvertSkill(BaseSkill):
    name = "audio_convert"
    description = "转换音频格式 — 支持 MP3/WAV/OGG/FLAC/AAC"
    category = "audio"
    tags = ["音频", "转换", "convert", "格式"]
    args_schema = AudioConvertArgs

    async def execute(self, **kwargs) -> str:
        args = AudioConvertArgs(**kwargs)
        if args.target_format not in SUPPORTED:
            return f"不支持的格式: {args.target_format}，支持: {', '.join(sorted(SUPPORTED))}"

        data = base64.b64decode(args.audio_b64)
        orig_size = len(data)
        audio = AudioSegment.from_file(io.BytesIO(data), format=args.source_format)

        buf = io.BytesIO()
        export_params = {}
        if args.target_format in ("mp3", "aac", "ogg"):
            export_params["bitrate"] = args.bitrate

        audio.export(buf, format=args.target_format, **export_params)
        out_data = buf.getvalue()
        out_b64 = base64.b64encode(out_data).decode()

        return (
            f"✅ 格式转换完成\n"
            f"源格式: {args.source_format} ({orig_size / 1024:.1f} KB)\n"
            f"目标格式: {args.target_format} ({len(out_data) / 1024:.1f} KB)\n"
            f"时长: {len(audio) / 1000:.1f}s\n"
            f"[BASE64_AUDIO]{out_b64}"
        )
