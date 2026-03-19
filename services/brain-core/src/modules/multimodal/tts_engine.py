"""TTS 文字转语音引擎 — Edge-TTS + MiniMax 双引擎（Phase 7 → Phase 11）

优先级:
1. Edge-TTS（免费、高质量、8 音色）
2. MiniMax TTS API（如配置了 API KEY，支持更多音色）
"""

import asyncio
import io
import logging
import os
import re
import tempfile
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False


# ── Edge-TTS 预设音色 ──

EDGE_VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",      # 女声，温柔
    "xiaoyi": "zh-CN-XiaoyiNeural",           # 女声，活泼
    "yunjian": "zh-CN-YunjianNeural",         # 男声，沉稳
    "yunxi": "zh-CN-YunxiNeural",             # 男声，年轻
    "yunyang": "zh-CN-YunyangNeural",         # 男声，新闻播报
    "xiaoxuan": "zh-CN-XiaoxuanNeural",       # 女声，甜美
    "en_jenny": "en-US-JennyNeural",          # 英文女声
    "en_guy": "en-US-GuyNeural",              # 英文男声
}

# ── MiniMax TTS 音色 ──

MINIMAX_VOICES = {
    "mm_female_1": {"voice_id": "female-tianmei", "label": "甜美女声"},
    "mm_female_2": {"voice_id": "female-shaonv", "label": "少女"},
    "mm_male_1": {"voice_id": "male-qn-qingse", "label": "青涩男声"},
    "mm_male_2": {"voice_id": "male-qn-jingying", "label": "精英男声"},
}

DEFAULT_VOICE = "xiaoxiao"

# 所有音色合集（用于路由）
ALL_VOICES = set(EDGE_VOICES.keys()) | set(MINIMAX_VOICES.keys())


async def text_to_speech(
    text: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    volume: str = "+0%",
) -> Optional[bytes]:
    """将文本转为语音 MP3

    Args:
        text: 要转换的文本
        voice: 音色名称（见 EDGE_VOICES / MINIMAX_VOICES）
        rate: 语速调整，如 "+20%", "-10%"
        volume: 音量调整

    Returns:
        MP3 音频字节，失败返回 None
    """
    clean_text = _strip_for_speech(text)
    if not clean_text.strip():
        return None

    # MiniMax 音色走 MiniMax API
    if voice in MINIMAX_VOICES:
        result = await _tts_minimax(clean_text, voice)
        if result:
            return result
        logger.warning("MiniMax TTS failed, falling back to Edge-TTS")
        voice = DEFAULT_VOICE

    # Edge-TTS
    if HAS_EDGE_TTS:
        return await _tts_edge(clean_text, voice, rate, volume)

    logger.warning("No TTS engine available")
    return None


async def _tts_edge(
    text: str, voice: str, rate: str, volume: str,
) -> Optional[bytes]:
    """Edge-TTS 合成"""
    voice_id = EDGE_VOICES.get(voice, EDGE_VOICES[DEFAULT_VOICE])
    try:
        communicate = edge_tts.Communicate(
            text=text, voice=voice_id, rate=rate, volume=volume,
        )
        audio_data = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.write(chunk["data"])
        result = audio_data.getvalue()
        return result if len(result) > 0 else None
    except Exception as e:
        logger.warning(f"Edge-TTS error: {e}")
        return None


async def _tts_minimax(text: str, voice: str) -> Optional[bytes]:
    """MiniMax TTS API 合成"""
    api_key = os.environ.get("MINIMAX_API_KEY", "")
    group_id = os.environ.get("MINIMAX_GROUP_ID", "")
    if not api_key or not group_id:
        return None

    voice_cfg = MINIMAX_VOICES.get(voice)
    if not voice_cfg:
        return None

    url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={group_id}"
    payload = {
        "model": "speech-01-turbo",
        "text": text[:2000],  # API 限制
        "voice_setting": {
            "voice_id": voice_cfg["voice_id"],
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code != 200:
                logger.warning(f"MiniMax TTS {resp.status_code}: {resp.text[:200]}")
                return None

            data = resp.json()
            audio_hex = data.get("data", {}).get("audio", "")
            if not audio_hex:
                return None
            return bytes.fromhex(audio_hex)
    except Exception as e:
        logger.warning(f"MiniMax TTS error: {e}")
        return None


def list_voices() -> list[dict]:
    """列出所有可用音色"""
    voices = []
    for k, v in EDGE_VOICES.items():
        voices.append({
            "id": k,
            "name": v,
            "lang": "zh-CN" if v.startswith("zh") else "en-US",
            "provider": "edge-tts",
        })
    has_minimax = bool(os.environ.get("MINIMAX_API_KEY"))
    if has_minimax:
        for k, v in MINIMAX_VOICES.items():
            voices.append({
                "id": k,
                "name": v["label"],
                "lang": "zh-CN",
                "provider": "minimax",
            })
    return voices


def get_tts_status() -> dict:
    """获取 TTS 引擎状态"""
    return {
        "edge_tts": HAS_EDGE_TTS,
        "minimax_tts": bool(os.environ.get("MINIMAX_API_KEY")),
        "voices": len(list_voices()),
    }


def _strip_for_speech(text: str) -> str:
    """去除不适合朗读的格式"""
    # 去除代码块
    text = re.sub(r'```[\s\S]*?```', '代码块已省略。', text)
    # 去除行内代码
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # 去除 Markdown 标题标记
    text = re.sub(r'#{1,6}\s', '', text)
    # 去除加粗/斜体
    text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)
    # 去除链接
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 去除表格分隔线
    text = re.sub(r'\|[-:]+\|[-:|\s]+\|', '', text)
    # 去除删除线
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    # 去除多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
