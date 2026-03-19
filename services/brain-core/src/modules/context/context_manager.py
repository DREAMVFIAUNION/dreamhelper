"""上下文管理器 (ContextManager) — Token 追踪 + 自动压缩

功能:
  - Token 使用量追踪（近似计算）
  - 92% 阈值自动压缩（保留关键文件内容和工具执行结果）
  - 分层存储: 当前对话 → 压缩历史 → 项目记忆文件
  - DREAMHELP.md 项目记忆（类似 CLAUDE.md）
    - 自动从对话中提取项目约定
    - 下次会话自动加载
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("context.manager")


@dataclass
class ContextStats:
    """上下文统计"""
    total_tokens: int = 0
    max_tokens: int = 128_000
    messages_count: int = 0
    compressed_count: int = 0
    compression_ratio: float = 0.0

    @property
    def usage_pct(self) -> float:
        if self.max_tokens == 0:
            return 0.0
        return self.total_tokens / self.max_tokens

    @property
    def needs_compression(self) -> bool:
        return self.usage_pct >= 0.92


def estimate_tokens(text: str) -> int:
    """近似 token 计算（中文约 1.5 char/token，英文约 4 char/token）"""
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    en_chars = len(text) - cn_chars
    return int(cn_chars * 0.67 + en_chars * 0.25)


class ContextManager:
    """上下文管理器 — Token 追踪 + 压缩 + 项目记忆"""

    COMPRESSION_THRESHOLD = 0.92
    KEEP_RECENT_MESSAGES = 6  # 压缩时保留最近 N 条消息

    def __init__(self, max_tokens: int = 128_000, project_dir: str = ""):
        self.max_tokens = max_tokens
        self.project_dir = project_dir
        self._messages: list[dict] = []
        self._compressed_summary: str = ""
        self._stats = ContextStats(max_tokens=max_tokens)

    def add_message(self, role: str, content: str):
        """添加消息并更新 token 计数"""
        msg = {"role": role, "content": content}
        self._messages.append(msg)
        tokens = estimate_tokens(content)
        self._stats.total_tokens += tokens
        self._stats.messages_count += 1

        # 检查是否需要压缩
        if self._stats.needs_compression:
            self._compress()

    def get_messages(self) -> list[dict]:
        """获取当前消息列表（含压缩摘要）"""
        messages = []

        # 注入项目记忆
        project_memory = self._load_project_memory()
        if project_memory:
            messages.append({
                "role": "system",
                "content": f"## 项目记忆 (DREAMHELP.md)\n{project_memory}",
            })

        # 注入压缩摘要
        if self._compressed_summary:
            messages.append({
                "role": "system",
                "content": f"## 对话历史摘要\n{self._compressed_summary}",
            })

        # 当前消息
        messages.extend(self._messages)
        return messages

    def _compress(self):
        """压缩历史消息 — 保留最近 N 条，旧消息生成摘要"""
        if len(self._messages) <= self.KEEP_RECENT_MESSAGES:
            return

        # 分割: 旧消息 + 保留消息
        old_messages = self._messages[:-self.KEEP_RECENT_MESSAGES]
        keep_messages = self._messages[-self.KEEP_RECENT_MESSAGES:]

        # 生成压缩摘要
        summary_parts = []
        if self._compressed_summary:
            summary_parts.append(self._compressed_summary)

        # 提取关键信息
        for msg in old_messages:
            content = msg.get("content", "")
            role = msg.get("role", "")

            if role == "user":
                # 保留用户请求摘要
                summary_parts.append(f"用户: {content[:150]}")
            elif role == "assistant":
                # 提取工具调用和关键结果
                if "[Action]" in content or "[Observation]" in content:
                    # 工具调用结果，只保留关键行
                    lines = content.split("\n")
                    key_lines = [l for l in lines if any(
                        kw in l for kw in ["[Action]", "[Observation]", "✅", "❌", "Exit code"]
                    )]
                    if key_lines:
                        summary_parts.append("Agent: " + " | ".join(key_lines[:3]))
                else:
                    summary_parts.append(f"助手: {content[:100]}")

        self._compressed_summary = "\n".join(summary_parts[-20:])  # 保留最近 20 条摘要

        # 更新消息和 token 计数
        self._messages = keep_messages
        self._stats.compressed_count += len(old_messages)

        # 重新计算 token
        total = estimate_tokens(self._compressed_summary)
        for msg in self._messages:
            total += estimate_tokens(msg.get("content", ""))
        self._stats.total_tokens = total

        old_pct = (self._stats.total_tokens + sum(
            estimate_tokens(m.get("content", "")) for m in old_messages
        )) / self.max_tokens
        self._stats.compression_ratio = 1.0 - (self._stats.usage_pct / old_pct) if old_pct > 0 else 0

        logger.info(
            "[Context] Compressed %d messages → summary (%d tokens, %.0f%% usage)",
            len(old_messages), self._stats.total_tokens, self._stats.usage_pct * 100,
        )

    def _load_project_memory(self) -> str:
        """加载 DREAMHELP.md 项目记忆"""
        if not self.project_dir:
            return ""

        memory_path = os.path.join(self.project_dir, "DREAMHELP.md")
        if not os.path.exists(memory_path):
            return ""

        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                content = f.read()
            # 截断过长的项目记忆
            if len(content) > 3000:
                content = content[:3000] + "\n... (截断)"
            return content
        except Exception:
            return ""

    def save_project_memory(self, content: str):
        """保存项目记忆到 DREAMHELP.md"""
        if not self.project_dir:
            return

        memory_path = os.path.join(self.project_dir, "DREAMHELP.md")
        try:
            os.makedirs(self.project_dir, exist_ok=True)
            with open(memory_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("[Context] Saved project memory: %s", memory_path)
        except Exception as e:
            logger.warning("[Context] Failed to save project memory: %s", e)

    def get_stats(self) -> dict:
        return {
            "total_tokens": self._stats.total_tokens,
            "max_tokens": self._stats.max_tokens,
            "usage_pct": round(self._stats.usage_pct * 100, 1),
            "messages_count": self._stats.messages_count,
            "compressed_count": self._stats.compressed_count,
            "compression_ratio": round(self._stats.compression_ratio * 100, 1),
            "has_project_memory": bool(self._load_project_memory()),
        }

    def reset(self):
        """重置上下文（新会话）"""
        self._messages.clear()
        self._compressed_summary = ""
        self._stats = ContextStats(max_tokens=self.max_tokens)
