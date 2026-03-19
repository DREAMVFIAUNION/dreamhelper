"""图像格式转换技能"""

import base64
import io

from PIL import Image
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill

SUPPORTED_FORMATS = {"PNG", "JPEG", "WEBP", "BMP", "GIF", "TIFF", "ICO"}


class ImageFormatConvertArgs(BaseModel):
    image_b64: str = Field(..., description="Base64 编码的图像数据")
    target_format: str = Field(..., description="目标格式: PNG/JPEG/WEBP/BMP/GIF/TIFF/ICO")
    quality: int = Field(85, description="输出质量 (仅 JPEG/WEBP 有效) 1-100")


class ImageFormatConvertSkill(BaseSkill):
    name = "image_format_convert"
    description = "转换图像格式 — 支持 PNG/JPEG/WEBP/BMP/GIF/TIFF/ICO"
    category = "image"
    tags = ["图像", "格式", "转换", "convert", "PNG", "JPEG", "WEBP"]
    args_schema = ImageFormatConvertArgs

    async def execute(self, **kwargs) -> str:
        args = ImageFormatConvertArgs(**kwargs)
        fmt = args.target_format.upper()
        if fmt == "JPG":
            fmt = "JPEG"
        if fmt not in SUPPORTED_FORMATS:
            return f"不支持的格式: {args.target_format}，支持: {', '.join(sorted(SUPPORTED_FORMATS))}"

        img_data = base64.b64decode(args.image_b64)
        orig_size = len(img_data)
        img = Image.open(io.BytesIO(img_data))
        src_fmt = img.format or "UNKNOWN"

        # JPEG 不支持 alpha
        if fmt == "JPEG" and img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        # ICO 需要限制尺寸
        if fmt == "ICO":
            if img.width > 256 or img.height > 256:
                img.thumbnail((256, 256), Image.LANCZOS)

        buf = io.BytesIO()
        save_kwargs = {}
        if fmt in ("JPEG", "WEBP"):
            save_kwargs["quality"] = args.quality
        if fmt == "PNG":
            save_kwargs["optimize"] = True

        img.save(buf, format=fmt, **save_kwargs)
        out_data = buf.getvalue()
        out_b64 = base64.b64encode(out_data).decode()

        return (
            f"✅ 格式转换完成\n"
            f"原格式: {src_fmt} ({orig_size / 1024:.1f} KB)\n"
            f"目标格式: {fmt} ({len(out_data) / 1024:.1f} KB)\n"
            f"尺寸: {img.width}×{img.height}\n"
            f"[BASE64]{out_b64}"
        )
