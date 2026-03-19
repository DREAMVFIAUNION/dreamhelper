"""图像缩放技能"""

import base64
import io
from typing import Optional

from PIL import Image
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class ImageResizeArgs(BaseModel):
    image_b64: str = Field(..., description="Base64 编码的图像数据")
    width: Optional[int] = Field(None, description="目标宽度 (px)")
    height: Optional[int] = Field(None, description="目标高度 (px)")
    scale: Optional[float] = Field(None, description="缩放比例 (0.1-10.0)")
    keep_aspect: bool = Field(True, description="保持宽高比")
    resample: str = Field("lanczos", description="重采样算法: nearest/bilinear/bicubic/lanczos")


RESAMPLE_MAP = {
    "nearest": Image.NEAREST,
    "bilinear": Image.BILINEAR,
    "bicubic": Image.BICUBIC,
    "lanczos": Image.LANCZOS,
}


class ImageResizeSkill(BaseSkill):
    name = "image_resize"
    description = "缩放图像到指定尺寸或比例"
    category = "image"
    tags = ["图像", "缩放", "resize", "尺寸"]
    args_schema = ImageResizeArgs

    async def execute(self, **kwargs) -> str:
        args = ImageResizeArgs(**kwargs)
        img_data = base64.b64decode(args.image_b64)
        img = Image.open(io.BytesIO(img_data))
        orig_w, orig_h = img.size

        resample = RESAMPLE_MAP.get(args.resample, Image.LANCZOS)

        if args.scale:
            new_w = int(orig_w * args.scale)
            new_h = int(orig_h * args.scale)
        elif args.width and args.height:
            if args.keep_aspect:
                ratio = min(args.width / orig_w, args.height / orig_h)
                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)
            else:
                new_w, new_h = args.width, args.height
        elif args.width:
            ratio = args.width / orig_w
            new_w = args.width
            new_h = int(orig_h * ratio) if args.keep_aspect else orig_h
        elif args.height:
            ratio = args.height / orig_h
            new_h = args.height
            new_w = int(orig_w * ratio) if args.keep_aspect else orig_w
        else:
            return "请指定 width/height 或 scale"

        result = img.resize((new_w, new_h), resample)
        buf = io.BytesIO()
        fmt = img.format or "PNG"
        result.save(buf, format=fmt)
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 缩放完成\n"
            f"原始尺寸: {orig_w}×{orig_h}\n"
            f"目标尺寸: {new_w}×{new_h}\n"
            f"格式: {fmt}\n"
            f"[BASE64]{out_b64}"
        )
