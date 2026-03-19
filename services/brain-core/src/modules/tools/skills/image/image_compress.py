"""图像压缩技能"""

import base64
import io

from PIL import Image
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class ImageCompressArgs(BaseModel):
    image_b64: str = Field(..., description="Base64 编码的图像数据")
    quality: int = Field(75, description="JPEG 质量 1-100")
    target_kb: int = Field(0, description="目标文件大小 (KB), 0=仅按quality压缩")
    max_width: int = Field(0, description="最大宽度, 超过则等比缩小, 0=不限")


class ImageCompressSkill(BaseSkill):
    name = "image_compress"
    description = "压缩图像 — 支持质量调节、目标大小、最大尺寸"
    category = "image"
    tags = ["图像", "压缩", "compress", "优化", "体积"]
    args_schema = ImageCompressArgs

    async def execute(self, **kwargs) -> str:
        args = ImageCompressArgs(**kwargs)
        img_data = base64.b64decode(args.image_b64)
        orig_size = len(img_data)
        img = Image.open(io.BytesIO(img_data))

        # 转为 RGB (JPEG 不支持 alpha)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 限制最大宽度
        if args.max_width > 0 and img.width > args.max_width:
            ratio = args.max_width / img.width
            img = img.resize(
                (args.max_width, int(img.height * ratio)),
                Image.LANCZOS,
            )

        if args.target_kb > 0:
            # 二分法逼近目标大小
            target_bytes = args.target_kb * 1024
            lo, hi = 5, 95
            best_buf = None
            for _ in range(10):
                mid = (lo + hi) // 2
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=mid, optimize=True)
                size = buf.tell()
                best_buf = buf
                if size > target_bytes:
                    hi = mid - 1
                else:
                    lo = mid + 1
            final_buf = best_buf
            final_quality = (lo + hi) // 2
        else:
            final_buf = io.BytesIO()
            img.save(final_buf, format="JPEG", quality=args.quality, optimize=True)
            final_quality = args.quality

        final_buf.seek(0)
        compressed_data = final_buf.read()
        out_b64 = base64.b64encode(compressed_data).decode()
        compressed_size = len(compressed_data)
        ratio = (1 - compressed_size / orig_size) * 100 if orig_size > 0 else 0

        return (
            f"✅ 压缩完成\n"
            f"原始大小: {orig_size / 1024:.1f} KB\n"
            f"压缩后: {compressed_size / 1024:.1f} KB\n"
            f"压缩率: {ratio:.1f}%\n"
            f"质量: {final_quality}\n"
            f"尺寸: {img.width}×{img.height}\n"
            f"[BASE64]{out_b64}"
        )
