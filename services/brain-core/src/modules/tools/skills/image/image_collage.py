"""图像拼接技能"""

import base64
import io
import math

from PIL import Image
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class ImageCollageArgs(BaseModel):
    images_b64: list[str] = Field(..., description="Base64 编码的图像列表 (2-20张)")
    layout: str = Field("grid", description="布局: grid/horizontal/vertical")
    cell_size: int = Field(300, description="每个单元格边长 (px)")
    gap: int = Field(4, description="间距 (px)")
    bg_color: str = Field("#000000", description="背景色 (hex)")


class ImageCollageSkill(BaseSkill):
    name = "image_collage"
    description = "拼接多张图像 — 支持网格/横排/竖排布局"
    category = "image"
    tags = ["图像", "拼接", "collage", "拼图", "组合"]
    args_schema = ImageCollageArgs

    async def execute(self, **kwargs) -> str:
        args = ImageCollageArgs(**kwargs)
        if len(args.images_b64) < 2:
            return "至少需要 2 张图像"
        if len(args.images_b64) > 20:
            return "最多支持 20 张图像"

        imgs = []
        for b64 in args.images_b64:
            data = base64.b64decode(b64)
            img = Image.open(io.BytesIO(data))
            img.thumbnail((args.cell_size, args.cell_size), Image.LANCZOS)
            imgs.append(img)

        n = len(imgs)
        gap = args.gap
        hex_bg = args.bg_color.lstrip("#")
        bg = tuple(int(hex_bg[i:i+2], 16) for i in (0, 2, 4))

        if args.layout == "horizontal":
            total_w = sum(im.width for im in imgs) + gap * (n - 1)
            max_h = max(im.height for im in imgs)
            canvas = Image.new("RGB", (total_w, max_h), bg)
            x = 0
            for im in imgs:
                y_off = (max_h - im.height) // 2
                canvas.paste(im, (x, y_off))
                x += im.width + gap
        elif args.layout == "vertical":
            max_w = max(im.width for im in imgs)
            total_h = sum(im.height for im in imgs) + gap * (n - 1)
            canvas = Image.new("RGB", (max_w, total_h), bg)
            y = 0
            for im in imgs:
                x_off = (max_w - im.width) // 2
                canvas.paste(im, (x_off, y))
                y += im.height + gap
        else:
            # grid
            cols = math.ceil(math.sqrt(n))
            rows = math.ceil(n / cols)
            canvas_w = cols * args.cell_size + (cols - 1) * gap
            canvas_h = rows * args.cell_size + (rows - 1) * gap
            canvas = Image.new("RGB", (canvas_w, canvas_h), bg)
            for idx, im in enumerate(imgs):
                r, c = divmod(idx, cols)
                x = c * (args.cell_size + gap) + (args.cell_size - im.width) // 2
                y = r * (args.cell_size + gap) + (args.cell_size - im.height) // 2
                canvas.paste(im, (x, y))

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 拼接完成\n"
            f"图片数: {n}\n"
            f"布局: {args.layout}\n"
            f"画布尺寸: {canvas.width}×{canvas.height}\n"
            f"[BASE64]{out_b64}"
        )
