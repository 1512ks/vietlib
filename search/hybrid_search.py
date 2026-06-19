"""
hybrid_search.py -- Hybrid Search kết hợp BM25 + Vector Search qua RRF fusion.

Thuật toán Reciprocal Rank Fusion (RRF):
    score(d) = Σ_i  1 / (k + rank_i(d))
    với k=60 (hằng số điều chỉnh, mặc định từ Cormack et al. 2009)

Cách dùng:
    from search.hybrid_search import HybridSearch

    engine = HybridSearch(bm25_retriever, chroma_manager, embedder)
    results = engine.search("truyện ngắn của Nam Cao", top_k=5)
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================
#  SearchResult -- ket qua thong nhat
# ============================================================
@dataclass
class SearchResult:
    doc_id: str
    text: str
    score: float           # RRF score (hoặc rerank score sau khi rerank)
    bm25_score: float = 0.0
    bm25_rank: int = -1    # -1 nếu không xuất hiện trong BM25 results
    vector_score: float = 0.0
    vector_rank: int = -1
    rerank_score: float = 0.0
    metadata: dict = field(default_factory=dict)

    def short_text(self, max_chars: int = 120) -> str:
        return self.text[:max_chars] + ("…" if len(self.text) > max_chars else "")


# ============================================================
#  RRF Fusion
# ============================================================
def reciprocal_rank_fusion(
    ranked_lists: List[List[str]],
    k: int = 60,
) -> Dict[str, float]:
    """
    Tính RRF score cho mỗi document.

    Args:
        ranked_lists: Danh sách các ranked list (mỗi phần tử là list doc_id sorted by rank)
        k: RRF hằng số (mặc định 60)

    Returns:
        Dict[doc_id → rrf_score] sắp xếp giảm dần
    """
    scores: Dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return scores


# ============================================================
#  HybridSearch Engine
# ============================================================
class HybridSearch:
    """
    Hybrid Search = BM25 + Vector Search kết hợp bằng RRF.

    Args:
        bm25_retriever  : BM25Retriever đã build index
        qdrant_manager  : QdrantManager đã kết nối collection
        embedder        : Embedder để embed query
        rrf_k           : RRF hằng số (default 60)
        candidate_mult  : Lấy top_k * candidate_mult candidates từ mỗi retriever
                          trước khi fusion (để đảm bảo coverage)
    """

    def __init__(
        self,
        bm25_retriever,
        qdrant_manager,
        embedder,
        rrf_k: int = 60,
        candidate_mult: int = 3,
    ):
        self.bm25 = bm25_retriever
        self.qdrant = qdrant_manager
        self.embedder = embedder
        self.rrf_k = rrf_k
        self.candidate_mult = candidate_mult

    # ----------------------------------------------------------
    #  Main search
    # ----------------------------------------------------------
    def search(
        self,
        query: str,
        top_k: int = 10,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        verbose: bool = False,
        parallel: bool = True,   # Chạy BM25 + Vector song song
    ) -> List[SearchResult]:
        """
        Hybrid search: BM25 + Vector → RRF fusion → top_k results.

        Args:
            query         : Câu hỏi người dùng
            top_k         : Số kết quả trả về
            bm25_weight   : Trọng số BM25 trong weighted RRF (chỉ ảnh hưởng khi
                            bm25_weight != vector_weight, mặc định equal-weight)
            vector_weight : Trọng số vector search
            verbose       : In log chi tiết

        Returns:
            List[SearchResult] sắp xếp theo RRF score giảm dần
        """
        n_candidates = top_k * self.candidate_mult
        t_total = time.time()

        if parallel:
            # ── Chạy BM25 và Vector song song ──
            # BM25: CPU (numpy, release GIL) | Qdrant: I/O network → overlap tốt
            def _bm25():
                return self.bm25.search(query, top_k=n_candidates)

            def _vector():
                q_vec = self.embedder.embed_query(query)
                raw = self.qdrant.query(query_vector=q_vec.tolist(), limit=n_candidates)
                return raw

            with ThreadPoolExecutor(max_workers=2) as ex:
                fut_bm25   = ex.submit(_bm25)
                fut_vector = ex.submit(_vector)
                bm25_results = fut_bm25.result()
                vector_raw   = fut_vector.result()

            t_bm25 = 0.0  # không đo riêng khi song song
            t_vec  = 0.0
        else:
            # ── Tuần tự (legacy) ──
            t0 = time.time()
            bm25_results = self.bm25.search(query, top_k=n_candidates)
            t_bm25 = time.time() - t0

            t0 = time.time()
            q_vec = self.embedder.embed_query(query)
            vector_raw = self.qdrant.query(query_vector=q_vec.tolist(), limit=n_candidates)
            t_vec = time.time() - t0

        # Parse Qdrant results
        vec_map = {
            r.id: {
                "text": r.payload.get("text", ""),
                "score": r.score,
                "meta": {k: v for k, v in r.payload.items() if k != "text"},
                "rank": ri,
            }
            for ri, r in enumerate(vector_raw)
        }
        vector_ranked = [r.id for r in vector_raw]

        # BM25 lookup maps
        bm25_map: Dict[str, object] = {r.doc_id: r for r in bm25_results}
        bm25_ranked = [r.doc_id for r in bm25_results]

        if verbose:
            logger.info(f"BM25: {len(bm25_results)}, Vector: {len(vector_ranked)} results")

        # ── 3. RRF Fusion ──
        # Weighted RRF: nhân score từng list với weight
        rrf_scores: Dict[str, float] = {}
        for rank, doc_id in enumerate(bm25_ranked):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + bm25_weight / (self.rrf_k + rank + 1)
        for rank, doc_id in enumerate(vector_ranked):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + vector_weight / (self.rrf_k + rank + 1)

        # Sort theo RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda d: rrf_scores[d], reverse=True)[:top_k]

        # ── 4. Assemble kết quả ──
        results = []
        for final_rank, doc_id in enumerate(sorted_ids):
            # Lấy text và metadata từ bất kỳ source nào có
            if doc_id in vec_map:
                text = vec_map[doc_id]["text"]
                meta = vec_map[doc_id]["meta"]
                v_score = vec_map[doc_id]["score"]
                v_rank = vec_map[doc_id]["rank"]
            elif doc_id in bm25_map:
                bm25r = bm25_map[doc_id]
                text = bm25r.text
                meta = bm25r.metadata
                v_score = 0.0
                v_rank = -1
            else:
                continue

            b_score = bm25_map[doc_id].score if doc_id in bm25_map else 0.0
            b_rank = bm25_map[doc_id].rank if doc_id in bm25_map else -1

            results.append(SearchResult(
                doc_id=doc_id,
                text=text,
                score=rrf_scores[doc_id],
                bm25_score=b_score,
                bm25_rank=b_rank,
                vector_score=v_score,
                vector_rank=v_rank,
                metadata=meta,
            ))

        if verbose:
            logger.info(
                f"Hybrid search tổng: {(time.time() - t_total) * 1000:.0f}ms | "
                f"candidates BM25={len(bm25_results)}, Vec={len(vector_ranked)} → fusion={len(results)}"
            )

        return results

    # ----------------------------------------------------------
    #  BM25-only & Vector-only (để so sánh baseline)
    # ----------------------------------------------------------
    def search_bm25_only(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Chỉ dùng BM25 (để so sánh)."""
        raw = self.bm25.search(query, top_k=top_k)
        return [
            SearchResult(
                doc_id=r.doc_id,
                text=r.text,
                score=r.score,
                bm25_score=r.score,
                bm25_rank=r.rank,
                metadata=r.metadata,
            )
            for r in raw
        ]

    def search_vector_only(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Chỉ dùng Vector Search (để so sánh)."""
        q_vec = self.embedder.embed_query(query)
        vector_raw = self.qdrant.query(query_vector=q_vec.tolist(), limit=top_k)

        return [
            SearchResult(
                doc_id=r.id,
                text=r.payload.get("text", ""),
                score=r.score,
                vector_score=r.score,
                vector_rank=i,
                metadata={k: v for k, v in r.payload.items() if k != "text"},
            )
            for i, r in enumerate(vector_raw)
        ]
