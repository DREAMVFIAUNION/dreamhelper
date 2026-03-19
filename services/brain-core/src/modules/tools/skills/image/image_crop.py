"""图像裁剪技能"""

import base64
import io
from typing import Optional

from PIL import Image
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class ImageCropArgs(BaseModel):
    image_b64: str = Field(..., description="Base64 编码的图像数据")
    left: Optional[int] = Field(None, description="左边界 (px)")
    top: Optional[int] = Field(None, description="上边界 (px)")
    right: Optional[int] = Field(None, description="右边界 (px)")
    bottom: Optional[int] = Field(None, description="下边界 (px)")
    center_width: Optional[int] = Field(None, description="从中心裁剪的宽度")
    center_height: Optional[int] = Field(None, description="从中心裁剪的高度")
    ratio: Optional[str] = Field(None, description="宽高比裁剪, 如 '16:9', '1:1', '4:3'")


class ImageCropSkill(BaseSkill):
    name = "image_crop"
    description = "裁剪图像 — 支持坐标裁剪、中心裁剪、比例裁剪"
    category = "image"
    tags = ["图像", "裁剪", "crop", "切割"]
    args_schema = ImageCropArgs

    async def execute(self, **kwargs) -> str:
        args = ImageCropArgs(**kwargs)
        img_data = base64.b64decode(args.image_b64)
        img = Image.open(io.BytesIO(img_data))
        w, h = img.size

        if args.ratio:
            rw, rh = map(int, args.ratio.split(":"))
            target_ratio = rw / rh
            current_ratio = w / h
            if current_ratio > target_ratio:
                new_w = int(h * target_ratio)
                left = (w - new_w) // 2
                box = (left, 0, left + new_w, h)
            else:
                new_h = int(w / target_ratio)
                top = (h - new_h) // 2
                box = (0, top, w, top + new_h)
        elif args.center_width and args.center_height:
            cw = min(args.center_width, w)
            ch = min(args.center_height, h)
            left = (w - cw) // 2
            top = (h - ch) // 2
            box = (left, top, left + cw, top + ch)
        elif args.left is not None and args.top is not None and args.right is not None and args.bottom is not None:
            box = (
                max(0, args.left),
                max(0, args.top),
                min(w, args.right),
                min(h, args.bottom),
            )
        else:
            return "请指定裁剪参数: left/top/right/bottom 或 center_width/center_height 或 ratio"

        result = img.crop(box)
        buf = io.BytesIO()
        fmt = img.format or "PNG"
        result.save(buf, format=fmt)
        out_b64 = base64.b64encode(buf.getvalue()).decode()
        rw, rh = result.size

        return (
            f"✅ 裁剪完成\n"
            f"原始尺寸: {w}×{h}\n"
            f"裁剪区域: {box}\n"
            f"结果尺寸: {rw}×{rh}\n"
            f"[BASE64]{out_b64}"
        )
