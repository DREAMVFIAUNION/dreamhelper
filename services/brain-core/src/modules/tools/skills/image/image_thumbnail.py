"""图像缩略图技能"""

import base64
import io

from PIL import Image
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class ImageThumbnailArgs(BaseModel):
    image_b64: str = Field(..., description="Base64 编码的图像数据")
    max_size: int = Field(200, description="缩略图最大边长 (px)")
    format: str = Field("PNG", description="输出格式: PNG/JPEG/WEBP")


class ImageThumbnailSkill(BaseSkill):
    name = "image_thumbnail"
    description = "生成图像缩略图 — 保持宽高比"
    category = "image"
    tags = ["图像", "缩略图", "thumbnail", "预览"]
    args_schema = ImageThumbnailArgs

    async def execute(self, **kwargs) -> str:
        args = ImageThumbnailArgs(**kwargs)
        img_data = base64.b64decode(args.image_b64)
        img = Image.open(io.BytesIO(img_data))
        orig_w, orig_h = img.size

        img.thumbnail((args.max_size, args.max_size), Image.LANCZOS)

        fmt = args.format.upper()
        if fmt == "JPG":
            fmt = "JPEG"
        if fmt == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format=fmt)
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 缩略图生成完成\n"
            f"原始尺寸: {orig_w}×{orig_h}\n"
            f"缩略图: {img.width}×{img.height}\n"
            f"格式: {fmt}\n"
            f"大小: {buf.tell() / 1024:.1f} KB\n"
            f"[BASE64]{out_b64}"
        )
