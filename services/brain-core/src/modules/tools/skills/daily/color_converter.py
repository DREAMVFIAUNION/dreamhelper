"""颜色转换器 — HEX/RGB/HSL 互转"""

from typing import Any
from pydantic import Field
from ..skill_engine import BaseSkill, SkillSchema
import colorsys
import re


class ColorSchema(SkillSchema):
    color: str = Field(description="颜色值，支持 HEX(#FF0000)、RGB(255,0,0)、HSL(0,100,50)")


def _parse_hex(s: str):
    s = s.lstrip("#")
    if len(s) == 3:
        s = s[0]*2 + s[1]*2 + s[2]*2
    if len(s) != 6:
        return None
    try:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError:
        return None


def _parse_rgb(s: str):
    m = re.match(r"(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", s)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if all(0 <= v <= 255 for v in (r, g, b)):
            return r, g, b
    return None


class ColorConverterSkill(BaseSkill):
    name = "color_converter"
    description = "颜色格式转换: HEX ↔ RGB ↔ HSL"
    category = "daily"
    args_schema = ColorSchema
    tags = ["颜色", "HEX", "RGB", "HSL", "color"]

    async def execute(self, **kwargs: Any) -> str:
        raw = kwargs["color"].strip()

        rgb = _parse_hex(raw)
        if rgb is None:
            rgb = _parse_rgb(raw)
        if rgb is None:
            return f"无法解析颜色: {raw}\n支持格式: #FF0000 / 255,0,0"

        r, g, b = rgb
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        hex_str = f"#{r:02X}{g:02X}{b:02X}"
        hsl_str = f"HSL({h*360:.0f}, {s*100:.0f}%, {l*100:.0f}%)"

        return (
            f"颜色转换结果:\n"
            f"  HEX: {hex_str}\n"
            f"  RGB: rgb({r}, {g}, {b})\n"
            f"  HSL: {hsl_str}"
        )
