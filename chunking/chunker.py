"""
chunker.py -- Các chiến lược chunking văn bản cho RAG.

Chiến lược:
  1. fixed_size   : chia đều theo số từ, có overlap
  2. sliding_window: cửa sổ trượt với stride tuỳ chỉnh
  3. sentence_aware: tôn trọng ranh giới câu (dùng dấu chấm)

Dùng:
    from chunking.chunker import Chunker
    chunks = Chunker(strategy="fixed_size", chunk_size=200, overlap=50).chunk(text)
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Literal


# ============================================================
#  Dataclass: mot chunk van ban
# ============================================================
@dataclass
class TextChunk:
    chunk_id: str          # "{doc_id}_chunk_{i}"
    doc_id: str            # ID tài liệu gốc
    text: str              # Nội dung chunk
    start_word: int        # Vị trí từ bắt đầu trong doc gốc
    end_word: int          # Vị trí từ kết thúc
    word_count: int        # Số từ
    char_count: int        # Số ký tự
    strategy: str          # Chiến lược chunking đã dùng
    metadata: dict = field(default_factory=dict)  # Metadata từ doc gốc


# ============================================================
#  Chunker chinh
# ============================================================
class Chunker:
    """
    Bộ chunking văn bản hỗ trợ 3 chiến lược.

    Args:
        strategy: "fixed_size" | "sliding_window" | "sentence_aware"
        chunk_size: Số từ mỗi chunk (target)
        overlap: Số từ overlap giữa các chunk liên tiếp (fixed_size)
        stride: Số từ tiến mỗi bước (sliding_window)
        min_chunk_size: Bỏ chunk ngắn hơn ngưỡng này
    """

    STRATEGIES = ("fixed_size", "sliding_window", "sentence_aware")

    def __init__(
        self,
        strategy: Literal["fixed_size", "sliding_window", "sentence_aware"] = "fixed_size",
        chunk_size: int = 200,
        overlap: int = 50,
        stride: int = 100,
        min_chunk_size: int = 30,
    ):
        assert strategy in self.STRATEGIES, f"strategy phải là {self.STRATEGIES}"
        assert chunk_size > 0
        assert 0 <= overlap < chunk_size
        assert 0 < stride <= chunk_size

        self.strategy = strategy
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.stride = stride
        self.min_chunk_size = min_chunk_size

    # ----------------------------------------------------------
    #  Public API
    # ----------------------------------------------------------
    def chunk(self, text: str, doc_id: str = "doc", metadata: dict = None) -> List[TextChunk]:
        """Chia văn bản thành danh sách TextChunk."""
        metadata = metadata or {}
        text = self._clean(text)
        words = text.split()

        if len(words) < self.min_chunk_size:
            return []  # Văn bản quá ngắn

        if self.strategy == "fixed_size":
            spans = self._fixed_size(words)
        elif self.strategy == "sliding_window":
            spans = self._sliding_window(words)
        else:
            spans = self._sentence_aware(text, words)

        chunks = []
        for i, (start, end) in enumerate(spans):
            chunk_text = " ".join(words[start:end])
            wc = end - start
            if wc < self.min_chunk_size:
                continue
            chunks.append(TextChunk(
                chunk_id=f"{doc_id}_chunk_{i}",
                doc_id=doc_id,
                text=chunk_text,
                start_word=start,
                end_word=end,
                word_count=wc,
                char_count=len(chunk_text),
                strategy=self.strategy,
                metadata=metadata,
            ))

        return chunks

    # ----------------------------------------------------------
    #  Chiến lược 1: Fixed-size với overlap
    # ----------------------------------------------------------
    def _fixed_size(self, words: List[str]) -> List[tuple]:
        """
        Chia thành các chunk kích thước cố định, có overlap.

        Ví dụ chunk_size=200, overlap=50:
          chunk 0: words[0:200]
          chunk 1: words[150:350]   ← lùi lại 50 từ
          chunk 2: words[300:500]
        """
        spans = []
        step = self.chunk_size - self.overlap
        start = 0
        n = len(words)

        while start < n:
            end = min(start + self.chunk_size, n)
            spans.append((start, end))
            if end == n:
                break
            start += step

        return spans

    # ----------------------------------------------------------
    #  Chiến lược 2: Sliding window
    # ----------------------------------------------------------
    def _sliding_window(self, words: List[str]) -> List[tuple]:
        """
        Cửa sổ trượt với kích thước cố định và stride tuỳ chỉnh.

        Ví dụ chunk_size=200, stride=100:
          chunk 0: words[0:200]
          chunk 1: words[100:300]   ← tiến 100 từ
          chunk 2: words[200:400]
        
        Khác fixed_size: stride độc lập với chunk_size,
        cho phép overlap > 50% nếu cần.
        """
        spans = []
        n = len(words)
        start = 0

        while start < n:
            end = min(start + self.chunk_size, n)
            spans.append((start, end))
            if end == n:
                break
            start += self.stride

        return spans

    # ----------------------------------------------------------
    #  Chiến lược 3: Sentence-aware
    # ----------------------------------------------------------
    def _sentence_aware(self, text: str, words: List[str]) -> List[tuple]:
        """
        Chia theo ranh giới câu. Cộng dồn câu cho đến khi đủ
        chunk_size từ, rồi bắt đầu chunk mới (có overlap = 1 câu).
        """
        # Tách câu theo dấu kết thúc câu tiếng Việt
        sentence_pattern = re.compile(r'(?<=[.!?…])\s+')
        sentences = sentence_pattern.split(text)
        if len(sentences) <= 1:
            # Fallback: tách theo dấu phẩy / xuống dòng nếu không có câu rõ ràng
            sentences = re.split(r'[,;\n]+', text)

        # Gom câu thành chunk theo word count
        spans = []
        current_words = 0
        chunk_start_word = 0
        word_pos = 0
        last_sentence_end = 0  # vị trí từ cuối câu trước (cho overlap)

        for sent in sentences:
            sent_words = sent.split()
            sw = len(sent_words)
            if sw == 0:
                continue

            if current_words + sw > self.chunk_size and current_words >= self.min_chunk_size:
                # Kết thúc chunk hiện tại
                spans.append((chunk_start_word, word_pos))
                last_sentence_end = word_pos
                # Bắt đầu chunk mới từ câu cuối của chunk cũ (overlap 1 câu)
                chunk_start_word = max(0, word_pos - sw)
                current_words = sw
            else:
                current_words += sw

            word_pos += sw

        # Chunk cuối
        if word_pos > chunk_start_word:
            spans.append((chunk_start_word, word_pos))

        return spans

    # ----------------------------------------------------------
    #  Helper
    # ----------------------------------------------------------
    @staticmethod
    def _clean(text: str) -> str:
        """Làm sạch cơ bản: normalize whitespace."""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# ============================================================
#  So sánh các chiến lược
# ============================================================
def compare_strategies(
    text: str,
    doc_id: str = "doc",
    chunk_size: int = 200,
    overlap: int = 50,
    stride: int = 100,
) -> dict:
    """
    Chạy cả 3 chiến lược trên cùng 1 văn bản, trả về thống kê so sánh.
    """
    results = {}
    configs = [
        ("fixed_size",    Chunker("fixed_size",    chunk_size, overlap, stride)),
        ("sliding_window",Chunker("sliding_window", chunk_size, overlap, stride)),
        ("sentence_aware",Chunker("sentence_aware", chunk_size, overlap, stride)),
    ]

    for name, chunker in configs:
        chunks = chunker.chunk(text, doc_id=doc_id)
        if not chunks:
            results[name] = {"n_chunks": 0}
            continue
        wcs = [c.word_count for c in chunks]
        results[name] = {
            "n_chunks":   len(chunks),
            "avg_words":  round(sum(wcs) / len(wcs), 1),
            "min_words":  min(wcs),
            "max_words":  max(wcs),
            "total_words": sum(wcs),
            "coverage":   round(sum(wcs) / max(len(text.split()), 1), 2),
        }

    return results
