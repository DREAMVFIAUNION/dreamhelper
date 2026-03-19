"""视频转 GIF 技能 — 调色板法优化体积"""

import base64
import subprocess
import tempfile
import os

from typing import Literal
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class VideoToGifArgs(BaseModel):
    video_b64: str = Field(..., description="Base64 编码的视频数据")
    format: Literal["mp4", "avi", "mkv", "webm", "mov"] = Field("mp4", description="视频格式")
    fps: int = Field(10, description="GIF 帧率 (5-30)")
    width: int = Field(320, description="GIF 宽度 (px), -1=保持原始")
    start_s: float = Field(0, description="起始时间 (秒)")
    duration_s: float = Field(5, description="持续时长 (秒), 最大 15s")


class VideoToGifSkill(BaseSkill):
    name = "video_to_gif"
    description = "将视频转换为 GIF 动图 — 调色板法优化体积"
    category = "video"
    tags = ["视频", "GIF", "动图", "转换"]
    args_schema = VideoToGifArgs

    async def execute(self, **kwargs) -> str:
        args = VideoToGifArgs(**kwargs)
        data = base64.b64decode(args.video_b64)
        fps = max(5, min(30, args.fps))
        dur = max(1, min(15, args.duration_s))

        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, f"input.{args.format}")
        palette_path = os.path.join(tmp_dir, "palette.png")
        out_path = os.path.join(tmp_dir, "output.gif")

        with open(input_path, "wb") as f:
            f.write(data)

        try:
            vf_scale = f"fps={fps},scale={args.width}:-1:flags=lanczos"

            # 第一步: 生成调色板
            r1 = subprocess.run(
                [
                    "ffmpeg", "-y", "-ss", str(args.start_s), "-t", str(dur),
                    "-i", input_path,
                    "-vf", f"{vf_scale},palettegen=stats_mode=diff",
                    palette_path,
                ],
                capture_output=True, text=True, timeout=60,
            )
            if r1.returncode != 0:
                return f"调色板生成失败: {r1.stderr[:200]}"

            # 第二步: 用调色板生成 GIF
            r2 = subprocess.run(
                [
                    "ffmpeg", "-y", "-ss", str(args.start_s), "-t", str(dur),
                    "-i", input_path, "-i", palette_path,
                    "-lavfi", f"{vf_scale} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5",
                    out_path,
                ],
                capture_output=True, text=True, timeout=60,
            )
            if r2.returncode != 0 or not os.path.exists(out_path):
                return f"GIF 生成失败: {r2.stderr[:200]}"

            with open(out_path, "rb") as f:
                out_b64 = base64.b64encode(f.read()).decode()

            out_size = os.path.getsize(out_path) / 1024

            return (
                f"✅ GIF 生成完成\n"
                f"帧率: {fps} fps\n"
                f"宽度: {args.width}px\n"
                f"时长: {dur}s (从 {args.start_s}s 开始)\n"
                f"大小: {out_size:.1f} KB\n"
                f"[BASE64]{out_b64}"
            )
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
