"""音频信息技能"""

import base64
import io

from pydub import AudioSegment
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class AudioInfoArgs(BaseModel):
    audio_b64: str = Field(..., description="Base64 编码的音频数据")
    format: str = Field("mp3", description="音频格式: mp3/wav/ogg/flac")


class AudioInfoSkill(BaseSkill):
    name = "audio_info"
    description = "获取音频文件信息 — 时长/采样率/声道/比特率"
    category = "audio"
    tags = ["音频", "信息", "audio", "info", "时长"]
    args_schema = AudioInfoArgs

    async def execute(self, **kwargs) -> str:
        args = AudioInfoArgs(**kwargs)
        data = base64.b64decode(args.audio_b64)
        audio = AudioSegment.from_file(io.BytesIO(data), format=args.format)

        duration_ms = len(audio)
        duration_s = duration_ms / 1000
        minutes = int(duration_s // 60)
        seconds = duration_s % 60

        size_kb = len(data) / 1024
        bitrate = (len(data) * 8) / duration_s / 1000 if duration_s > 0 else 0

        return (
            f"🎵 音频信息\n"
            f"时长: {minutes}:{seconds:05.2f}\n"
            f"采样率: {audio.frame_rate} Hz\n"
            f"声道: {audio.channels} ({'立体声' if audio.channels == 2 else '单声道'})\n"
            f"位深度: {audio.sample_width * 8} bit\n"
            f"比特率: ~{bitrate:.0f} kbps\n"
            f"文件大小: {size_kb:.1f} KB\n"
            f"帧数: {audio.frame_count():.0f}"
        )
