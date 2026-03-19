"""视频合并技能 — concat demuxer"""

import base64
import subprocess
import tempfile
import os

from typing import Literal
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class VideoMergeArgs(BaseModel):
    videos_b64: list[str] = Field(..., description="Base64 编码的视频列表 (2-10个)")
    format: Literal["mp4", "avi", "mkv", "webm", "mov"] = Field("mp4", description="视频格式")


class VideoMergeSkill(BaseSkill):
    name = "video_merge"
    description = "合并多段视频 — concat 拼接"
    category = "video"
    tags = ["视频", "合并", "merge", "拼接"]
    args_schema = VideoMergeArgs

    async def execute(self, **kwargs) -> str:
        args = VideoMergeArgs(**kwargs)
        if len(args.videos_b64) < 2:
            return "至少需要 2 段视频"
        if len(args.videos_b64) > 10:
            return "最多支持 10 段视频"

        tmp_dir = tempfile.mkdtemp()
        input_paths = []

        try:
            # 写入临时文件
            for i, b64 in enumerate(args.videos_b64):
                path = os.path.join(tmp_dir, f"input_{i}.{args.format}")
                with open(path, "wb") as f:
                    f.write(base64.b64decode(b64))
                input_paths.append(path)

            # 创建 concat 文件
            list_path = os.path.join(tmp_dir, "list.txt")
            with open(list_path, "w") as f:
                for p in input_paths:
                    f.write(f"file '{p}'\n")

            out_path = os.path.join(tmp_dir, f"merged.{args.format}")

            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", list_path, "-c", "copy", out_path,
                ],
                capture_output=True, text=True, timeout=120,
            )

            if result.returncode != 0 or not os.path.exists(out_path):
                return f"合并失败: {result.stderr[:200]}"

            with open(out_path, "rb") as f:
                out_b64 = base64.b64encode(f.read()).decode()

            out_size = os.path.getsize(out_path) / 1024

            return (
                f"✅ 视频合并完成\n"
                f"片段数: {len(args.videos_b64)}\n"
                f"结果大小: {out_size:.1f} KB\n"
                f"[BASE64_VIDEO]{out_b64}"
            )
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
