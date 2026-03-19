"""图片理解引擎 — 多 Provider Vision API（Phase 12）

支持:
- 图片描述（多 Provider 降级: MiniMax → OpenAI → fallback）
- OCR 文字提取（结构化输出）
- 图片格式自动检测
- Hook 事件集成
"""

import base64
import logging
from typing import Optional

from ..llm.llm_client import get_llm_client
from ..llm.types import LLMRequest

logger = logging.getLogger(__name__)

# 安全限制
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_PROMPT_LENGTH = 500              # prompt 最大字符数
ALLOWED_MIMES = {"image/png", "image/jpeg", "image/gif", "image/webp"}

# Vision 模型优先级 — NVIDIA NIM 免费通道优先
VISION_MODELS = [
    "qwen/qwen3.5-397b-a17b",           # NVIDIA NIM: Qwen 3.5 397B VLM (最强免费)
    "nvidia/nemotron-nano-12b-v2-vl",   # NVIDIA NIM: Nemotron VL 12B (轻量快速)
    "moonshotai/kimi-k2.5",             # NVIDIA NIM: Kimi K2.5 VLM
    "gpt-4o",                            # OpenAI GPT-4o (付费)
    "gpt-4o-mini",                       # OpenAI GPT-4o-mini (付费)
    "MiniMax-M2.5-highspeed",           # MiniMax (国产付费)
]

OCR_PROMPT = """请提取这张图片中的所有文字内容。

要求:
1. 保持原始格式和排版
2. 如果有表格，用 Markdown 表格格式输出
3. 如果有代码，用代码块格式输出
4. 如果没有文字，描述图片内容
5. 标注文字语言"""


def _detect_mime(image_bytes: bytes) -> str:
    """检测图片 MIME 类型"""
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    if image_bytes[:2] == b'\xff\xd8':
        return "image/jpeg"
    if image_bytes[:4] == b'GIF8':
        return "image/gif"
    if image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return "image/webp"
    return "image/jpeg"  # 默认


def _select_vision_model() -> str:
    """选择可用的 Vision 模型 — NVIDIA NIM 免费通道优先"""
    client = get_llm_client()
    for model in VISION_MODELS:
        for provider in client.providers:
            if provider.supports_model(model):
                return model
    return VISION_MODELS[0] if VISION_MODELS else "qwen/qwen3.5-397b-a17b"


async def describe_image(
    image_bytes: bytes,
    prompt: str = "请详细描述这张图片的内容。",
    language: str = "zh",
    model: str = "",
) -> dict:
    """分析图片内容 — 多 Provider 降级

    Returns:
        {"description": str, "model": str, "tokens": int, "provider": str}
    """
    if not image_bytes:
        return {"description": "", "error": "Empty image data"}

    # 安全校验: 文件大小
    if len(image_bytes) > MAX_IMAGE_BYTES:
        return {"description": "", "error": f"图片过大: {len(image_bytes) / 1024 / 1024:.1f}MB，上限 {MAX_IMAGE_BYTES // 1024 // 1024}MB"}

    # 安全校验: MIME 类型
    mime = _detect_mime(image_bytes)
    if mime not in ALLOWED_MIMES:
        return {"description": "", "error": f"不支持的图片格式: {mime}"}

    # 安全校验: prompt 长度截断
    prompt = prompt[:MAX_PROMPT_LENGTH]

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    vision_model = model or _select_vision_model()

    # 尝试 Vision API
    try:
        result = await _vision_api(b64, mime, prompt, vision_model)
        await _emit_vision_event("describe", vision_model, True)
        return result
    except Exception as e:
        logger.warning(f"Vision API failed with {vision_model}: {e}")

    # 尝试其他 Vision 模型
    for alt_model in VISION_MODELS:
        if alt_model == vision_model:
            continue
        try:
            client = get_llm_client()
            has_provider = any(p.supports_model(alt_model) for p in client.providers)
            if not has_provider:
                continue
            result = await _vision_api(b64, mime, prompt, alt_model)
            await _emit_vision_event("describe", alt_model, True)
            return result
        except Exception:
            continue

    # 全部失败 → fallback
    await _emit_vision_event("describe", "fallback", False)
    return await _fallback_describe(b64, prompt, vision_model)


async def _vision_api(b64_image: str, mime: str, prompt: str, model: str) -> dict:
    """使用多模态模型分析图片"""
    client = get_llm_client()

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64_image}"},
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]

    request = LLMRequest(
        messages=messages, model=model,
        temperature=0.5, max_tokens=2048, stream=False,
    )

    response = await client.complete(request)
    return {
        "description": response.content,
        "model": model,
        "provider": response.provider,
        "tokens": response.usage.get("total_tokens", 0) if response.usage else 0,
    }


async def _fallback_describe(b64_image: str, prompt: str, model: str) -> dict:
    """Fallback: 告知用户图片已接收但无法分析"""
    size_kb = len(b64_image) * 3 / 4 / 1024
    client = get_llm_client()
    request = LLMRequest(
        messages=[{
            "role": "user",
            "content": (
                f"用户发送了一张图片（约 {size_kb:.0f}KB）并说：{prompt}\n\n"
                "由于当前模型不支持图片理解，请友好地告知用户你已收到图片，"
                "但暂时无法分析图片内容。建议用户用文字描述图片内容或问题。"
            ),
        }],
        model=model, temperature=0.7, max_tokens=512, stream=False,
    )
    response = await client.complete(request)
    return {
        "description": response.content,
        "model": model,
        "vision_supported": False,
        "image_size_kb": round(size_kb, 1),
    }


async def extract_text_from_image(
    image_bytes: bytes,
    model: str = "",
) -> dict:
    """OCR: 从图片中提取文字（结构化输出）"""
    return await describe_image(image_bytes, prompt=OCR_PROMPT, model=model)


async def analyze_image(
    image_bytes: bytes,
    question: str = "",
    model: str = "",
) -> dict:
    """图片问答: 用户针对图片提问"""
    prompt = question or "请详细描述这张图片的内容，包括场景、物体、文字、颜色等。"
    return await describe_image(image_bytes, prompt=prompt, model=model)


async def _emit_vision_event(action: str, model: str, success: bool):
    """Hook: 触发 Vision 分析事件"""
    try:
        from ..hooks.hook_registry import HookRegistry, HookEventType
        await HookRegistry.emit(HookEventType.VISION_ANALYZE, {
            "action": action, "model": model, "success": success,
        })
    except Exception:
        pass


def get_vision_status() -> dict:
    """获取 Vision 引擎状态"""
    selected = _select_vision_model()
    return {
        "available": True,
        "engine": "multi_provider_vision",
        "primary_model": selected,
        "supported_models": VISION_MODELS,
        "fallback": "text_description",
    }
