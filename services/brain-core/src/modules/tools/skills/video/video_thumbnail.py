"""视频截图技能 — 提取单帧或网格缩略图"""

import base64
import subprocess
import tempfile
import os

from typing import Literal
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class VideoThumbnailArgs(BaseModel):
    video_b64: str = Field(..., description="Base64 编码的视频数据")
    format: Literal["mp4", "avi", "mkv", "webm", "mov"] = Field("mp4", description="视频格式")
    time_s: float = Field(1.0, description="截图时间点 (秒)")
    grid: str = Field("", description="网格模式, 如 '3x3' 表示 3 行 3 列, 留空=单帧")


class VideoThumbnailSkill(BaseSkill):
    name = "video_thumbnail"
    description = "从视频提取缩略图 — 单帧截图或网格预览"
    category = "video"
    tags = ["视频", "截图", "缩略图", "thumbnail", "预览"]
    args_schema = VideoThumbnailArgs

    async def execute(self, **kwargs) -> str:
        args = VideoThumbnailArgs(**kwargs)
        data = base64.b64decode(args.video_b64)

        with tempfile.NamedTemporaryFile(suffix=f".{args.format}", delete=False) as tmp:
            tmp.write(data)
            input_path = tmp.name

        out_path = input_path + "_thumb.png"

        try:
            if args.grid:
                # 网格缩略图
                parts = args.grid.split("x")
                cols = int(parts[0]) if len(parts) >= 1 else 3
                rows = int(parts[1]) if len(parts) >= 2 else 3
                total = cols * rows
                cmd = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-vf", f"select='not(mod(n\\,{max(1, 30)}))',scale=320:-1,tile={cols}x{rows}",
                    "-frames:v", "1",
                    "-vsync", "vfr",
                    out_path,
                ]
                mode = f"网格 {cols}×{rows}"
            else:
                # 单帧截图
                cmd = [
                    "ffmpeg", "-y", "-ss", str(args.time_s),
                    "-i", input_path,
                    "-frames:v", "1",
                    "-q:v", "2",
                    out_path,
                ]
                mode = f"单帧 @{args.time_s}s"

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0 or not os.path.exists(out_path):
                return f"截图失败: {result.stderr[:200]}"

            with open(out_path, "rb") as f:
                out_b64 = base64.b64encode(f.read()).decode()

            size_kb = os.path.getsize(out_path) / 1024

            return (
                f"✅ 视频截图完成\n"
                f"模式: {mode}\n"
                f"大小: {size_kb:.1f} KB\n"
                f"[BASE64]{out_b64}"
            )
        finally:
            for p in (input_path, out_path):
                if os.path.exists(p):
                    os.unlink(p)
