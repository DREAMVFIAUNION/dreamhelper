"""图像旋转技能"""

import base64
import io

from PIL import Image
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class ImageRotateArgs(BaseModel):
    image_b64: str = Field(..., description="Base64 编码的图像数据")
    angle: float = Field(..., description="旋转角度 (正值=逆时针)")
    expand: bool = Field(True, description="是否扩展画布以容纳旋转后的图像")
    fill_color: str = Field("transparent", description="填充颜色: transparent/white/black 或 hex")


class ImageRotateSkill(BaseSkill):
    name = "image_rotate"
    description = "旋转图像到指定角度，支持 EXIF 自动校正"
    category = "image"
    tags = ["图像", "旋转", "rotate", "翻转"]
    args_schema = ImageRotateArgs

    async def execute(self, **kwargs) -> str:
        args = ImageRotateArgs(**kwargs)
        img_data = base64.b64decode(args.image_b64)
        img = Image.open(io.BytesIO(img_data))

        # EXIF 自动校正
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        orig_w, orig_h = img.size

        # 处理填充颜色
        if args.fill_color == "transparent":
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            fill = (0, 0, 0, 0)
        elif args.fill_color == "white":
            fill = (255, 255, 255)
        elif args.fill_color == "black":
            fill = (0, 0, 0)
        else:
            hex_color = args.fill_color.lstrip("#")
            fill = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        result = img.rotate(args.angle, expand=args.expand, fillcolor=fill, resample=Image.BICUBIC)

        buf = io.BytesIO()
        fmt = "PNG" if img.mode == "RGBA" else (img.format or "PNG")
        result.save(buf, format=fmt)
        out_b64 = base64.b64encode(buf.getvalue()).decode()
        rw, rh = result.size

        return (
            f"✅ 旋转完成\n"
            f"旋转角度: {args.angle}°\n"
            f"原始尺寸: {orig_w}×{orig_h}\n"
            f"结果尺寸: {rw}×{rh}\n"
            f"[BASE64]{out_b64}"
        )
