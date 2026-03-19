"""Prometheus 指标采集 + 内置指标收集器

两套指标系统:
1. prometheus_client — 供 Prometheus/Grafana 拉取 (需安装 prometheus_client)
2. InMemoryMetrics — 零依赖内置指标，供 /metrics API 和 Sentry 上报
"""

import time
import logging
from collections import defaultdict
from typing import Optional

logger = logging.getLogger(__name__)

# ── 尝试导入 prometheus_client (可选依赖) ──

try:
    from prometheus_client import Counter, Histogram, Gauge

    llm_requests_total = Counter(
        "llm_requests_total",
        "Total LLM API requests",
        ["provider", "model", "status"],
    )
    llm_request_duration = Histogram(
        "llm_request_duration_seconds",
        "LLM request duration",
        ["provider", "model"],
        buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    )
    llm_tokens_total = Counter(
        "llm_tokens_total",
        "Total tokens consumed",
        ["provider", "model", "type"],
    )
    agent_runs_total = Counter(
        "agent_runs_total",
        "Total agent runs",
        ["agent_type", "status"],
    )
    agent_steps_total = Counter(
        "agent_steps_total",
        "Total agent reasoning steps",
        ["agent_type"],
    )
    rag_queries_total = Counter(
        "rag_queries_total",
        "Total RAG queries",
        ["status"],
    )
    rag_retrieval_duration = Histogram(
        "rag_retrieval_duration_seconds",
        "RAG retrieval duration",
        buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
    )
    active_connections = Gauge(
        "active_connections",
        "Current active SSE/WebSocket connections",
        ["type"],
    )

    # ── 三脑指标 ──
    brain_fusions_total = Counter(
        "brain_fusions_total",
        "Total brain fusion operations",
        ["strategy", "task_type"],
    )
    brain_fusion_duration = Histogram(
        "brain_fusion_duration_seconds",
        "Brain fusion total latency",
        ["strategy"],
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0],
    )
    brain_cache_hits = Counter(
        "brain_cache_hits_total",
        "Fusion cache hits",
    )
    brain_cache_misses = Counter(
        "brain_cache_misses_total",
        "Fusion cache misses",
    )

    # ── 工作流指标 ──
    workflow_executions_total = Counter(
        "workflow_executions_total",
        "Total workflow executions",
        ["status"],
    )
    workflow_execution_duration = Histogram(
        "workflow_execution_duration_seconds",
        "Workflow execution duration",
        buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
    )

    HAS_PROMETHEUS = True

except ImportError:
    HAS_PROMETHEUS = False
    logger.info("prometheus_client not installed, using built-in metrics only")


# ── 零依赖内置指标收集器 ──────────────────────────────────

class InMemoryMetrics:
    """零依赖内置指标 — 供 /metrics API 使用"""

    def __init__(self):
        self._counters: dict[str, int] = defaultdict(int)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}
        self._start_time = time.time()

    def inc(self, name: str, value: int = 1, labels: Optional[dict] = None):
        """递增计数器"""
        key = self._key(name, labels)
        self._counters[key] += value

    def observe(self, name: str, value: float, labels: Optional[dict] = None):
        """记录直方图观测值"""
        key = self._key(name, labels)
        hist = self._histograms[key]
        hist.append(value)
        # 保留最近1000个观测值
        if len(hist) > 1000:
            self._histograms[key] = hist[-500:]

    def set_gauge(self, name: str, value: float, labels: Optional[dict] = None):
        """设置仪表值"""
        key = self._key(name, labels)
        self._gauges[key] = value

    def snapshot(self) -> dict:
        """导出指标快照"""
        uptime = time.time() - self._start_time

        # 计算直方图摘要
        hist_summary = {}
        for key, values in self._histograms.items():
            if values:
                sorted_v = sorted(values)
                n = len(sorted_v)
                hist_summary[key] = {
                    "count": n,
                    "avg": round(sum(sorted_v) / n, 3),
                    "p50": round(sorted_v[n // 2], 3),
                    "p95": round(sorted_v[int(n * 0.95)], 3) if n >= 20 else None,
                    "p99": round(sorted_v[int(n * 0.99)], 3) if n >= 100 else None,
                    "max": round(sorted_v[-1], 3),
                }

        return {
            "uptime_seconds": round(uptime, 1),
            "counters": dict(self._counters),
            "histograms": hist_summary,
            "gauges": dict(self._gauges),
        }

    @staticmethod
    def _key(name: str, labels: Optional[dict] = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# 全局单例
_metrics: Optional[InMemoryMetrics] = None


def get_metrics() -> InMemoryMetrics:
    global _metrics
    if _metrics is None:
        _metrics = InMemoryMetrics()
    return _metrics
