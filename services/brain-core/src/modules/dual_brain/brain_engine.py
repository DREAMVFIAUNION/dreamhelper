"""仿生大脑引擎 — 丘脑(MiniMax路由) + 左脑皮层(GLM-5) + 右脑皮层(Qwen-3.5) + 脑干(GLM-5) + 小脑(Kimi-K2.5) via NVIDIA NIM"""

import asyncio
import logging
import time
from typing import AsyncGenerator, Optional
from dataclasses import dataclass, field

from .hemisphere import LeftHemisphere, RightHemisphere, HemisphereResult
from .cortex import Cortex, FusionStrategy
from .corpus_callosum import CorpusCallosum
from .activation import BrainActivation, TaskType
from .brain_config import BrainConfig
from .thalamus import Thalamus, ThalamusDecision
from .brainstem import Brainstem
from .cerebellum import Cerebellum, CerebellumResult
from .visual_cortex import VisualCortex, VisualCortexResult
from .hippocampus import Hippocampus, HippocampusContext
from .fusion_cache import FusionCache
from .weight_tracker import DynamicWeightTracker
from .mcp_thinking import run_sequential_thinking, build_thinking_enhanced_context

logger = logging.getLogger(__name__)

# 安全审计 P0-#1: 对外统一错误消息，不泄露内部细节
_SAFE_ERROR = "处理请求时遇到问题，请稍后重试"


@dataclass
class BrainOutput:
    """双脑融合最终输出"""
    content: str
    left_raw: str
    right_raw: str
    fusion_strategy: str
    left_latency_ms: float
    right_latency_ms: float
    total_latency_ms: float
    left_weight: float
    right_weight: float
    confidence: float = 0.0
    task_type: str = ""
    metadata: dict = field(default_factory=dict)


