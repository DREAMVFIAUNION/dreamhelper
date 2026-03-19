"""视频裁剪技能 — 无重编码快速切割"""

import base64
import subprocess
import tempfile
import os

from typing import Literal
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class VideoTrimArgs(BaseModel):
    video_b64: str = Field(..., description="Base64 编码的视频数据")
    format: Literal["mp4", "avi", "mkv", "webm", "mov"] = Field("mp4", description="视频格式")
    start_s: float = Field(0, description="起始时间 (秒)")
    end_s: float = Field(0, description="结束时间 (秒), 0=到末尾")
    reencode: bool = Field(False, description="是否重编码 (更精确但更慢)")


class VideoTrimSkill(BaseSkill):
    name = "video_trim"
    description = "裁剪视频片段 — 支持无重编码快速切割"
    category = "video"
    tags = ["视频", "裁剪", "trim", "剪切", "切割"]
    args_schema = VideoTrimArgs

    async def execute(self, **kwargs) -> str:
        args = VideoTrimArgs(**kwargs)
        data = base64.b64decode(args.video_b64)

        with tempfile.NamedTemporaryFile(suffix=f".{args.format}", delete=False) as tmp:
            tmp.write(data)
            input_path = tmp.name

        out_path = input_path + f"_trimmed.{args.format}"

        try:
            cmd = ["ffmpeg", "-y"]

            if not args.reencode:
                # 无重编码: -ss 放在 -i 前面更快
                cmd += ["-ss", str(args.start_s)]
                if args.end_s > 0:
                    cmd += ["-to", str(args.end_s - args.start_s)]
                cmd += ["-i", input_path, "-c", "copy", out_path]
            else:
                cmd += ["-i", input_path, "-ss", str(args.start_s)]
                if args.end_s > 0:
                    cmd += ["-to", str(args.end_s)]
                cmd += ["-c:v", "libx264", "-c:a", "aac", out_path]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0 or not os.path.exists(out_path):
                return f"裁剪失败: {result.stderr[:200]}"

            with open(out_path, "rb") as f:
                out_b64 = base64.b64encode(f.read()).decode()

            out_size = os.path.getsize(out_path) / 1024

            return (
                f"✅ 视频裁剪完成\n"
                f"范围: {args.start_s}s - {'末尾' if args.end_s <= 0 else f'{args.end_s}s'}\n"
                f"模式: {'重编码' if args.reencode else '无重编码(快速)'}\n"
                f"原始: {len(data) / 1024:.1f} KB → 结果: {out_size:.1f} KB\n"
                f"[BASE64_VIDEO]{out_b64}"
            )
        finally:
            for p in (input_path, out_path):
                if os.path.exists(p):
                    os.unlink(p)
