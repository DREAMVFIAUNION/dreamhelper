"""视频缩放技能"""

import base64
import subprocess
import tempfile
import os

from typing import Literal
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class VideoResizeArgs(BaseModel):
    video_b64: str = Field(..., description="Base64 编码的视频数据")
    format: Literal["mp4", "avi", "mkv", "webm", "mov"] = Field("mp4", description="视频格式")
    width: int = Field(0, description="目标宽度, 0=按高度等比")
    height: int = Field(0, description="目标高度, 0=按宽度等比")
    preset: str = Field("", description="预设: 720p/1080p/480p/360p (覆盖 width/height)")


PRESETS = {
    "360p": (640, 360),
    "480p": (854, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
}


class VideoResizeSkill(BaseSkill):
    name = "video_resize"
    description = "缩放视频分辨率 — 支持预设和自定义尺寸"
    category = "video"
    tags = ["视频", "缩放", "resize", "分辨率"]
    args_schema = VideoResizeArgs

    async def execute(self, **kwargs) -> str:
        args = VideoResizeArgs(**kwargs)
        data = base64.b64decode(args.video_b64)

        if args.preset and args.preset in PRESETS:
            w, h = PRESETS[args.preset]
        elif args.width > 0 and args.height > 0:
            w, h = args.width, args.height
        elif args.width > 0:
            w, h = args.width, -2  # -2 = 保持比例且偶数
        elif args.height > 0:
            w, h = -2, args.height
        else:
            return "请指定 width/height 或 preset (360p/480p/720p/1080p)"

        with tempfile.NamedTemporaryFile(suffix=f".{args.format}", delete=False) as tmp:
            tmp.write(data)
            input_path = tmp.name

        out_path = input_path + f"_resized.{args.format}"

        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-i", input_path,
                    "-vf", f"scale={w}:{h}",
                    "-c:v", "libx264", "-preset", "fast",
                    "-c:a", "copy",
                    out_path,
                ],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0 or not os.path.exists(out_path):
                return f"缩放失败: {result.stderr[:200]}"

            with open(out_path, "rb") as f:
                out_b64 = base64.b64encode(f.read()).decode()

            out_size = os.path.getsize(out_path) / 1024
            target = args.preset if args.preset else f"{w}×{h}"

            return (
                f"✅ 视频缩放完成\n"
                f"目标: {target}\n"
                f"原始: {len(data) / 1024:.1f} KB → 结果: {out_size:.1f} KB\n"
                f"[BASE64_VIDEO]{out_b64}"
            )
        finally:
            for p in (input_path, out_path):
                if os.path.exists(p):
                    os.unlink(p)
