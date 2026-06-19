"""
search_pipeline.py -- Pipeline tổng hợp: BM25 + Vector → RRF → Cross-Encoder.

Flow:
    Query
      ├── BM25 Search (top n_candidates)
      └── Vector Search (top n_candidates)
            ↓
        RRF Fusion (top n_rerank)
            ↓
        Cross-Encoder Reranking (top_k)
            ↓
        Final Results

Cách dùng:
    from search.search_pipeline import SearchPipeline

    pipeline = SearchPipeline.build(
        chroma_manager=chroma,
        embedder=embedder,
    )
    results = pipeline.search("sách của Nguyễn Nhật Ánh", top_k=5)
    pipeline.print_results(results)
"""

from __future__ import annotations

import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .bm25_retriever import BM25Retriever
from .hybrid_search import HybridSearch, SearchResult
from .reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Cau hinh cho SearchPipeline."""
    # So candidates lay tu moi retriever truoc khi fusion
    n_candidates: int = 20
    # So candidates dua vao reranker (top ket qua sau RRF)
    n_rerank: int = 7   # Giảm 10→7: ít cặp hơn cho cross-encoder, ít mất accuracy
    # So ket qua cuoi tra ve
    top_k: int = 5
    # RRF k constant
    rrf_k: int = 60
    # BM25 / Vector weights cho RRF
    bm25_weight: float = 0.5
    vector_weight: float = 0.5
    # Có dùng reranker không
    use_reranker: bool = True
    # Cross-Encoder model
    reranker_model: str = CrossEncoderReranker.MULTILINGUAL_MODEL
    # BM25 cache path
    bm25_cache_path: Optional[str] = None


class SearchPipeline:
    """
    Pipeline tổng hợp: Hybrid Search + Cross-Encoder Reranking.

    Khởi tạo qua SearchPipeline.build() để tự động load tất cả components.
    """

    def __init__(
        self,
        hybrid_search: HybridSearch,
        reranker: Optional[CrossEncoderReranker],
        config: PipelineConfig,
    ):
        self.hybrid = hybrid_search
        self.reranker = reranker
        self.config = config

    # ----------------------------------------------------------
    #  Factory
    # ----------------------------------------------------------
    @classmethod
    def build(
        cls,
        qdrant_manager,
        embedder,
        config: Optional[PipelineConfig] = None,
        force_rebuild_bm25: bool = False,
    ) -> "SearchPipeline":
        """
        Build SearchPipeline từ QdrantManager + Embedder.

        Args:
            qdrant_manager     : QdrantManager đã kết nối
            embedder           : Embedder (multilingual-e5 hoặc MiniLM)
            config             : PipelineConfig (dùng default nếu None)
            force_rebuild_bm25 : Force rebuild BM25 index dù đã có cache
        """
        if config is None:
            config = PipelineConfig()

        # BM25 cache
        bm25_cache = (
            Path(config.bm25_cache_path)
            if config.bm25_cache_path
            else Path(__file__).parent.parent / "data" / "bm25_index.pkl"
        )

        logger.info("=== Đang khởi tạo SearchPipeline ===")

        # Build BM25
        bm25 = BM25Retriever.from_qdrant(
            qdrant_manager,
            index_cache_path=bm25_cache,
            force_rebuild=force_rebuild_bm25,
        )

        # Hybrid Search
        hybrid = HybridSearch(
            bm25_retriever=bm25,
            qdrant_manager=qdrant_manager,
            embedder=embedder,
            rrf_k=config.rrf_k,
        )

        # Reranker (lazy load)
        reranker = None
        if config.use_reranker:
            reranker = CrossEncoderReranker(model_name=config.reranker_model)

        logger.info("=== SearchPipeline đã sẵn sàng ===")
        return cls(hybrid, reranker, config)

    # ----------------------------------------------------------
    #  Search
    # ----------------------------------------------------------
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        use_reranker: Optional[bool] = None,
        mode: str = "hybrid",  # "hybrid" | "bm25" | "vector"
    ) -> List[SearchResult]:
        """
        Thực hiện tìm kiếm đầy đủ pipeline.

        Args:
            query       : Câu hỏi
            top_k       : Override config.top_k
            use_reranker: Override config.use_reranker
            mode        : "hybrid" (mặc định) | "bm25" | "vector"

        Returns:
            List[SearchResult] sorted by score descending
        """
        cfg = self.config
        final_top_k = top_k or cfg.top_k
        do_rerank = (use_reranker if use_reranker is not None else cfg.use_reranker)

        t0 = time.time()

        # ── Bước 1: Retrieve candidates ──
        if mode == "bm25":
            candidates = self.hybrid.search_bm25_only(query, top_k=final_top_k)
            do_rerank = False
        elif mode == "vector":
            candidates = self.hybrid.search_vector_only(query, top_k=final_top_k)
            do_rerank = False
        else:  # hybrid
            candidates = self.hybrid.search(
                query,
                top_k=cfg.n_rerank if do_rerank else final_top_k,
                bm25_weight=cfg.bm25_weight,
                vector_weight=cfg.vector_weight,
                parallel=True,   # Chạy BM25 + Vector song song
            )

        # ── Bước 2: Rerank ──
        if do_rerank and self.reranker and candidates:
            results = self.reranker.rerank(query, candidates, top_k=final_top_k)
        else:
            results = candidates[:final_top_k]

        elapsed = time.time() - t0
        logger.info(
            f"[Pipeline] '{query[:50]}...' → {len(results)} results | "
            f"{elapsed*1000:.0f}ms (mode={mode}, rerank={do_rerank})"
        )
        return results

    # ----------------------------------------------------------
    #  Display
    # ----------------------------------------------------------
    def print_results(self, results: List[SearchResult], query: str = ""):
        """In kết quả dạng đẹp ra console."""
        if query:
            print(f"\n{'='*60}")
            print(f"  Câu hỏi: {query}")
            print(f"{'='*60}")

        if not results:
            print("  (Không tìm thấy kết quả)")
            return

        for i, r in enumerate(results, 1):
            title = r.metadata.get("title", r.metadata.get("name", "N/A"))
            author = r.metadata.get("author", r.metadata.get("authors", "N/A"))
            score_str = f"score={r.score:.4f}"
            if r.rerank_score != 0:
                score_str += f" | rerank={r.rerank_score:.4f}"
            if r.bm25_rank >= 0:
                score_str += f" | bm25_rank={r.bm25_rank}"
            if r.vector_rank >= 0:
                score_str += f" | vec_rank={r.vector_rank}"

            print(f"\n  [{i}] {title} — {author}")
            print(f"       {score_str}")
            print(f"       {r.short_text(150)}")

        print()
