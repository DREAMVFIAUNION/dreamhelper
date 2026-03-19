"""STT / TTS 引擎测试"""

import pytest
from src.modules.multimodal.stt_engine import (
    speech_to_text,
    get_stt_status,
    _convert_webm_to_wav,
)
from src.modules.multimodal.tts_engine import (
    list_voices,
    get_tts_status,
    _strip_for_speech,
    EDGE_VOICES,
    MINIMAX_VOICES,
)


# ── STT Tests ──

def test_stt_status():
    status = get_stt_status()
    assert "available" in status
    assert "engine" in status
    assert "has_api_fallback" in status


@pytest.mark.asyncio
async def test_stt_empty_audio():
    result = await speech_to_text(b"", language="zh", format="wav")
    assert result["text"] == ""
    assert "error" in result


@pytest.mark.asyncio
async def test_stt_returns_dict():
    """STT 应始终返回 dict，无论引擎是否可用"""
    result = await speech_to_text(b"\x00\x01\x02", language="zh", format="wav")
    assert isinstance(result, dict)
    # 要么有 text，要么有 error
    assert "text" in result or "error" in result


def test_webm_to_wav_passthrough():
    """无 pydub 时应该原样返回"""
    data = b"fake webm data"
    result = _convert_webm_to_wav(data)
    # 无论是否转换成功，都应返回 bytes
    assert isinstance(result, bytes)


# ── TTS Tests ──

def test_tts_status():
    status = get_tts_status()
    assert "edge_tts" in status
    assert "minimax_tts" in status
    assert "voices" in status
    assert isinstance(status["voices"], int)


def test_list_voices():
    voices = list_voices()
    assert isinstance(voices, list)
    assert len(voices) >= len(EDGE_VOICES)
    for v in voices:
        assert "id" in v
        assert "name" in v
        assert "lang" in v
        assert "provider" in v


def test_edge_voices_mapping():
    assert "xiaoxiao" in EDGE_VOICES
    assert "en_jenny" in EDGE_VOICES
    assert EDGE_VOICES["xiaoxiao"] == "zh-CN-XiaoxiaoNeural"


def test_minimax_voices_mapping():
    assert "mm_female_1" in MINIMAX_VOICES
    assert "mm_male_1" in MINIMAX_VOICES
    assert MINIMAX_VOICES["mm_female_1"]["voice_id"] == "female-tianmei"


def test_strip_for_speech_code_blocks():
    text = "hello ```python\nprint('hi')\n``` world"
    result = _strip_for_speech(text)
    assert "```" not in result
    assert "代码块已省略" in result


def test_strip_for_speech_inline_code():
    text = "use `pip install` to install"
    result = _strip_for_speech(text)
    assert "`" not in result
    assert "pip install" in result


def test_strip_for_speech_markdown():
    text = "## Title\n**bold** and *italic*\n[link](http://example.com)"
    result = _strip_for_speech(text)
    assert "##" not in result
    assert "**" not in result
    assert "[link]" not in result
    assert "Title" in result
    assert "bold" in result
    assert "link" in result


def test_strip_for_speech_strikethrough():
    text = "this is ~~deleted~~ text"
    result = _strip_for_speech(text)
    assert "~~" not in result
    assert "deleted" in result


def test_strip_for_speech_table_separator():
    text = "| col1 | col2 |\n|:---:|---:|\n| a | b |"
    result = _strip_for_speech(text)
    assert "|:---:|" not in result
