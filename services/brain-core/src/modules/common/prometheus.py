"""
Prometheus 指标收集器 — 轻量级实现（无外部依赖）
"""

import time
from collections import defaultdict
from typing import Dict


class SimpleMetrics:
    """简易指标收集器（生产环境建议替换为 prometheus_client）"""

    _counters: Dict[str, int] = defaultdict(int)
    _histograms: Dict[str, list] = defaultdict(list)
    _gauges: Dict[str, float] = defaultdict(float)
    _start_time: float = time.time()

    @classmethod
    def inc(cls, name: str, value: int = 1, labels: dict | None = None):
        key = cls._key(name, labels)
        cls._counters[key] += value

    @classmethod
    def set_gauge(cls, name: str, value: float, labels: dict | None = None):
        key = cls._key(name, labels)
        cls._gauges[key] = value

    @classmethod
    def observe(cls, name: str, value: float, labels: dict | None = None):
        key = cls._key(name, labels)
        cls._histograms[key].append(value)
        # 保留最近 1000 个样本
        if len(cls._histograms[key]) > 1000:
            cls._histograms[key] = cls._histograms[key][-500:]

    @classmethod
    def _key(cls, name: str, labels: dict | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    @classmethod
    def export_text(cls) -> str:
        """导出 Prometheus 文本格式"""
        lines = []
        uptime = time.time() - cls._start_time

        lines.append(f"# HELP process_uptime_seconds Process uptime")
        lines.append(f"# TYPE process_uptime_seconds gauge")
        lines.append(f"process_uptime_seconds {uptime:.2f}")

        for key, val in cls._counters.items():
            lines.append(f"{key} {val}")

        for key, val in cls._gauges.items():
            lines.append(f"{key} {val}")

        for key, samples in cls._histograms.items():
            if samples:
                count = len(samples)
                total = sum(samples)
                avg = total / count
                lines.append(f"{key}_count {count}")
                lines.append(f"{key}_sum {total:.4f}")
                lines.append(f"{key}_avg {avg:.4f}")

        return "\n".join(lines) + "\n"

    @classmethod
    def to_dict(cls) -> dict:
        result = {
            "uptime_seconds": round(time.time() - cls._start_time, 2),
            "counters": dict(cls._counters),
            "gauges": dict(cls._gauges),
            "histograms": {},
        }
        for key, samples in cls._histograms.items():
            if samples:
                result["histograms"][key] = {
                    "count": len(samples),
                    "sum": round(sum(samples), 4),
                    "avg": round(sum(samples) / len(samples), 4),
                    "min": round(min(samples), 4),
                    "max": round(max(samples), 4),
                }
        return result


metrics = SimpleMetrics()
