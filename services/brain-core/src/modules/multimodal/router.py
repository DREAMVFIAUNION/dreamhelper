"""多模态 API 路由 — STT / TTS / Vision（Phase 7）"""

import base64
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel

from ...common.rate_limit import limiter

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100MB


async def _read_upload(file: UploadFile, label: str = "文件") -> bytes:
    """读取上传文件并检查大小限制 (100MB)"""
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"{label}大小超过限制 (最大 100MB)")
    return data

from .tts_engine import text_to_speech, list_voices, get_tts_status
from .stt_engine import speech_to_text, get_stt_status
from .vision_engine import describe_image, extract_text_from_image, analyze_image, get_vision_status
from .document_parser import parse_document

router = APIRouter(prefix="/multimodal", tags=["multimodal"])


# ── TTS ──

class TTSRequest(BaseModel):
    text: str
    voice: str = "xiaoxiao"
    rate: str = "+0%"
    volume: str = "+0%"


@router.post("/tts")
@limiter.limit("10/minute")
async def tts_endpoint(request: Request, req: TTSRequest):
    """文字转语音 → 返回 MP3 音频"""
    audio = await text_to_speech(
        text=req.text,
        voice=req.voice,
        rate=req.rate,
        volume=req.volume,
    )
    if audio is None:
        return {"error": "TTS failed or not available"}

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=speech.mp3",
            "Content-Length": str(len(audio)),
        },
    )


@router.post("/tts/base64")
@limiter.limit("10/minute")
async def tts_base64_endpoint(request: Request, req: TTSRequest):
    """文字转语音 → 返回 base64 编码音频"""
    audio = await text_to_speech(
        text=req.text,
        voice=req.voice,
        rate=req.rate,
        volume=req.volume,
    )
    if audio is None:
        return {"error": "TTS failed or not available"}

    return {
        "audio_base64": base64.b64encode(audio).decode("utf-8"),
        "format": "mp3",
        "size_bytes": len(audio),
        "voice": req.voice,
    }


@router.get("/tts/voices")
@limiter.limit("30/minute")
async def tts_voices(request: Request):
    """列出可用音色"""
    return {"voices": list_voices()}


# ── STT ──

@router.post("/stt")
@limiter.limit("5/minute")
async def stt_endpoint(
    request: Request,
    audio: UploadFile = File(...),
    language: str = Form("zh"),
):
    """语音转文字 — 上传音频文件"""
    audio_bytes = await _read_upload(audio, "音频文件")
    fmt = audio.filename.rsplit(".", 1)[-1] if audio.filename and "." in audio.filename else "wav"
    result = await speech_to_text(audio_bytes, language=language, format=fmt)
    return result


@router.post("/stt/base64")
@limiter.limit("5/minute")
async def stt_base64_endpoint(
    request: Request,
    audio_base64: str = Form(...),
    language: str = Form("zh"),
    format: str = Form("wav"),
):
    """语音转文字 — base64 编码音频"""
    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception:
        return {"text": "", "error": "Invalid base64 audio data"}
    result = await speech_to_text(audio_bytes, language=language, format=format)
    return result


# ── Vision ──

@router.post("/vision/describe")
@limiter.limit("5/minute")
async def vision_describe(
    request: Request,
    image: UploadFile = File(...),
    prompt: str = Form("请详细描述这张图片的内容。"),
):
    """图片理解 — 上传图片"""
    image_bytes = await _read_upload(image, "图片")
    result = await describe_image(image_bytes, prompt=prompt)
    return result


@router.post("/vision/describe/base64")
@limiter.limit("5/minute")
async def vision_describe_base64(
    request: Request,
    image_base64: str = Form(...),
    prompt: str = Form("请详细描述这张图片的内容。"),
):
    """图片理解 — base64 编码图片"""
    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception:
        return {"description": "", "error": "Invalid base64 image data"}
    result = await describe_image(image_bytes, prompt=prompt)
    return result


@router.post("/vision/ocr")
@limiter.limit("5/minute")
async def vision_ocr(request: Request, image: UploadFile = File(...)):
    """OCR 文字提取"""
    image_bytes = await _read_upload(image, "图片")
    result = await extract_text_from_image(image_bytes)
    return result


# ── Vision Q&A ──

@router.post("/vision/analyze")
@limiter.limit("5/minute")
async def vision_analyze(
    request: Request,
    image: UploadFile = File(...),
    question: str = Form(""),
):
    """图片问答 — 上传图片并提问"""
    image_bytes = await _read_upload(image, "图片")
    result = await analyze_image(image_bytes, question=question)
    return result


# ── Document Parse ──

@router.post("/document/parse")
@limiter.limit("5/minute")
async def document_parse_endpoint(
    request: Request,
    file: UploadFile = File(...),
):
    """文档解析 — 提取纯文本内容（PDF/DOCX/XLSX/CSV/MD/TXT/JSON）"""
    file_bytes = await _read_upload(file, "文档")
    filename = file.filename or "unknown"
    result = await parse_document(file_bytes, filename)
    return result


# ── 状态 ──

@router.get("/status")
@limiter.limit("30/minute")
async def multimodal_status(request: Request):
    """多模态引擎状态"""
    return {
        "tts": get_tts_status(),
        "stt": get_stt_status(),
        "vision": get_vision_status(),
    }