class BrainEngine:
    """
    仿生大脑引擎 — 按人类大脑神经科学设计的多LLM协作系统

    架构 (信息流):
      查询 → 丘脑(MiniMax 路由, ~1-3s)
        ├── 简单 → 脑干(MiniMax 快速响应, ~3-8s)
        └── 复杂 → 大脑皮层并行处理
                    ├─ 左脑皮层(GLM-5 744B 推理) ──┐
                    ├─ 右脑皮层(Qwen-3.5 397B 创意) ┤→ 前额叶融合 → 小脑校准 → 元认知质控
                    └─ 小脑(Kimi-K2.5 1T 条件并行) ─┘

    丘脑: 感觉信息中继, 路由决策 (MiniMax)
    脑干: 基础反射, 简单查询快速响应 (MiniMax) / 意图分析 (GLM-5 via NVIDIA)
    左脑皮层: 逻辑推理, 语言分析, 思维链 (GLM-5 744B via NVIDIA NIM)
    右脑皮层: 创意联想, 全局视角, 模式识别 (Qwen-3.5 397B via NVIDIA NIM)
    小脑: 代码精度, 技术校准 (Kimi-K2.5 1T via NVIDIA NIM)
    前额叶: 执行控制, 融合决策, 元认知 (GLM-5 via NVIDIA NIM)
    """

    # 小脑激活的任务类型
    CEREBELLUM_PARALLEL_TASKS = {TaskType.CODE, TaskType.MATH}
    CEREBELLUM_CALIBRATE_TASKS = {TaskType.COMPLEX, TaskType.CODE, TaskType.MATH}

    def __init__(self, config: Optional[BrainConfig] = None):
        self.config = config or BrainConfig()
        self.thalamus = Thalamus(config=self.config)
        self.left = LeftHemisphere(config=self.config)
        self.right = RightHemisphere(config=self.config)
        self.cortex = Cortex(config=self.config)
        self.corpus_callosum = CorpusCallosum()
        self.activation = BrainActivation()
        self.brainstem = Brainstem(config=self.config)
        self.cerebellum = Cerebellum(config=self.config)
        self.visual_cortex = VisualCortex(config=self.config)
        self.hippocampus = Hippocampus(config=self.config)
        self.fusion_cache = FusionCache(max_size=200, max_age=1800.0)
        self.weight_tracker = DynamicWeightTracker()

    def _resolve_strategy(self, name: str) -> FusionStrategy:
        """将策略名称解析为 FusionStrategy 枚举"""
        return FusionStrategy(name)

    async def think(
        self,
        query: str,
        context: dict,
        system_prompt: str = "",
        history: list[dict] | None = None,
        strategy: Optional[FusionStrategy] = None,
    ) -> BrainOutput:
        """
        双脑并行思考 — 核心方法

        流程:
        1. 任务分析 → 确定脑区激活权重
        2. asyncio.gather → 左右脑并行推理
        3. 皮层融合 → 合成最终输出
        """
        start_time = time.time()
        history = history or []

        # ── Step 1: 动态脑区激活 + 自适应权重 ──
        task_type = self.activation.detect_task_type(query)
        default_left, default_right = self.activation.get_weights(task_type)
        left_weight, right_weight = self.weight_tracker.get_adjusted_weights(
            task_type, default_left, default_right
        )

        # ── Step 2: 双脑并行推理 ──
        left_prompt = self.left.build_prompt(query, system_prompt, task_type)
        right_prompt = self.right.build_prompt(query, system_prompt, task_type)

        left_messages = [{"role": "system", "content": left_prompt}] + history + [{"role": "user", "content": query}]
        right_messages = [{"role": "system", "content": right_prompt}] + history + [{"role": "user", "content": query}]

        # 并行执行 — 这是核心！两个模型同时推理
        left_result, right_result = await asyncio.gather(
            self.left.process(left_messages),
            self.right.process(right_messages),
            return_exceptions=True,
        )

        # 容错: 如果某个半球失败，降级为单脑模式
        left_ok = isinstance(left_result, HemisphereResult)
        right_ok = isinstance(right_result, HemisphereResult)

        if not left_ok and not right_ok:
            left_err = left_result if isinstance(left_result, Exception) else "unknown"
            right_err = right_result if isinstance(right_result, Exception) else "unknown"
            raise RuntimeError(f"双脑均失败: 左脑={left_err}, 右脑={right_err}")

        if not left_ok:
            return BrainOutput(
                content=right_result.content,
                left_raw="[LEFT HEMISPHERE FAILED]",
                right_raw=right_result.content,
                fusion_strategy="single_right",
                left_latency_ms=0,
                right_latency_ms=right_result.latency_ms,
                total_latency_ms=(time.time() - start_time) * 1000,
                left_weight=0, right_weight=1.0,
                task_type=task_type.value,
            )

        if not right_ok:
            return BrainOutput(
                content=left_result.content,
                left_raw=left_result.content,
                right_raw="[RIGHT HEMISPHERE FAILED]",
                fusion_strategy="single_left",
                left_latency_ms=left_result.latency_ms,
                right_latency_ms=0,
                total_latency_ms=(time.time() - start_time) * 1000,
                left_weight=1.0, right_weight=0,
                task_type=task_type.value,
            )

        # ── Step 3: 胼胝体信息交换 ──
        agreement = self.corpus_callosum.exchange(left_result, right_result)

        # ── Step 4: 皮层融合 ──
        if strategy is None:
            strategy_name = self.activation.get_fusion_strategy_name(task_type)
            fusion_strategy = self._resolve_strategy(strategy_name)
        else:
            fusion_strategy = strategy

        # 冲突自动升级: 一致性过低 → 强制辩论
        if self.corpus_callosum.should_escalate_to_debate(left_result, right_result):
            fusion_strategy = FusionStrategy.DEBATE

        # ── 缓存检查 ──
        cached = self.fusion_cache.get(query, fusion_strategy.value, left_weight, right_weight)
        if cached:
            total_latency = (time.time() - start_time) * 1000
            return BrainOutput(
                content=cached.content,
                left_raw=left_result.content,
                right_raw=right_result.content,
                fusion_strategy=fusion_strategy.value,
                left_latency_ms=left_result.latency_ms,
                right_latency_ms=right_result.latency_ms,
                total_latency_ms=total_latency,
                left_weight=left_weight,
                right_weight=right_weight,
                confidence=cached.confidence,
                task_type=task_type.value,
                metadata={"agreement": round(agreement, 3), "cache_hit": True},
            )

        fused_content, confidence = await self.cortex.fuse(
            left_result=left_result,
            right_result=right_result,
            left_weight=left_weight,
            right_weight=right_weight,
            strategy=fusion_strategy,
            query=query,
        )

        # ── 写入缓存 + 记录权重 ──
        self.fusion_cache.put(query, fusion_strategy.value, left_weight, right_weight, fused_content, confidence)
        self.weight_tracker.record(task_type, left_weight, right_weight, confidence, fusion_strategy.value)

        total_latency = (time.time() - start_time) * 1000

        return BrainOutput(
            content=fused_content,
            left_raw=left_result.content,
            right_raw=right_result.content,
            fusion_strategy=fusion_strategy.value,
            left_latency_ms=left_result.latency_ms,
            right_latency_ms=right_result.latency_ms,
            total_latency_ms=total_latency,
            left_weight=left_weight,
            right_weight=right_weight,
            confidence=confidence,
            task_type=task_type.value,
            metadata={"agreement": round(agreement, 3)},
        )

    async def think_stream(
        self,
        query: str,
        context: dict,
        system_prompt: str = "",
        history: list[dict] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """
        仿生大脑流式思考 — 丘脑路由 → 脑干/皮层分支处理

        信息流 (模拟人类大脑):
          查询 → 丘脑(MiniMax 路由, ~1-3s)
            ├── 简单 → 脑干(MiniMax 快速响应, ~3-8s) → brain_done
            └── 复杂 → 大脑皮层(GLM+Qwen 并行) → 前额叶融合 → 小脑校准 → 元认知质控 → brain_done

        SSE 事件流:
        --- 丘脑路由 ---
        1.  {"type": "thalamus_routing", ...}
        2.  {"type": "thalamus_result", ...}

        --- 脑干快速路径 (简单查询) ---
        3a. {"type": "brainstem_responding", ...}
        4a. {"type": "chunk", "content": "..."}
        5a. {"type": "brain_done", ...}

        --- 皮层深度路径 (复杂查询) ---
        3b. {"type": "cortex_activating", ...}
        4b. {"type": "left_thinking", ...}  + {"type": "right_thinking", ...}
        5b. {"type": "cerebellum_thinking", ...}     ← 小脑并行(CODE/MATH)
        6b. {"type": "left_done", ...}  + {"type": "right_done", ...}
        7b. {"type": "brainstem_directive", ...}
        8b. {"type": "fusing", "strategy": "..."}
        9b. {"type": "chunk", "content": "..."}
        10b.{"type": "cerebellum_calibrating", ...}  ← 小脑校准(COMPLEX)
        11b.{"type": "brainstem_reviewing", ...}
        12b.{"type": "brain_done", "metadata": {...}}
        """
        history = history or []

        # ── Step 0: 丘脑路由 — 快速分类查询 ──
        yield {"type": "thalamus_routing", "content": f"丘脑({self.config.thalamus_model})正在分类..."}

        thalamus_decision = await self.thalamus.classify(query)

        # 从丘脑决策中获取路由信息
        task_type_str = thalamus_decision.task_type
        try:
            task_type = TaskType(task_type_str)
        except ValueError:
            task_type = self.activation.detect_task_type(query)

        yield {
            "type": "thalamus_result",
            "route": thalamus_decision.route,
            "complexity": thalamus_decision.complexity,
            "task_type": task_type.value,
            "weights": {"left": thalamus_decision.left_weight, "right": thalamus_decision.right_weight},
            "reasoning": thalamus_decision.reasoning,
            "latency_ms": round(thalamus_decision.latency_ms, 1),
        }

        # ── 脑干快速路径: 简单查询不经大脑皮层 ──
        if thalamus_decision.route == "brainstem":
            yield {"type": "brain_start", "task_type": task_type.value,
                   "weights": {"left": 0, "right": 0}, "mode": "brainstem"}
            yield {"type": "brainstem_responding",
                   "content": f"脑干({self.config.brainstem_response_model})快速响应中..."}

            brainstem_content = ""
            try:
                async for event in self.brainstem.quick_respond_stream(
                    query=query, system_prompt=system_prompt, history=history,
                ):
                    if event.get("type") == "chunk":
                        brainstem_content += event.get("content", "")
                        yield event
            except Exception as e:
                logger.error("脑干快速响应失败: %s", e, exc_info=True)
                yield {"type": "chunk", "content": _SAFE_ERROR}

            yield {
                "type": "brain_done",
                "metadata": {
                    "task_type": task_type.value,
                    "fusion_strategy": "brainstem_direct",
                    "confidence": 0.7,
                    "left_latency_ms": 0,
                    "right_latency_ms": 0,
                    "left_model": self.config.left_model,
                    "right_model": self.config.right_model,
                    "brainstem_model": self.config.brainstem_response_model,
                    "brainstem_latency_ms": round(thalamus_decision.latency_ms, 1),
                    "cerebellum_model": None,
                    "cerebellum_latency_ms": 0,
                    "cerebellum_mode": None,
                    "task_complexity": thalamus_decision.complexity,
                    "quality_score": None,
                    "calibration_has_errors": None,
                    "mcp_thinking": False,
                    "mcp_thinking_length": 0,
                    "thalamus_route": "brainstem",
                    "thalamus_latency_ms": round(thalamus_decision.latency_ms, 1),
                },
            }
            return  # 脑干路径结束，不进入大脑皮层

        # ══════════════════════════════════════════════════
        # 大脑皮层路径: 复杂查询 → 双脑并行 → 前额叶融合
        # ══════════════════════════════════════════════════

        # 使用丘脑决策的权重，结合自适应调整
        raw_left_w = thalamus_decision.left_weight
        raw_right_w = thalamus_decision.right_weight
        default_left_w, default_right_w = self.weight_tracker.get_adjusted_weights(
            task_type, raw_left_w, raw_right_w
        )
        default_strategy = self.activation.get_fusion_strategy_name(task_type)

        # 全局状态变量 — 用于 brain_done 元数据
        left_ok = False
        right_ok = False
        left_result = None
        right_result = None
        directive = None
        cerebellum_result: CerebellumResult | None = None
        cerebellum_parallel = thalamus_decision.cerebellum_needed or task_type in self.CEREBELLUM_PARALLEL_TASKS
        visual_cortex_result: VisualCortexResult | None = None
        hippocampus_ctx: HippocampusContext | None = None
        thinking_chain = None
        confidence = 0.0
        fusion_strategy = self._resolve_strategy(default_strategy)
        fused_chunks: list[str] = []
        brainstem_review = None
        cerebellum_calibration = None
        task_complexity = thalamus_decision.complexity
        should_calibrate = False
        left_weight = default_left_w
        right_weight = default_right_w

        yield {
            "type": "brain_start",
            "task_type": task_type.value,
            "weights": {"left": default_left_w, "right": default_right_w},
            "mode": "quad" if (self.brainstem.enabled and self.cerebellum.enabled) else ("triple" if self.brainstem.enabled else "dual"),
        }

        yield {"type": "cortex_activating", "content": "大脑皮层激活，启动并行深度处理..."}

        try:  # ← 保证 brain_done 总被发送
            # ── Step 1: 脑干分析 + 双脑 全部并行启动 ──
            left_prompt = self.left.build_prompt(query, system_prompt, task_type)
            right_prompt = self.right.build_prompt(query, system_prompt, task_type)

            left_task = asyncio.create_task(
                self.left.process(
                    [{"role": "system", "content": left_prompt}]
                    + history + [{"role": "user", "content": query}]
                )
            )
            right_task = asyncio.create_task(
                self.right.process(
                    [{"role": "system", "content": right_prompt}]
                    + history + [{"role": "user", "content": query}]
                )
            )

            # 脑干并行启动（不阻塞双脑）
            brainstem_task = None
            if self.brainstem.enabled:
                brainstem_task = asyncio.create_task(
                    self.brainstem.pre_analyze(query, history)
                )
                yield {"type": "brainstem_analyzing", "content": f"脑干({self.config.brainstem_model})正在深度分析..."}

            # 小脑并行启动（CODE/MATH 任务触发）
            cerebellum_task = None
            if self.cerebellum.enabled and cerebellum_parallel:
                cerebellum_task = asyncio.create_task(
                    self.cerebellum.generate_code(query, history)
                )
                yield {"type": "cerebellum_thinking", "content": f"小脑({self.config.cerebellum_model})正在精确编码..."}

            # MCP Sequential Thinking 并行启动（仅在服务器已连接时）
            thinking_task = None
            is_likely_complex = task_type in (TaskType.CODE, TaskType.MATH, TaskType.EXPERT)
            if is_likely_complex:
                try:
                    from ..mcp.mcp_client_manager import MCPClientManager
                    conn = MCPClientManager.get_connection("sequential-thinking")
                    if conn and conn.connected:
                        thinking_task = asyncio.create_task(
                            run_sequential_thinking(query, "complex", timeout=30.0)
                        )
                        yield {"type": "mcp_thinking", "content": "结构化思维链正在分析..."}
                except Exception:
                    pass  # MCP 不可用，跳过

            # 视觉皮层并行启动（丘脑检测到视觉输入时触发）
            visual_cortex_task = None
            if self.visual_cortex.enabled and thalamus_decision.visual_needed:
                image_url = context.get("image_url", "")
                if image_url:
                    visual_cortex_task = asyncio.create_task(
                        self.visual_cortex.analyze_image(image_url, query)
                    )
                    yield {"type": "visual_cortex_analyzing", "content": f"视觉皮层({self.config.visual_cortex_model})正在分析图像..."}

            # 海马体并行启动（丘脑检测到需要记忆检索时触发）
            hippocampus_task = None
            if self.hippocampus.enabled and thalamus_decision.hippocampus_needed:
                user_id = context.get("user_id", "")
                user_facts = context.get("user_facts", {})
                hippocampus_task = asyncio.create_task(
                    self.hippocampus.recall(query, user_id, history, user_facts)
                )
                yield {"type": "hippocampus_recalling", "content": f"海马体({self.config.hippocampus_model})正在检索记忆..."}

            yield {"type": "left_thinking", "content": f"左脑({self.config.left_model})正在逻辑分析..."}
            yield {"type": "right_thinking", "content": f"右脑({self.config.right_model})正在深度推理..."}

            # ── Step 2: 等待全部并行任务完成（带超时保护）──
            tasks = [left_task, right_task]
            if brainstem_task:
                tasks.append(brainstem_task)
            if cerebellum_task:
                tasks.append(cerebellum_task)
            if thinking_task:
                tasks.append(thinking_task)
            if visual_cortex_task:
                tasks.append(visual_cortex_task)
            if hippocampus_task:
                tasks.append(hippocampus_task)

            # 总超时 = 最慢半球超时 + 10s 余量
            gather_timeout = max(self.config.left_timeout, self.config.right_timeout) + 30.0
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=gather_timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("并行任务总超时 (%.0fs)，取消剩余任务", gather_timeout)
                for t in tasks:
                    if not t.done():
                        t.cancel()
                # 收集已完成的结果
                results = []
                for t in tasks:
                    if t.done() and not t.cancelled():
                        try:
                            results.append(t.result())
                        except Exception as e:
                            results.append(e)
                    else:
                        results.append(TimeoutError("task timed out"))

            left_result = results[0] if len(results) > 0 else TimeoutError("no result")
            right_result = results[1] if len(results) > 1 else TimeoutError("no result")
            idx = 2

            if brainstem_task:
                directive = results[idx] if idx < len(results) else None
                idx += 1
            if cerebellum_task:
                cerebellum_result = results[idx] if idx < len(results) else None
                idx += 1
            if thinking_task:
                thinking_chain = results[idx] if idx < len(results) else None
                idx += 1
            if visual_cortex_task:
                visual_cortex_result = results[idx] if idx < len(results) else None
                idx += 1
            if hippocampus_task:
                hippocampus_ctx = results[idx] if idx < len(results) else None
                idx += 1

            # 视觉皮层容错
            if isinstance(visual_cortex_result, Exception):
                logger.warning("视觉皮层分析失败: %s", visual_cortex_result)
                visual_cortex_result = None

            # 海马体容错
            if isinstance(hippocampus_ctx, Exception):
                logger.warning("海马体记忆检索失败: %s", hippocampus_ctx)
                hippocampus_ctx = None

            # 脑干容错
            if isinstance(directive, Exception):
                logger.warning("脑干分析失败: %s", directive)
                directive = None

            # 小脑容错
            if isinstance(cerebellum_result, Exception):
                logger.warning("小脑代码生成失败: %s", cerebellum_result)
                cerebellum_result = None

            # 思维链容错
            if isinstance(thinking_chain, Exception):
                logger.warning("思维链分析失败: %s", thinking_chain)
                thinking_chain = None

            left_ok = isinstance(left_result, HemisphereResult)
            right_ok = isinstance(right_result, HemisphereResult)

            if left_ok:
                yield {"type": "left_done", "latency_ms": round(left_result.latency_ms, 1)}
            else:
                yield {"type": "left_done", "latency_ms": 0, "error": str(left_result)}
            if right_ok:
                yield {"type": "right_done", "latency_ms": round(right_result.latency_ms, 1)}
            else:
                yield {"type": "right_done", "latency_ms": 0, "error": str(right_result)}

            # 输出小脑结果（与双脑完全并行，零额外延迟）
            if cerebellum_result and isinstance(cerebellum_result, CerebellumResult) and cerebellum_result.content:
                yield {
                    "type": "cerebellum_done",
                    "latency_ms": round(cerebellum_result.latency_ms, 1),
                    "code_blocks": len(cerebellum_result.code_blocks),
                    "language": cerebellum_result.language,
                }

            # 输出脑干指令（此时已完成，不增加延迟）
            if directive:
                yield {
                    "type": "brainstem_directive",
                    "complexity": directive.task_complexity,
                    "strategy": directive.recommended_strategy,
                    "weights": {"left": round(directive.left_weight, 2), "right": round(directive.right_weight, 2)},
                    "focus": directive.focus_instructions,
                    "reasoning": directive.reasoning_trace[:500] if directive.reasoning_trace else "",
                    "latency_ms": round(directive.latency_ms, 1),
                }

            # 输出思维链结果（与脑干/双脑完全并行，零额外延迟）
            if thinking_chain:
                yield {
                    "type": "mcp_thinking_done",
                    "content": thinking_chain[:500],
                    "full_length": len(thinking_chain),
                }

            # 输出视觉皮层结果
            if visual_cortex_result and isinstance(visual_cortex_result, VisualCortexResult) and visual_cortex_result.description:
                yield {
                    "type": "visual_cortex_done",
                    "latency_ms": round(visual_cortex_result.latency_ms, 1),
                    "objects": visual_cortex_result.objects[:10],
                    "has_text": bool(visual_cortex_result.text_content),
                }

            # 输出海马体结果
            if hippocampus_ctx and isinstance(hippocampus_ctx, HippocampusContext) and hippocampus_ctx.relevant_memories:
                yield {
                    "type": "hippocampus_done",
                    "memories_count": len(hippocampus_ctx.relevant_memories),
                    "tokens_used": hippocampus_ctx.total_tokens,
                    "latency_ms": round(hippocampus_ctx.latency_ms, 1),
                }

            # ── 构建融合增强上下文 (思维链 + 脑干指令 + 小脑代码) ──
            cerebellum_context = ""
            if cerebellum_result and isinstance(cerebellum_result, CerebellumResult) and cerebellum_result.content:
                cerebellum_context = f"\n\n[小脑技术基准 — {self.config.cerebellum_model}]\n{cerebellum_result.content[:2000]}"

            fusion_extra_context = build_thinking_enhanced_context(
                thinking_chain=thinking_chain,
                brainstem_focus=directive.focus_instructions if directive else "",
            )
            fusion_extra_context += cerebellum_context

            # 视觉皮层上下文注入融合
            if visual_cortex_result and isinstance(visual_cortex_result, VisualCortexResult) and visual_cortex_result.description:
                fusion_extra_context += f"\n\n[视觉皮层分析 — {self.config.visual_cortex_model}]\n{visual_cortex_result.description}"
                if visual_cortex_result.text_content:
                    fusion_extra_context += f"\n图中文字: {visual_cortex_result.text_content[:500]}"

            # 海马体记忆上下文注入融合
            if hippocampus_ctx and isinstance(hippocampus_ctx, HippocampusContext):
                hippocampus_context_str = self.hippocampus.build_context_for_fusion(hippocampus_ctx)
                if hippocampus_context_str:
                    fusion_extra_context += hippocampus_context_str

            # ── 脑干智能覆盖: 使用脑干推荐的权重和策略 ──
            task_complexity = directive.task_complexity if directive else "medium"
            if directive:
                left_weight = directive.left_weight
                right_weight = directive.right_weight
                strategy_name = directive.recommended_strategy
            else:
                strategy_name = default_strategy

            # ── Step 3: 皮层融合 (流式) ──
            fusion_strategy = self._resolve_strategy(strategy_name)

            if left_ok and right_ok:
                # 冲突自动升级
                if self.corpus_callosum.should_escalate_to_debate(left_result, right_result):
                    fusion_strategy = FusionStrategy.DEBATE

                yield {"type": "fusing", "strategy": fusion_strategy.value}

                self.corpus_callosum.exchange(left_result, right_result)

                confidence = 0.8
                try:
                    async for event in self.cortex.fuse_stream(
                        left_result, right_result, left_weight, right_weight, fusion_strategy, query,
                        extra_context=fusion_extra_context,
                    ):
                        if event.get("type") == "chunk":
                            yield {"type": "chunk", "content": event["content"]}
                            fused_chunks.append(event["content"])
                        elif event.get("type") == "fusion_meta":
                            confidence = event.get("confidence", 0.8)
                except Exception as e:
                    logger.warning("融合失败，降级为主半球输出: %s", e)
                    fallback = left_result.content if left_weight >= right_weight else right_result.content
                    yield {"type": "chunk", "content": fallback}
                    fused_chunks.append(fallback)
                    confidence = 0.5
            elif left_ok:
                yield {"type": "fusing", "strategy": "single_left"}
                yield {"type": "chunk", "content": left_result.content}
                fused_chunks.append(left_result.content)
                confidence = 0.5
            elif right_ok:
                yield {"type": "fusing", "strategy": "single_right"}
                yield {"type": "chunk", "content": right_result.content}
                fused_chunks.append(right_result.content)
                confidence = 0.5
            else:
                left_err = str(left_result)[:200] if left_result else "unknown"
                right_err = str(right_result)[:200] if right_result else "unknown"
                logger.error("双脑均失败详情: left=%s, right=%s", left_err, right_err)
                yield {"type": "fusing", "strategy": "fallback"}
                yield {"type": "chunk", "content": _SAFE_ERROR}
                confidence = 0.0

            # ── Step 4: 小脑后置校准 (CODE/MATH/COMPLEX 任务触发) ──
            should_calibrate = (
                self.cerebellum.enabled
                and left_ok and right_ok
                and task_type in self.CEREBELLUM_CALIBRATE_TASKS
                and task_complexity in ("complex", "expert")
                and not cerebellum_parallel  # 并行模式已参与融合，不需要再校准
            )
            if should_calibrate:
                try:
                    yield {"type": "cerebellum_calibrating", "content": "小脑正在技术校准..."}
                    fused_for_calibrate = "".join(fused_chunks)
                    async for cal_event in self.cerebellum.calibrate_stream(fused_for_calibrate, query):
                        if cal_event.get("type") == "calibration_result":
                            cerebellum_calibration = cal_event
                        elif cal_event.get("type") == "calibration_code":
                            yield {"type": "chunk", "content": cal_event["content"]}
                except Exception as e:
                    logger.warning("小脑校准失败: %s", e)

            # ── Step 5: 脑干后处理 (仅复杂/专家级任务才触发) ──
            if self.brainstem.enabled and left_ok and right_ok and task_complexity in ("complex", "expert"):
                try:
                    yield {"type": "brainstem_reviewing", "content": "脑干正在质量评估..."}
                    fused_content = "".join(fused_chunks)
                    async for review_event in self.brainstem.post_review_stream(
                        fused_content=fused_content,
                        left_raw=left_result.content if left_ok else "",
                        right_raw=right_result.content if right_ok else "",
                        query=query,
                        task_complexity=task_complexity,
                    ):
                        if review_event.get("type") == "review_result":
                            brainstem_review = review_event
                        elif review_event.get("type") == "enhancement_chunk":
                            yield {"type": "chunk", "content": review_event["content"]}
                except Exception as e:
                    logger.warning("脑干后处理失败: %s", e)

            # ── 记录权重跟踪 ──
            if left_ok and right_ok:
                self.weight_tracker.record(
                    task_type, left_weight, right_weight, confidence,
                    fusion_strategy.value,
                )

        except Exception as e:
            # 未预期的全局错误 — 记录并降级
            logger.error("think_stream 未预期错误: %s", e, exc_info=True)
            if not fused_chunks:
                yield {"type": "chunk", "content": _SAFE_ERROR}

        finally:
            # ★ brain_done 必定发送 — 保证前端收到结束信号
            yield {
                "type": "brain_done",
                "metadata": {
                    "task_type": task_type.value,
                    "fusion_strategy": fusion_strategy.value if left_ok and right_ok else "single",
                    "confidence": round(confidence, 3),
                    "left_latency_ms": round(left_result.latency_ms, 1) if left_ok else 0,
                    "right_latency_ms": round(right_result.latency_ms, 1) if right_ok else 0,
                    "left_model": self.config.left_model,
                    "right_model": self.config.right_model,
                    "brainstem_model": self.config.brainstem_model if self.brainstem.enabled else None,
                    "brainstem_latency_ms": round(directive.latency_ms, 1) if directive else 0,
                    "cerebellum_model": self.config.cerebellum_model if self.cerebellum.enabled else None,
                    "cerebellum_latency_ms": round(cerebellum_result.latency_ms, 1) if (cerebellum_result and isinstance(cerebellum_result, CerebellumResult)) else 0,
                    "cerebellum_mode": "parallel" if cerebellum_parallel else ("calibrate" if should_calibrate else None),
                    "task_complexity": task_complexity,
                    "quality_score": brainstem_review.get("quality_score") if brainstem_review else None,
                    "calibration_has_errors": cerebellum_calibration.get("has_errors") if cerebellum_calibration else None,
                    "visual_cortex_model": self.config.visual_cortex_model if self.visual_cortex.enabled else None,
                    "visual_cortex_latency_ms": round(visual_cortex_result.latency_ms, 1) if (visual_cortex_result and isinstance(visual_cortex_result, VisualCortexResult)) else 0,
                    "hippocampus_model": self.config.hippocampus_model if self.hippocampus.enabled else None,
                    "hippocampus_latency_ms": round(hippocampus_ctx.latency_ms, 1) if (hippocampus_ctx and isinstance(hippocampus_ctx, HippocampusContext)) else 0,
                    "hippocampus_memories": len(hippocampus_ctx.relevant_memories) if (hippocampus_ctx and isinstance(hippocampus_ctx, HippocampusContext)) else 0,
                    "mcp_thinking": bool(thinking_chain),
                    "mcp_thinking_length": len(thinking_chain) if thinking_chain else 0,
                    "thalamus_route": "cortex",
                    "thalamus_latency_ms": round(thalamus_decision.latency_ms, 1),
                },
            }

    async def think_single(self, query: str, system_prompt: str = "", history: list[dict] | None = None) -> str:
        """单脑快速模式 — 简短消息直接走左脑"""
        history = history or []
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": query}]
        result = await self.left.process(messages)
        return result.content

    def get_stats(self) -> dict:
        """仿生大脑运行统计"""
        return {
            "enabled": self.config.enabled,
            "thalamus_model": self.config.thalamus_model,
            "thalamus_enabled": self.config.thalamus_enabled,
            "left_model": self.config.left_model,
            "right_model": self.config.right_model,
            "judge_model": self.config.judge_model,
            "fusion_model": self.config.fusion_model,
            "brainstem_model": self.config.brainstem_model,
            "brainstem_response_model": self.config.brainstem_response_model,
            "brainstem_enabled": self.config.brainstem_enabled,
            "cerebellum_model": self.config.cerebellum_model,
            "cerebellum_enabled": self.config.cerebellum_enabled,
            "visual_cortex_model": self.config.visual_cortex_model,
            "visual_cortex_enabled": self.config.visual_cortex_enabled,
            "hippocampus_model": self.config.hippocampus_model,
            "hippocampus_enabled": self.config.hippocampus_enabled,
            "consciousness_model": self.config.consciousness_model,
            "consciousness_enabled": self.config.consciousness_enabled,
            "corpus_callosum": self.corpus_callosum.get_stats(),
            "fusion_cache": self.fusion_cache.get_stats(),
            "weight_tracker": self.weight_tracker.get_stats(),
        }
