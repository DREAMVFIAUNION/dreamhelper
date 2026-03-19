"""自适应文档分块器 — 智能分块，尊重句子/段落/标题边界

策略:
- text: 句子感知分块，不在句子中间切割
- markdown: 按标题层级分块，保留层级上下文
- code: 按函数/类定义分块
- faq: 按 Q&A 对分块
"""

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    content: str
    metadata: dict = field(default_factory=dict)
    chunk_index: int = 0
    token_count: int = 0


# 中英文句子结尾模式
_SENTENCE_END = re.compile(r'(?<=[。！？.!?\n])\s*')
# Markdown 标题
_MD_HEADING = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
# 代码定义 (Python / JS / TS)
_CODE_BLOCK = re.compile(
    r'^(?:def |class |async def |function |export |const |let |var )',
    re.MULTILINE,
)


def _estimate_tokens(text: str) -> int:
    """粗估 token 数: 中文按字数, 英文按词数"""
    cn = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    en = len(re.findall(r'[a-zA-Z]+', text))
    return cn + en


def _split_sentences(text: str) -> List[str]:
    """将文本按句子边界切分"""
    parts = _SENTENCE_END.split(text)
    return [s.strip() for s in parts if s.strip()]


class AdaptiveChunker:
    """根据文档类型自动选择分块策略"""

    def __init__(self, max_chunk_size: int = 512, overlap: int = 50):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def chunk(self, text: str, doc_type: str = "text") -> List[Chunk]:
        """分块入口"""
        if doc_type == "markdown":
            return self._chunk_markdown(text)
        elif doc_type == "code":
            return self._chunk_code(text)
        elif doc_type == "faq":
            return self._chunk_faq(text)
        else:
            return self._chunk_text(text)

    # ── 通用文本: 句子感知分块 ──────────────────────────

    def _chunk_text(self, text: str) -> List[Chunk]:
        """句子感知分块: 按句子边界累积，不在句子中间切割"""
        sentences = _split_sentences(text)
        if not sentences:
            return self._fallback_chunk(text, "text")

        chunks: List[Chunk] = []
        current_sentences: List[str] = []
        current_len = 0

        for sent in sentences:
            sent_len = len(sent)

            # 单句超长: 强制按字符切割
            if sent_len > self.max_chunk_size:
                # 先保存已有内容
                if current_sentences:
                    chunks.append(self._make_chunk(
                        "\n".join(current_sentences), len(chunks), "text",
                    ))
                # 切割超长句子
                for i in range(0, sent_len, self.max_chunk_size - self.overlap):
                    piece = sent[i:i + self.max_chunk_size]
                    if piece.strip():
                        chunks.append(self._make_chunk(piece, len(chunks), "text"))
                current_sentences = []
                current_len = 0
                continue

            if current_len + sent_len > self.max_chunk_size and current_sentences:
                chunks.append(self._make_chunk(
                    "\n".join(current_sentences), len(chunks), "text",
                ))
                # 保留最后一句作为 overlap 上下文
                overlap_sents = current_sentences[-1:]
                current_sentences = overlap_sents
                current_len = sum(len(s) for s in current_sentences)

            current_sentences.append(sent)
            current_len += sent_len

        if current_sentences:
            chunks.append(self._make_chunk(
                "\n".join(current_sentences), len(chunks), "text",
            ))

        return chunks or self._fallback_chunk(text, "text")

    # ── Markdown: 按标题层级分块 ──────────────────────────

    def _chunk_markdown(self, text: str) -> List[Chunk]:
        """按 Markdown 标题层级分块，保留标题路径作为上下文"""
        # 按标题切分段落
        sections: List[tuple[str, int, str]] = []  # (heading, level, body)
        current_heading = ""
        current_level = 0
        current_body: List[str] = []

        for line in text.split("\n"):
            m = _MD_HEADING.match(line)
            if m:
                if current_body or current_heading:
                    sections.append((current_heading, current_level, "\n".join(current_body).strip()))
                current_heading = m.group(2).strip()
                current_level = len(m.group(1))
                current_body = []
            else:
                current_body.append(line)

        if current_body or current_heading:
            sections.append((current_heading, current_level, "\n".join(current_body).strip()))

        # 构建 chunks, 合并小段落
        chunks: List[Chunk] = []
        pending = ""
        pending_heading = ""

        for heading, level, body in sections:
            section_text = f"## {heading}\n{body}" if heading else body
            if not section_text.strip():
                continue

            if len(pending) + len(section_text) > self.max_chunk_size and pending:
                chunks.append(self._make_chunk(pending, len(chunks), "markdown", heading=pending_heading))
                pending = ""
                pending_heading = ""

            if len(section_text) > self.max_chunk_size * 2:
                # 超长段落: 先 flush pending
                if pending:
                    chunks.append(self._make_chunk(pending, len(chunks), "markdown", heading=pending_heading))
                    pending = ""
                    pending_heading = ""
                # 用句子感知切割超长段落
                sub_chunks = self._chunk_text(section_text)
                for sc in sub_chunks:
                    sc.metadata["heading"] = heading
                    sc.chunk_index = len(chunks)
                    chunks.append(sc)
            else:
                pending += ("\n\n" if pending else "") + section_text
                if not pending_heading:
                    pending_heading = heading

        if pending.strip():
            chunks.append(self._make_chunk(pending, len(chunks), "markdown", heading=pending_heading))

        return chunks or self._fallback_chunk(text, "markdown")

    # ── 代码: 按函数/类定义分块 ──────────────────────────

    def _chunk_code(self, text: str) -> List[Chunk]:
        """按函数/类定义边界分块"""
        # 找到所有定义点的位置
        positions = [m.start() for m in _CODE_BLOCK.finditer(text)]

        if not positions:
            return self._chunk_text(text)

        # 确保从文件开头开始
        if positions[0] != 0:
            positions.insert(0, 0)

        chunks: List[Chunk] = []
        for i, start in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(text)
            block = text[start:end].strip()
            if not block:
                continue

            if len(block) > self.max_chunk_size * 2:
                # 超长函数: 滑动窗口切割
                for j in range(0, len(block), self.max_chunk_size - self.overlap):
                    piece = block[j:j + self.max_chunk_size]
                    if piece.strip():
                        chunks.append(self._make_chunk(piece, len(chunks), "code"))
            else:
                chunks.append(self._make_chunk(block, len(chunks), "code"))

        return chunks or self._fallback_chunk(text, "code")

    # ── FAQ: 按 Q&A 对分块 ──────────────────────────

    def _chunk_faq(self, text: str) -> List[Chunk]:
        """按 Q&A 问答对分块"""
        # 常见 FAQ 模式: Q: / A: 或 问: / 答: 或 **问题** 等
        qa_pattern = re.compile(r'(?:^|\n)(?:Q[:：]|问[:：]|\d+[.、]\s*(?:问题|Q))', re.IGNORECASE)
        positions = [m.start() for m in qa_pattern.finditer(text)]

        if len(positions) < 2:
            return self._chunk_text(text)

        chunks: List[Chunk] = []
        for i, start in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(text)
            qa_block = text[start:end].strip()
            if qa_block:
                chunks.append(self._make_chunk(qa_block, len(chunks), "faq"))

        return chunks or self._chunk_text(text)

    # ── 辅助方法 ──────────────────────────

    def _make_chunk(self, content: str, index: int, doc_type: str, **extra_meta) -> Chunk:
        return Chunk(
            content=content,
            metadata={"type": doc_type, **extra_meta},
            chunk_index=index,
            token_count=_estimate_tokens(content),
        )

    def _fallback_chunk(self, text: str, doc_type: str) -> List[Chunk]:
        """兜底: 直接按字符切割"""
        if not text.strip():
            return []
        return [self._make_chunk(
            text[:self.max_chunk_size],
            0,
            doc_type,
        )]
