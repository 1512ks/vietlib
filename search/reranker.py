"""
reranker.py -- Cross-Encoder reranking cho Semantic Search.

Model mặc định: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
  - Đa ngôn ngữ, hỗ trợ tiếng Việt
  - Input: (query, passage) → relevance score
  - ~400MB

Model nhanh hơn (tiếng Anh chính): cross-encoder/ms-marco-MiniLM-L-6-v2
  - ~80MB, nhanh hơn 5x, nhưng kém hơn với tiếng Việt

Cách dùng:
    from search.reranker import CrossEncoderReranker

    reranker = CrossEncoderReranker()
    reranked = reranker.rerank(query, candidates, top_k=5)
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Cross-Encoder reranker: nhận query + danh sách candidates →
    score lại từng cặp (query, doc) → sắp xếp theo score mới.

    Args:
        model_name  : HuggingFace model ID
        device      : "cpu" | "cuda" | None (tự phát hiện)
        max_length  : Max token length cho cross-encoder input
        batch_size  : Batch size khi inference
    """

    # Model da ngon ngu (tot voi tieng Viet)
    MULTILINGUAL_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    # Model tieng Anh (nhanh hon, dung khi khong can multilingual)
    ENGLISH_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(
        self,
        model_name: str = MULTILINGUAL_MODEL,
        device: Optional[str] = None,
        max_length: int = 192,   # Giảm từ 512→192: đủ cho title+summary, nhanh hơn ~2x
        batch_size: int = 32,    # Tăng từ 16→32: tận dụng vectorized CPU inference
    ):
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self._model = None  # lazy load

        if device is None:
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"
        else:
            self.device = device

    def _load(self):
        """Lazy-load Cross-Encoder model."""
        if self._model is None:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading Cross-Encoder '{self.model_name}' trên {self.device}...")
            t0 = time.time()
            self._model = CrossEncoder(
                self.model_name,
                max_length=self.max_length,
                device=self.device,
            )
            logger.info(f"  → Load xong trong {time.time()-t0:.1f}s")
        return self._model

    def rerank(
        self,
        query: str,
        candidates,  # List[SearchResult]
        top_k: Optional[int] = None,
    ):
        """
        Rerank danh sách candidates theo Cross-Encoder score.

        Args:
            query      : Câu hỏi người dùng
            candidates : List[SearchResult] từ HybridSearch
            top_k      : Số kết quả trả về (None = trả tất cả)

        Returns:
            List[SearchResult] sắp xếp lại theo rerank_score giảm dần
        """
        if not candidates:
            return []

        model = self._load()

        # Tạo pairs (query, doc_text)
        pairs = [(query, c.text[:self.max_length]) for c in candidates]

        # Inference: dùng batch size lớn hơn để tận dụng vectorized ops trên CPU
        t0 = time.time()
        scores = model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        logger.info(f"Cross-Encoder reranked {len(candidates)} docs trong {(time.time()-t0)*1000:.0f}ms")

        # Gán rerank_score
        for candidate, score in zip(candidates, scores):
            candidate.rerank_score = float(score)

        # Sort theo rerank score giảm dần
        reranked = sorted(candidates, key=lambda c: c.rerank_score, reverse=True)

        if top_k is not None:
            reranked = reranked[:top_k]

        # Cập nhật score tổng = rerank_score (để downstream dùng thống nhất)
        for c in reranked:
            c.score = c.rerank_score

        return reranked

    def score(self, query: str, texts: List[str]) -> List[float]:
        """
        Tính rerank score cho từng cặp (query, text) — dùng để re-rank pool
        các context dict (không phải SearchResult). Trả về list float cùng thứ tự.
        """
        if not texts:
            return []
        model = self._load()
        pairs = [(query, t[:self.max_length]) for t in texts]
        scores = model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return [float(s) for s in scores]

    def rerank_with_threshold(
        self,
        query: str,
        candidates,
        threshold: float = 0.0,
        top_k: Optional[int] = None,
    ):
        """
        Rerank và lọc chỉ giữ những kết quả có score >= threshold.
        Hữu ích để loại bỏ completely irrelevant results.
        """
        reranked = self.rerank(query, candidates, top_k=top_k)
        return [c for c in reranked if c.rerank_score >= threshold]
