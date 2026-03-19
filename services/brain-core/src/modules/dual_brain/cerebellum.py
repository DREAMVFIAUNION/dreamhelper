"""小脑 (Cerebellum) — 代码精度与技术校准模块

职责:
1. GENERATE  — CODE/MATH 任务时并行生成精确代码（与左右脑并行）
2. CALIBRATE — COMPLEX/EXPERT 任务后置校准融合输出中的技术错误

使用 Kimi K2.5 Code（代码专精模型）
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from .brain_config import BrainConfig
from ..llm.llm_client import get_llm_client
from ..llm.types import LLMRequest

logger = logging.getLogger(__name__)


@dataclass
class CerebellumResult:
    """小脑输出结果"""
    content: str = ""
    code_blocks: list[str] = field(default_factory=list)
    language: str = ""
    latency_ms: float = 0.0
    verified: bool = False
    verification_output: str = ""


# ── 小脑代码生成 Prompt ──────────────────────────────────

CODE_GENERATE_PROMPT = """你是一个**代码精度专家**，专注于生成正确、可运行、高质量的代码。

要求:
- 输出完整可运行的代码，不要省略任何部分
- 包含必要的 import 语句
- 包含至少一个测试用例或示例调用
- 代码风格简洁，变量命名清晰
- 如果是算法题，分析时间/空间复杂度
- 用中文注释关键逻辑

用户问题: {query}"""


# ── 小脑技术校准 Prompt ──────────────────────────────────

CALIBRATE_PROMPT = """你是一个**技术校准专家**，负责审查AI回答中的技术错误。

以下是对用户问题的回答，请仔细审查其中的技术内容（代码、数据、公式、逻辑推理），找出并修正错误。

**用户问题**: {query}

**待审查回答**:
{content}

请输出 JSON（不要输出其他内容）:
```json
{{
  "has_errors": true|false,
  "errors": [
    {{"location": "错误位置描述", "issue": "问题描述", "fix": "修正建议"}}
  ],
  "corrected_code": "如果有代码错误，输出修正后的完整代码；否则留空",
  "confidence": 0.0-1.0
}}
```

审查重点:
- 代码语法错误、逻辑错误、边界条件遗漏
- 数学计算或公式错误
- API 用法错误、参数错误
- 安全隐患（SQL注入、XSS等）
- 如果没有技术错误，has_errors=false 即可"""


class Cerebellum:
    """
    小脑 — 四脑架构的代码精度与技术校准模块

    如同人类小脑负责运动协调和精确控制，
    Cerebellum 专注于:
    - 代码生成精度（比通用模型更精确的代码输出）
    - 技术校准（审查融合输出中的技术性错误）
    - 执行验证（与 AgentBay 联动，验证代码可运行性）
    """

    def __init__(self, config: BrainConfig):
        self.config = config
        self.model = config.cerebellum_model
        self.enabled = config.cerebellum_enabled

    async def generate_code(
        self,
        query: str,
        history: list[dict] | None = None,
    ) -> CerebellumResult:
        """
        代码生成 — CODE/MATH 任务时与左右脑并行调用

        生成精确、可运行的代码，作为融合时的"技术基准"。
        """
        if not self.enabled:
            return CerebellumResult()

        start = time.time()
        client = get_llm_client()
        history = history or []

        prompt = CODE_GENERATE_PROMPT.format(query=query)
        messages = [{"role": "system", "content": prompt}] + history + [{"role": "user", "content": query}]

        try:
            response = await client.complete(LLMRequest(
                messages=messages,
                model=self.model,
                temperature=0.2,
                max_tokens=6144,
                stream=False,
            ))
            latency = (time.time() - start) * 1000

            code_blocks = self._extract_code_blocks(response.content)
            language = self._detect_language(code_blocks)

            logger.info(
                "小脑代码生成完成: %d个代码块, 语言=%s (%.0fms)",
                len(code_blocks), language, latency,
            )

            return CerebellumResult(
                content=response.content,
                code_blocks=code_blocks,
                language=language,
                latency_ms=latency,
            )

        except Exception as e:
            logger.warning("小脑代码生成失败: %s", e)
            return CerebellumResult(
                latency_ms=(time.time() - start) * 1000,
            )

    async def calibrate(
        self,
        fused_content: str,
        query: str,
    ) -> CerebellumResult:
        """
        技术校准 — COMPLEX/EXPERT 任务融合后进行后置审查

        检查融合输出中的代码错误、逻辑错误、数据错误。
        """
        if not self.enabled:
            return CerebellumResult()

        start = time.time()
        client = get_llm_client()

        # 截断避免 prompt 过大
        content_truncated = fused_content[:4000]
        prompt = CALIBRATE_PROMPT.format(query=query, content=content_truncated)

        try:
            response = await client.complete(LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,
                max_tokens=4096,
                stream=False,
            ))
            latency = (time.time() - start) * 1000

            review = self._parse_calibration(response.content)

            logger.info(
                "小脑校准完成: has_errors=%s, confidence=%.2f (%.0fms)",
                review.get("has_errors", False),
                review.get("confidence", 0.0),
                latency,
            )

            corrected_code = review.get("corrected_code", "")
            code_blocks = [corrected_code] if corrected_code else []

            return CerebellumResult(
                content=response.content,
                code_blocks=code_blocks,
                latency_ms=latency,
                verified=not review.get("has_errors", False),
            )

        except Exception as e:
            logger.warning("小脑校准失败: %s", e)
            return CerebellumResult(
                latency_ms=(time.time() - start) * 1000,
            )

    async def calibrate_stream(
        self,
        fused_content: str,
        query: str,
    ) -> AsyncGenerator[dict, None]:
        """
        流式校准 — 输出校准事件供 BrainEngine 使用

        事件类型:
        - {"type": "calibration_result", "has_errors": bool, "errors": [...]}
        - {"type": "calibration_code", "content": "修正后的代码"}
        """
        result = await self.calibrate(fused_content, query)

        if not result.content:
            yield {"type": "calibration_skip", "reason": "cerebellum disabled or failed"}
            return

        review = self._parse_calibration(result.content)

        yield {
            "type": "calibration_result",
            "has_errors": review.get("has_errors", False),
            "errors": review.get("errors", []),
            "confidence": review.get("confidence", 0.0),
            "latency_ms": round(result.latency_ms, 1),
        }

        # 如果有修正代码，流式输出
        corrected = review.get("corrected_code", "")
        if corrected:
            chunk_size = 30
            for i in range(0, len(corrected), chunk_size):
                yield {"type": "calibration_code", "content": corrected[i:i+chunk_size]}

    def _extract_code_blocks(self, content: str) -> list[str]:
        """从回答中提取所有代码块"""
        pattern = r'```(?:\w+)?\n(.*?)```'
        blocks = re.findall(pattern, content, re.DOTALL)
        return [b.strip() for b in blocks if b.strip()]

    def _detect_language(self, code_blocks: list[str]) -> str:
        """简单检测代码语言"""
        if not code_blocks:
            return ""
        first = code_blocks[0]
        if "def " in first or "import " in first or "print(" in first:
            return "python"
        if "function " in first or "const " in first or "console.log" in first:
            return "javascript"
        if "SELECT " in first.upper() or "FROM " in first.upper():
            return "sql"
        return "unknown"

    def _parse_calibration(self, content: str) -> dict:
        """解析校准 JSON"""
        try:
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            logger.warning("小脑校准JSON解析失败: %s", content[:200])
            return {"has_errors": False, "errors": [], "confidence": 0.5}
