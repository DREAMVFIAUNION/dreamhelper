"""视觉皮层 (Visual Cortex) — 图像/视频理解模块

如同人类视觉皮层处理视觉信息，VisualCortex 负责:
- 图片理解 + 视觉问答 (VQA)
- 视频帧分析 + 截图/文档 OCR
- 集成: 丘脑检测视觉输入 → 视觉皮层并行 → 结果注入前额叶融合

使用 NVIDIA Nemotron-Nano-12B-VL（视觉语言模型，免费无限量）
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from .brain_config import BrainConfig
from ..llm.llm_client import get_llm_client
from ..llm.types import LLMRequest

logger = logging.getLogger(__name__)


@dataclass
class VisualCortexResult:
    """视觉皮层输出结果"""
    description: str = ""
    objects: list[str] = field(default_factory=list)
    text_content: str = ""
    latency_ms: float = 0.0
    confidence: float = 0.0


# ── 视觉皮层 Prompt ──────────────────────────────────

IMAGE_ANALYZE_PROMPT = """你是一个**视觉理解专家**，负责分析图像并提供详细描述。

请仔细观察图像，然后输出 JSON（不要输出其他内容）：

```json
{{
  "description": "图像内容的详细描述（2-3句话）",
  "objects": ["识别到的主要物体/元素列表"],
  "text_content": "图中检测到的所有文字（OCR结果，没有则留空）",
  "scene": "场景类型（如：室内/室外/文档/代码截图/图表/UI界面）",
  "confidence": 0.0-1.0
}}
```

{extra_instruction}"""

VIDEO_FRAMES_PROMPT = """你是一个**视频内容分析专家**，以下是从视频中提取的关键帧序列。

请分析帧序列，输出 JSON（不要输出其他内容）：

```json
{{
  "description": "视频内容的整体描述",
  "key_events": ["检测到的关键事件/动作序列"],
  "objects": ["出现的主要物体/人物"],
  "text_content": "视频中出现的文字（如有）",
  "confidence": 0.0-1.0
}}
```

{extra_instruction}"""


class VisualCortex:
    """
    视觉皮层 — 仿生大脑的视觉信息处理中心

    如同人类视觉皮层（V1-V5区）处理来自眼睛的视觉信号，
    VisualCortex 使用 NVIDIA Nemotron-12B-VL 处理:
    - 图片内容理解与描述
    - 视觉问答（用户问+图片）
    - 文字识别（OCR）
    - 视频帧序列分析
    """

    def __init__(self, config: BrainConfig):
        self.config = config
        self.model = config.visual_cortex_model
        self.enabled = config.visual_cortex_enabled
        self.timeout = config.visual_cortex_timeout

    async def analyze_image(
        self,
        image_url: str,
        query: str = "",
        detail: str = "auto",
    ) -> VisualCortexResult:
        """
        分析图片 — 支持 URL 或 base64

        Args:
            image_url: 图片 URL 或 data:image/...;base64,... 格式
            query: 用户附带的问题（可选）
            detail: 图片细节级别 auto|low|high
        """
        if not self.enabled:
            return VisualCortexResult()

        start = time.time()
        client = get_llm_client()

        extra = f"用户问题: {query}" if query else "请尽可能详细地描述图像内容。"
        system_prompt = IMAGE_ANALYZE_PROMPT.format(extra_instruction=extra)

        # 构建多模态消息（OpenAI Vision 格式）
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": detail},
                    },
                    {
                        "type": "text",
                        "text": query or "请分析这张图片。",
                    },
                ],
            },
        ]

        try:
            response = await client.complete(LLMRequest(
                messages=messages,
                model=self.model,
                temperature=0.2,
                max_tokens=2048,
                stream=False,
            ))
            latency = (time.time() - start) * 1000

            parsed = self._parse_visual_result(response.content)

            logger.info(
                "视觉皮层图像分析完成: objects=%d, has_text=%s (%.0fms)",
                len(parsed.get("objects", [])),
                bool(parsed.get("text_content")),
                latency,
            )

            return VisualCortexResult(
                description=parsed.get("description", response.content[:500]),
                objects=parsed.get("objects", []),
                text_content=parsed.get("text_content", ""),
                latency_ms=latency,
                confidence=float(parsed.get("confidence", 0.7)),
            )

        except Exception as e:
            logger.warning("视觉皮层图像分析失败: %s", e)
            return VisualCortexResult(
                latency_ms=(time.time() - start) * 1000,
            )

    async def analyze_video_frames(
        self,
        frame_urls: list[str],
        query: str = "",
    ) -> VisualCortexResult:
        """
        分析视频帧序列

        Args:
            frame_urls: 关键帧 URL/base64 列表（建议 4-8 帧）
            query: 用户附带的问题
        """
        if not self.enabled or not frame_urls:
            return VisualCortexResult()

        start = time.time()
        client = get_llm_client()

        extra = f"用户问题: {query}" if query else "请描述视频的主要内容和事件。"
        system_prompt = VIDEO_FRAMES_PROMPT.format(extra_instruction=extra)

        # 构建多帧消息
        content_parts = []
        for i, url in enumerate(frame_urls[:8]):  # 最多 8 帧
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": url, "detail": "low"},
            })
        content_parts.append({
            "type": "text",
            "text": query or f"以上是视频的 {len(frame_urls)} 个关键帧，请分析视频内容。",
        })

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_parts},
        ]

        try:
            response = await client.complete(LLMRequest(
                messages=messages,
                model=self.model,
                temperature=0.2,
                max_tokens=2048,
                stream=False,
            ))
            latency = (time.time() - start) * 1000

            parsed = self._parse_visual_result(response.content)

            logger.info(
                "视觉皮层视频分析完成: frames=%d (%.0fms)",
                len(frame_urls), latency,
            )

            return VisualCortexResult(
                description=parsed.get("description", response.content[:500]),
                objects=parsed.get("objects", []),
                text_content=parsed.get("text_content", ""),
                latency_ms=latency,
                confidence=float(parsed.get("confidence", 0.6)),
            )

        except Exception as e:
            logger.warning("视觉皮层视频分析失败: %s", e)
            return VisualCortexResult(
                latency_ms=(time.time() - start) * 1000,
            )

    async def describe_for_fusion(
        self,
        image_url: str,
        query: str = "",
    ) -> str:
        """
        为前额叶融合生成简洁图像描述

        返回可直接注入融合上下文的文本摘要。
        """
        result = await self.analyze_image(image_url, query)
        if not result.description:
            return ""

        parts = [f"[视觉皮层分析 — {self.model}]"]
        parts.append(f"图像描述: {result.description}")
        if result.objects:
            parts.append(f"识别物体: {', '.join(result.objects[:10])}")
        if result.text_content:
            parts.append(f"文字内容: {result.text_content[:500]}")
        return "\n".join(parts)

    def _parse_visual_result(self, content: str) -> dict:
        """解析视觉分析 JSON"""
        try:
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            logger.warning("视觉皮层JSON解析失败: %s", content[:200])
            return {"description": content[:500], "objects": [], "confidence": 0.5}
