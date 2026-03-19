"""Vision 引擎测试"""

import pytest
from src.modules.multimodal.vision_engine import (
    _detect_mime,
    _select_vision_model,
    get_vision_status,
    describe_image,
    VISION_MODELS,
)


def test_detect_mime_jpeg():
    assert _detect_mime(b'\xff\xd8\xff\xe0') == "image/jpeg"


def test_detect_mime_png():
    assert _detect_mime(b'\x89PNG\r\n\x1a\n') == "image/png"


def test_detect_mime_gif():
    assert _detect_mime(b'GIF89a') == "image/gif"


def test_detect_mime_webp():
    assert _detect_mime(b'RIFF\x00\x00\x00\x00WEBP') == "image/webp"


def test_detect_mime_unknown():
    assert _detect_mime(b'\x00\x00\x00\x00') == "image/jpeg"  # default


def test_select_vision_model():
    model = _select_vision_model()
    assert isinstance(model, str)
    assert len(model) > 0


def test_vision_status():
    status = get_vision_status()
    assert status["available"] is True
    assert status["engine"] == "multi_provider_vision"
    assert "primary_model" in status
    assert "supported_models" in status
    assert isinstance(status["supported_models"], list)
    assert status["fallback"] == "text_description"


def test_vision_models_list():
    assert len(VISION_MODELS) >= 3
    assert "gpt-4o" in VISION_MODELS


@pytest.mark.asyncio
async def test_describe_image_empty():
    result = await describe_image(b"")
    assert result["description"] == ""
    assert "error" in result
