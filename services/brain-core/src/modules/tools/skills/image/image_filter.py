"""图像滤镜技能"""

import base64
import io

from PIL import Image, ImageFilter, ImageEnhance
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill

FILTERS = {
    "blur": lambda img, v: img.filter(ImageFilter.GaussianBlur(radius=v or 3)),
    "sharpen": lambda img, _: img.filter(ImageFilter.SHARPEN),
    "edge": lambda img, _: img.filter(ImageFilter.FIND_EDGES),
    "emboss": lambda img, _: img.filter(ImageFilter.EMBOSS),
    "contour": lambda img, _: img.filter(ImageFilter.CONTOUR),
    "smooth": lambda img, _: img.filter(ImageFilter.SMOOTH_MORE),
    "detail": lambda img, _: img.filter(ImageFilter.DETAIL),
    "grayscale": lambda img, _: img.convert("L").convert("RGB"),
    "sepia": lambda img, _: _apply_sepia(img),
    "invert": lambda img, _: _apply_invert(img),
}


def _apply_sepia(img: Image.Image) -> Image.Image:
    gray = img.convert("L")
    w, h = gray.size
    sepia = Image.new("RGB", (w, h))
    pixels = gray.load()
    sepia_pixels = sepia.load()
    for y in range(h):
        for x in range(w):
            g = pixels[x, y]
            r = min(255, int(g * 1.2 + 40))
            gn = min(255, int(g * 1.0 + 20))
            b = min(255, int(g * 0.8))
            sepia_pixels[x, y] = (r, gn, b)
    return sepia


def _apply_invert(img: Image.Image) -> Image.Image:
    if img.mode == "RGBA":
        r, g, b, a = img.split()
        from PIL import ImageOps
        rgb = Image.merge("RGB", (r, g, b))
        rgb = ImageOps.invert(rgb)
        r2, g2, b2 = rgb.split()
        return Image.merge("RGBA", (r2, g2, b2, a))
    from PIL import ImageOps
    return ImageOps.invert(img.convert("RGB"))


class ImageFilterArgs(BaseModel):
    image_b64: str = Field(..., description="Base64 编码的图像数据")
    filter_name: str = Field(..., description="滤镜: blur/sharpen/edge/emboss/contour/smooth/detail/grayscale/sepia/invert")
    intensity: float = Field(0, description="强度参数 (仅部分滤镜有效, 如 blur 的半径)")
    brightness: float = Field(1.0, description="亮度 0.0-3.0 (1.0=原始)")
    contrast: float = Field(1.0, description="对比度 0.0-3.0 (1.0=原始)")
    saturation: float = Field(1.0, description="饱和度 0.0-3.0 (1.0=原始)")


class ImageFilterSkill(BaseSkill):
    name = "image_filter"
    description = "应用图像滤镜 — 支持 10 种滤镜 + 亮度/对比度/饱和度调节"
    category = "image"
    tags = ["图像", "滤镜", "filter", "模糊", "锐化", "灰度", "特效"]
    args_schema = ImageFilterArgs

    async def execute(self, **kwargs) -> str:
        args = ImageFilterArgs(**kwargs)
        img_data = base64.b64decode(args.image_b64)
        img = Image.open(io.BytesIO(img_data))

        applied = []

        # 应用滤镜
        filter_fn = FILTERS.get(args.filter_name)
        if filter_fn is None:
            return f"未知滤镜: {args.filter_name}，支持: {', '.join(FILTERS.keys())}"
        img = filter_fn(img, args.intensity)
        applied.append(args.filter_name)

        # 亮度/对比度/饱和度
        if img.mode == "L":
            img = img.convert("RGB")
        if args.brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(args.brightness)
            applied.append(f"brightness={args.brightness}")
        if args.contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(args.contrast)
            applied.append(f"contrast={args.contrast}")
        if args.saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(args.saturation)
            applied.append(f"saturation={args.saturation}")

        buf = io.BytesIO()
        fmt = "PNG"
        img.save(buf, format=fmt)
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 滤镜应用完成\n"
            f"效果: {', '.join(applied)}\n"
            f"尺寸: {img.width}×{img.height}\n"
            f"[BASE64]{out_b64}"
        )
