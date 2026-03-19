"""二维码生成技能"""

import base64
import io

import qrcode
from PIL import Image
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class QrcodeGeneratorArgs(BaseModel):
    data: str = Field(..., description="二维码内容 (URL/文本)")
    size: int = Field(10, description="二维码方块大小 1-40")
    border: int = Field(4, description="边框宽度 (方块数)")
    fill_color: str = Field("#000000", description="前景色 (hex)")
    back_color: str = Field("#FFFFFF", description="背景色 (hex)")
    logo_b64: str = Field("", description="可选: Logo 图像 Base64 (叠加在中心)")
    error_correction: str = Field("M", description="纠错等级: L/M/Q/H")


EC_MAP = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


class QrcodeGeneratorSkill(BaseSkill):
    name = "qrcode_generator"
    description = "生成二维码 — 支持自定义颜色和 Logo 叠加"
    category = "image"
    tags = ["二维码", "QR", "qrcode", "链接"]
    args_schema = QrcodeGeneratorArgs

    async def execute(self, **kwargs) -> str:
        args = QrcodeGeneratorArgs(**kwargs)

        ec = EC_MAP.get(args.error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)
        # 如果有 Logo 则用高纠错
        if args.logo_b64:
            ec = qrcode.constants.ERROR_CORRECT_H

        qr = qrcode.QRCode(
            version=None,
            error_correction=ec,
            box_size=max(1, min(40, args.size)),
            border=max(0, args.border),
        )
        qr.add_data(args.data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=args.fill_color, back_color=args.back_color).convert("RGBA")

        # Logo 叠加
        if args.logo_b64:
            try:
                logo_data = base64.b64decode(args.logo_b64)
                logo = Image.open(io.BytesIO(logo_data)).convert("RGBA")
                # Logo 占 QR 码的 1/4
                qr_w, qr_h = img.size
                logo_max = min(qr_w, qr_h) // 4
                logo.thumbnail((logo_max, logo_max), Image.LANCZOS)
                # 居中
                lw, lh = logo.size
                pos = ((qr_w - lw) // 2, (qr_h - lh) // 2)
                # 白色底板
                pad = 6
                bg_rect = Image.new("RGBA", (lw + pad * 2, lh + pad * 2), (255, 255, 255, 255))
                img.paste(bg_rect, (pos[0] - pad, pos[1] - pad))
                img.paste(logo, pos, logo)
            except Exception:
                pass  # Logo 叠加失败则忽略

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        out_b64 = base64.b64encode(buf.getvalue()).decode()

        return (
            f"✅ 二维码生成完成\n"
            f"内容: {args.data[:80]}{'...' if len(args.data) > 80 else ''}\n"
            f"尺寸: {img.width}×{img.height}\n"
            f"纠错等级: {args.error_correction}\n"
            f"{'含 Logo' if args.logo_b64 else ''}\n"
            f"[BASE64]{out_b64}"
        )
