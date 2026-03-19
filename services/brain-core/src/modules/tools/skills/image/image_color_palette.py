"""图像取色板技能"""

import base64
import io
from collections import Counter

from PIL import Image
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class ImageColorPaletteArgs(BaseModel):
    image_b64: str = Field(..., description="Base64 编码的图像数据")
    colors: int = Field(8, description="提取颜色数量 (2-20)")
    method: str = Field("quantize", description="取色方法: quantize/kmeans")


class ImageColorPaletteSkill(BaseSkill):
    name = "image_color_palette"
    description = "从图像中提取主色调色板 — 量化取色"
    category = "image"
    tags = ["图像", "取色", "色板", "palette", "颜色"]
    args_schema = ImageColorPaletteArgs

    async def execute(self, **kwargs) -> str:
        args = ImageColorPaletteArgs(**kwargs)
        n = max(2, min(20, args.colors))

        img_data = base64.b64decode(args.image_b64)
        img = Image.open(io.BytesIO(img_data)).convert("RGB")

        # 缩小以加速
        img.thumbnail((200, 200), Image.LANCZOS)

        # 量化
        quantized = img.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
        palette_data = quantized.getpalette()
        if not palette_data:
            return "无法提取色板"

        # 统计每个颜色的像素占比
        pixel_count = quantized.width * quantized.height
        counter = Counter(quantized.getdata())
        top_indices = counter.most_common(n)

        lines = [f"🎨 色板 — {n} 色 (从 {img.width}×{img.height} 采样)"]
        lines.append("")

        palette_colors = []
        for idx, (color_idx, count) in enumerate(top_indices):
            i = color_idx * 3
            if i + 2 < len(palette_data):
                r, g, b = palette_data[i], palette_data[i + 1], palette_data[i + 2]
                hex_color = f"#{r:02X}{g:02X}{b:02X}"
                pct = count / pixel_count * 100
                palette_colors.append((hex_color, r, g, b, pct))
                block = "█" * max(1, int(pct / 3))
                lines.append(f"  {idx + 1}. {hex_color}  RGB({r},{g},{b})  {pct:5.1f}%  {block}")

        lines.append("")
        lines.append("CSS 变量:")
        for i, (hex_c, *_) in enumerate(palette_colors):
            lines.append(f"  --color-{i + 1}: {hex_c};")

        return "\n".join(lines)
