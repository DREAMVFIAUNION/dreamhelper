"""图像元数据技能"""

import base64
import io

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pydantic import BaseModel, Field

from ..skill_engine import BaseSkill


class ImageMetadataArgs(BaseModel):
    image_b64: str = Field(..., description="Base64 编码的图像数据")
    strip: bool = Field(False, description="是否清除所有元数据并返回干净图像")


class ImageMetadataSkill(BaseSkill):
    name = "image_metadata"
    description = "读取图像 EXIF 元数据（相机/GPS/日期）或清除隐私信息"
    category = "image"
    tags = ["图像", "元数据", "EXIF", "GPS", "隐私"]
    args_schema = ImageMetadataArgs

    async def execute(self, **kwargs) -> str:
        args = ImageMetadataArgs(**kwargs)
        img_data = base64.b64decode(args.image_b64)
        img = Image.open(io.BytesIO(img_data))

        if args.strip:
            # 清除元数据：重新保存不带 EXIF
            clean = Image.new(img.mode, img.size)
            clean.putdata(list(img.getdata()))
            buf = io.BytesIO()
            fmt = img.format or "PNG"
            clean.save(buf, format=fmt)
            out_b64 = base64.b64encode(buf.getvalue()).decode()
            return f"✅ 元数据已清除\n格式: {fmt}\n尺寸: {img.width}×{img.height}\n[BASE64]{out_b64}"

        # 读取基本信息
        lines = [
            f"📷 图像元数据",
            f"格式: {img.format or 'UNKNOWN'}",
            f"尺寸: {img.width}×{img.height}",
            f"模式: {img.mode}",
        ]

        # 读取 EXIF
        exif_data = img.getexif()
        if exif_data:
            lines.append("\n— EXIF 信息 —")
            gps_info = {}
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                if tag_name == "GPSInfo":
                    # 解析 GPS
                    for gps_tag_id, gps_value in value.items():
                        gps_tag_name = GPSTAGS.get(gps_tag_id, str(gps_tag_id))
                        gps_info[gps_tag_name] = gps_value
                elif tag_name in ("Make", "Model", "DateTime", "DateTimeOriginal",
                                  "ExposureTime", "FNumber", "ISOSpeedRatings",
                                  "FocalLength", "Software", "ImageWidth", "ImageLength"):
                    lines.append(f"  {tag_name}: {value}")

            if gps_info:
                lines.append("\n— GPS 信息 —")
                lat = _convert_gps(gps_info.get("GPSLatitude"), gps_info.get("GPSLatitudeRef"))
                lon = _convert_gps(gps_info.get("GPSLongitude"), gps_info.get("GPSLongitudeRef"))
                if lat is not None and lon is not None:
                    lines.append(f"  纬度: {lat:.6f}")
                    lines.append(f"  经度: {lon:.6f}")
                    lines.append(f"  ⚠ 此图像包含 GPS 位置信息")
        else:
            lines.append("\n无 EXIF 数据")

        return "\n".join(lines)


def _convert_gps(coords, ref) -> float | None:
    """将 GPS 坐标元组转为十进制度数"""
    if coords is None or ref is None:
        return None
    try:
        d = float(coords[0])
        m = float(coords[1])
        s = float(coords[2])
        result = d + m / 60.0 + s / 3600.0
        if ref in ("S", "W"):
            result = -result
        return result
    except (IndexError, TypeError, ValueError):
        return None
