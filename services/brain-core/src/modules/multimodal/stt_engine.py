"""STT 语音转文字引擎 — 三级降级策略（Phase 7 → Phase 11）

优先级:
1. faster-whisper 本地（零 API 成本）
2. OpenAI Whisper API 兼容接口（OPENAI_BASE_URL + /audio/transcriptions）
3. MiniMax STT（如有 KEY）
"""

import io
import logging
import tempfile
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False


# 全局模型实例（懒加载）
_whisper_model: Optional[object] = None
_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")


def _get_model():
    """懒加载 Whisper 模型"""
    global _whisper_model
    if _whisper_model is None and HAS_FASTER_WHISPER:
        logger.info(f"Loading Whisper model: {_MODEL_SIZE}")
        _whisper_model = WhisperModel(
            _MODEL_SIZE,
            device="cpu",
            compute_type="int8",
        )
        logger.info("Whisper model loaded")
    return _whisper_model


def _convert_webm_to_wav(audio_bytes: bytes) -> bytes:
    """将 WebM 音频转为 WAV（浏览器录音常为 WebM）"""
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
        buf = io.BytesIO()
        seg.export(buf, format="wav")
        return buf.getvalue()
    except ImportError:
        logger.warning("pydub not installed, skipping WebM→WAV conversion")
        return audio_bytes
    except Exception as e:
        logger.warning(f"WebM→WAV conversion failed: {e}")
        return audio_bytes


async def speech_to_text(
    audio_bytes: bytes,
    language: str = "zh",
    format: str = "wav",
) -> dict:
    """语音转文字

    Args:
        audio_bytes: 音频字节数据
        language: 语言代码 (zh, en, ja, auto)
        format: 音频格式 (wav, mp3, webm, ogg)

    Returns:
        {"text": "识别结果", "language": "zh", "duration": 3.5, "segments": [...]}
    """
    if not audio_bytes:
        return {"text": "", "error": "Empty audio data"}

    # WebM → WAV 转换（浏览器录音兼容）
    if format in ("webm", "ogg"):
        audio_bytes = _convert_webm_to_wav(audio_bytes)
        format = "wav"

    # 方式 1: faster-whisper 本地识别
    if HAS_FASTER_WHISPER:
        return await _transcribe_local(audio_bytes, language, format)

    # 方式 2: OpenAI Whisper API 兼容接口
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        return await _transcribe_openai_api(audio_bytes, language, format, openai_key)

    # 方式 3: 无引擎可用
    return {
        "text": "",
        "error": "STT not available. Install faster-whisper or set OPENAI_API_KEY.",
        "engine": "none",
    }


async def _transcribe_local(
    audio_bytes: bytes,
    language: str,
    format: str,
) -> dict:
    """使用 faster-whisper 本地转写"""
    model = _get_model()
    if model is None:
        return {"text": "", "error": "Whisper model failed to load"}

    suffix = f".{format}" if format else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        segments, info = model.transcribe(
            tmp_path,
            language=language if language != "auto" else None,
            beam_size=5,
            vad_filter=True,
        )

        result_segments = []
        full_text = ""
        for seg in segments:
            result_segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
            })
            full_text += seg.text

        return {
            "text": full_text.strip(),
            "language": info.language,
            "duration": round(info.duration, 2),
            "segments": result_segments,
            "engine": "faster-whisper",
        }
    except Exception as e:
        return {"text": "", "error": f"Transcription failed: {e}"}
    finally:
        os.unlink(tmp_path)


async def _transcribe_openai_api(
    audio_bytes: bytes,
    language: str,
    format: str,
    api_key: str,
) -> dict:
    """OpenAI Whisper API 兼容接口（也支持 DeepSeek、本地 API 等）"""
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    url = f"{base_url}/audio/transcriptions"

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            files = {"file": (f"audio.{format}", audio_bytes, f"audio/{format}")}
            data = {"model": "whisper-1"}
            if language and language != "auto":
                data["language"] = language

            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data,
            )

            if resp.status_code != 200:
                return {"text": "", "error": f"Whisper API {resp.status_code}: {resp.text[:200]}"}

            result = resp.json()
            return {
                "text": result.get("text", "").strip(),
                "language": language,
                "duration": result.get("duration", 0),
                "segments": [],
                "engine": "openai-whisper-api",
            }
    except Exception as e:
        logger.warning(f"OpenAI Whisper API error: {e}")
        return {"text": "", "error": f"Whisper API error: {e}"}


def get_stt_status() -> dict:
    """获取 STT 引擎状态"""
    has_api = bool(os.environ.get("OPENAI_API_KEY"))
    engine = "faster-whisper" if HAS_FASTER_WHISPER else ("openai-api" if has_api else "none")
    return {
        "available": HAS_FASTER_WHISPER or has_api,
        "engine": engine,
        "model_size": _MODEL_SIZE if HAS_FASTER_WHISPER else None,
        "model_loaded": _whisper_model is not None,
        "has_api_fallback": has_api,
    }
