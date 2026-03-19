"""图像水印技能"""

import base64
import io

from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class ImageWatermarkArgs(BaseModel):
    image_b64: str = Field(..., description="Base64 编码的图像数据")
    text: str = Field(..., description="水印文字")
    position: str = Field("bottom-right", description="位置: center/top-left/top-right/bottom-left/bottom-right/tile")
    opacity: int = Field(80, description="不透明度 0-255")
    font_size: int = Field(24, description="字体大小")
    color: str = Field("#FFFFFF", description="文字颜色 (hex)")


class ImageWatermarkSkill(BaseSkill):
    name = "image_watermark"
    description = "为图像添加文字水印 — 支持定位/平铺/透明度"
    category = "image"
    tags = ["图像", "水印", "watermark", "版权"]
    args_schema = ImageWatermarkArgs

    async def execute(self, **kwargs) -> str:
        args = ImageWatermarkArgs(**kwargs)
        img_data = base64.b64decode(args.image_b64)
        img = Image.open(io.BytesIO(img_data)).convert("RGBA")
        w, h = img.size

        hex_color = args.color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        fill = (r, g, b, args.opacity)

        # 创建水印层
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        try:
            font = ImageFont.truetype("arial.ttf", args.font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), args.text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        if args.position == "tile":
            # 平铺水印
            spacing_x = tw + 60
            spacing_y = th + 60
            y = 10
            while y < h:
                x = 10
                while x < w:
                    draw.text((x, y), args.text, font=font, fill=fill)
                    x += spacing_x
                y += spacing_y
        else:
            margin = 20
            pos_map = {
                "center": ((w - tw) // 2, (h - th) // 2),
                "top-left": (margin, margin),
                "top-right": (w - tw - margin, margin),
                "bottom-left": (margin, h - th - margin),
                "bottom-right": (w - tw - margin, h - th - margin),
            }
            pos = pos_map.get(args.position, pos_map["bottom-right"])
            draw.text(pos, args.text, font=font, fill=fill)

        result = Image.alpha_composite(img, overlay)

        buf = io.BytesIO()
        result.save(buf, format="PNG")
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 水印添加完成\n"
            f"文字: {args.text}\n"
            f"位置: {args.position}\n"
            f"透明度: {args.opacity}/255\n"
            f"[BASE64]{out_b64}"
        )
