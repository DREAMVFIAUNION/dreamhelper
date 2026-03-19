"""视频信息技能 — 通过 ffprobe 获取"""

import base64
import json
import subprocess
import tempfile
import os

from typing import Literal
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class VideoInfoArgs(BaseModel):
    video_b64: str = Field(..., description="Base64 编码的视频数据")
    format: Literal["mp4", "avi", "mkv", "webm", "mov"] = Field("mp4", description="视频格式: mp4/avi/mkv/webm/mov")


class VideoInfoSkill(BaseSkill):
    name = "video_info"
    description = "获取视频文件信息 — 时长/分辨率/编码/帧率/比特率"
    category = "video"
    tags = ["视频", "信息", "video", "info", "ffprobe"]
    args_schema = VideoInfoArgs

    async def execute(self, **kwargs) -> str:
        args = VideoInfoArgs(**kwargs)
        data = base64.b64decode(args.video_b64)

        with tempfile.NamedTemporaryFile(suffix=f".{args.format}", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-print_format", "json",
                    "-show_format", "-show_streams",
                    tmp_path,
                ],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return f"ffprobe 执行失败: {result.stderr[:200]}"

            info = json.loads(result.stdout)
            fmt = info.get("format", {})
            streams = info.get("streams", [])

            lines = [f"🎬 视频信息"]
            lines.append(f"文件大小: {len(data) / 1024:.1f} KB")
            lines.append(f"时长: {float(fmt.get('duration', 0)):.2f}s")
            lines.append(f"比特率: {int(fmt.get('bit_rate', 0)) // 1000} kbps")
            lines.append(f"格式: {fmt.get('format_long_name', 'N/A')}")

            for s in streams:
                codec_type = s.get("codec_type", "")
                if codec_type == "video":
                    lines.append(f"\n— 视频流 —")
                    lines.append(f"  编码: {s.get('codec_name', 'N/A')}")
                    lines.append(f"  分辨率: {s.get('width')}×{s.get('height')}")
                    lines.append(f"  帧率: {s.get('r_frame_rate', 'N/A')}")
                    lines.append(f"  像素格式: {s.get('pix_fmt', 'N/A')}")
                elif codec_type == "audio":
                    lines.append(f"\n— 音频流 —")
                    lines.append(f"  编码: {s.get('codec_name', 'N/A')}")
                    lines.append(f"  采样率: {s.get('sample_rate', 'N/A')} Hz")
                    lines.append(f"  声道: {s.get('channels', 'N/A')}")

            return "\n".join(lines)
        finally:
            os.unlink(tmp_path)
