"""图像技能测试"""

import asyncio
import base64
import io
import pytest

# 创建一个小测试图片
def _make_test_image(w=100, h=100, color=(255, 0, 0)) -> str:
    from PIL import Image
    img = Image.new("RGB", (w, h), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


TEST_IMG = None

def get_test_img():
    global TEST_IMG
    if TEST_IMG is None:
        TEST_IMG = _make_test_image()
    return TEST_IMG


class TestImageResize:
    def test_resize_by_scale(self):
        from src.modules.tools.skills.image.image_resize import ImageResizeSkill
        skill = ImageResizeSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(image_b64=get_test_img(), scale=0.5)
        )
        assert "缩放完成" in result
        assert "50×50" in result

    def test_resize_by_width(self):
        from src.modules.tools.skills.image.image_resize import ImageResizeSkill
        skill = ImageResizeSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(image_b64=get_test_img(), width=200)
        )
        assert "缩放完成" in result
        assert "200×200" in result


class TestImageCrop:
    def test_crop_coordinates(self):
        from src.modules.tools.skills.image.image_crop import ImageCropSkill
        skill = ImageCropSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(image_b64=get_test_img(), left=10, top=10, right=50, bottom=50)
        )
        assert "裁剪完成" in result
        assert "40×40" in result

    def test_crop_ratio(self):
        from src.modules.tools.skills.image.image_crop import ImageCropSkill
        skill = ImageCropSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(image_b64=get_test_img(), ratio="16:9")
        )
        assert "裁剪完成" in result


class TestImageFilter:
    def test_grayscale(self):
        from src.modules.tools.skills.image.image_filter import ImageFilterSkill
        skill = ImageFilterSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(image_b64=get_test_img(), filter_name="grayscale")
        )
        assert "滤镜应用完成" in result
        assert "grayscale" in result

    def test_blur(self):
        from src.modules.tools.skills.image.image_filter import ImageFilterSkill
        skill = ImageFilterSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(image_b64=get_test_img(), filter_name="blur", intensity=5)
        )
        assert "滤镜应用完成" in result

    def test_invalid_filter(self):
        from src.modules.tools.skills.image.image_filter import ImageFilterSkill
        skill = ImageFilterSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(image_b64=get_test_img(), filter_name="nonexistent")
        )
        assert "未知滤镜" in result


class TestQrcode:
    def test_basic_qrcode(self):
        from src.modules.tools.skills.image.qrcode_generator import QrcodeGeneratorSkill
        skill = QrcodeGeneratorSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(data="https://dreamvfia.com")
        )
        assert "二维码生成完成" in result
        assert "[BASE64]" in result


class TestImageCompress:
    def test_compress_quality(self):
        from src.modules.tools.skills.image.image_compress import ImageCompressSkill
        skill = ImageCompressSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(image_b64=get_test_img(), quality=50)
        )
        assert "压缩完成" in result


class TestImageFormatConvert:
    def test_png_to_jpeg(self):
        from src.modules.tools.skills.image.image_format_convert import ImageFormatConvertSkill
        skill = ImageFormatConvertSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(image_b64=get_test_img(), target_format="JPEG")
        )
        assert "格式转换完成" in result
        assert "JPEG" in result

    def test_unsupported_format(self):
        from src.modules.tools.skills.image.image_format_convert import ImageFormatConvertSkill
        skill = ImageFormatConvertSkill()
        result = asyncio.get_event_loop().run_until_complete(
            skill.execute(image_b64=get_test_img(), target_format="XYZ")
        )
        assert "不支持的格式" in result
