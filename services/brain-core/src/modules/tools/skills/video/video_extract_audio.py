"""视频提取音频技能"""

import base64
import subprocess
import tempfile
import os

from typing import Literal
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class VideoExtractAudioArgs(BaseModel):
    video_b64: str = Field(..., description="Base64 编码的视频数据")
    format: Literal["mp4", "avi", "mkv", "webm", "mov"] = Field("mp4", description="视频格式")
    audio_format: Literal["mp3", "wav", "aac", "ogg"] = Field("mp3", description="输出音频格式: mp3/wav/aac/ogg")
    bitrate: str = Field("192k", description="音频比特率")


class VideoExtractAudioSkill(BaseSkill):
    name = "video_extract_audio"
    description = "从视频中提取音频轨道"
    category = "video"
    tags = ["视频", "音频", "提取", "extract", "audio"]
    args_schema = VideoExtractAudioArgs

    async def execute(self, **kwargs) -> str:
        args = VideoExtractAudioArgs(**kwargs)
        data = base64.b64decode(args.video_b64)

        with tempfile.NamedTemporaryFile(suffix=f".{args.format}", delete=False) as tmp:
            tmp.write(data)
            input_path = tmp.name

        out_path = input_path + f"_audio.{args.audio_format}"

        try:
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-vn",  # 去掉视频
                "-ab", args.bitrate,
            ]
            if args.audio_format == "mp3":
                cmd += ["-acodec", "libmp3lame"]
            elif args.audio_format == "aac":
                cmd += ["-acodec", "aac"]
            elif args.audio_format == "ogg":
                cmd += ["-acodec", "libvorbis"]
            # wav 无需指定编码

            cmd.append(out_path)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0 or not os.path.exists(out_path):
                return f"提取失败: {result.stderr[:200]}"

            with open(out_path, "rb") as f:
                out_b64 = base64.b64encode(f.read()).decode()

            out_size = os.path.getsize(out_path) / 1024

            return (
                f"✅ 音频提取完成\n"
                f"格式: {args.audio_format}\n"
                f"比特率: {args.bitrate}\n"
                f"大小: {out_size:.1f} KB\n"
                f"[BASE64_AUDIO]{out_b64}"
            )
        finally:
            for p in (input_path, out_path):
                if os.path.exists(p):
                    os.unlink(p)
