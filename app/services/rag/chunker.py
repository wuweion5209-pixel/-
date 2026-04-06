"""文档分块模块"""

import re
from typing import List
from app.utils.logger import logger


class TextChunker:
    """文档分块器"""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        min_chunk_size: int = 100
    ):
        """
        初始化分块器

        Args:
            chunk_size: 每块最大字符数
            chunk_overlap: 块之间重叠字符数（保持上下文连续性）
            min_chunk_size: 最小块字符数（太小的块会被合并）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_text(self, text: str) -> List[str]:
        """
        对文本进行分块

        Args:
            text: 原始文本

        Returns:
            分块后的文本列表
        """
        if not text or not text.strip():
            return []

        # 1. 先按段落分割
        paragraphs = self._split_by_paragraph(text)
        if not paragraphs:
            return [text]

        # 2. 按段落逐步添加到块中
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果当前块加上这个段落超过大小限制，先保存当前块
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk.strip())
                else:
                    # 太短，和下一个合并
                    current_chunk += "\n" + para
                    continue

                # 保留 overlap 部分
                if self.chunk_overlap > 0:
                    current_chunk = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk#这一步是为了保留当前块的最后 chunk_overlap 个字符，以便与下一个块重叠，保持上下文连续性。如果当前块的长度小于 chunk_overlap，则保留整个块作为重叠部分。
            else:
                if current_chunk:
                    current_chunk += "\n"
                current_chunk += para

        # 3. 处理最后一块
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk.strip())
        elif current_chunk and chunks:
            # 合并到最后一个块
            chunks[-1] += "\n" + current_chunk.strip()

        logger.info(f"[分块] 原始文本 {len(text)} 字符 → {len(chunks)} 个块")
        return chunks

    def _split_by_paragraph(self, text: str) -> List[str]:
        """
        按段落分割文本

        优先按换行符（\n\n）分割，其次按句号+空格分割
        """
        # 1. 先按双换行分割（段落分隔符）
        paragraphs = re.split(r'\n\n+', text)

        # 2. 如果分割太少，尝试按单换行
        if len(paragraphs) < 2:
            paragraphs = re.split(r'\n+', text)

        # 3. 过滤空段落
        return [p for p in paragraphs if p.strip()]


# 全局单例
_chunker = None


def get_chunker(
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    min_chunk_size: int = 100
) -> TextChunker:
    """获取分块器单例"""
    global _chunker
    if _chunker is None:
        _chunker = TextChunker(chunk_size, chunk_overlap, min_chunk_size)
    return _chunker
