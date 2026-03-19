"""视频旋转技能"""

import base64
import subprocess
import tempfile
import os

from typing import Literal
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class VideoRotateArgs(BaseModel):
    video_b64: str = Field(..., description="Base64 编码的视频数据")
    format: Literal["mp4", "avi", "mkv", "webm", "mov"] = Field("mp4", description="视频格式")
    angle: int = Field(90, description="旋转角度: 90/180/270")
    flip: str = Field("", description="翻转: hflip(水平)/vflip(垂直), 留空=不翻转")


TRANSPOSE_MAP = {
    90: "transpose=1",    # 顺时针90
    180: "transpose=1,transpose=1",  # 180
    270: "transpose=2",   # 逆时针90
}


class VideoRotateSkill(BaseSkill):
    name = "video_rotate"
    description = "旋转视频 — 支持 90°/180°/270° 和水平/垂直翻转"
    category = "video"
    tags = ["视频", "旋转", "rotate", "翻转"]
    args_schema = VideoRotateArgs

    async def execute(self, **kwargs) -> str:
        args = VideoRotateArgs(**kwargs)
        data = base64.b64decode(args.video_b64)

        filters = []
        if args.angle in TRANSPOSE_MAP:
            filters.append(TRANSPOSE_MAP[args.angle])
        if args.flip == "hflip":
            filters.append("hflip")
        elif args.flip == "vflip":
            filters.append("vflip")

        if not filters:
            return "请指定旋转角度 (90/180/270) 或翻转 (hflip/vflip)"

        vf = ",".join(filters)

        with tempfile.NamedTemporaryFile(suffix=f".{args.format}", delete=False) as tmp:
            tmp.write(data)
            input_path = tmp.name

        out_path = input_path + f"_rotated.{args.format}"

        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-i", input_path,
                    "-vf", vf,
                    "-c:v", "libx264", "-preset", "fast",
                    "-c:a", "copy",
                    out_path,
                ],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0 or not os.path.exists(out_path):
                return f"旋转失败: {result.stderr[:200]}"

            with open(out_path, "rb") as f:
                out_b64 = base64.b64encode(f.read()).decode()

            out_size = os.path.getsize(out_path) / 1024
            desc = f"{args.angle}°" if args.angle in TRANSPOSE_MAP else ""
            if args.flip:
                desc += f" + {args.flip}"

            return (
                f"✅ 视频旋转完成\n"
                f"操作: {desc.strip()}\n"
                f"大小: {out_size:.1f} KB\n"
                f"[BASE64_VIDEO]{out_b64}"
            )
        finally:
            for p in (input_path, out_path):
                if os.path.exists(p):
                    os.unlink(p)
