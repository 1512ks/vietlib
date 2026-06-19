"""
search/ -- Semantic Search Engine cho hệ thống chatbot thư viện tiếng Việt.

Modules:
    bm25_retriever  : BM25 keyword search
    hybrid_search   : Hybrid Search = BM25 + Vector (RRF fusion)
    reranker        : Cross-Encoder reranking
    search_pipeline : Pipeline tổng hợp
    evaluator       : Đánh giá Precision@K, Recall@K, MRR
    test_queries    : Tập test queries + ground truth
"""

from .bm25_retriever import BM25Retriever
from .hybrid_search import HybridSearch, SearchResult
from .reranker import CrossEncoderReranker
from .search_pipeline import SearchPipeline

__all__ = [
    "BM25Retriever",
    "HybridSearch",
    "SearchResult",
    "CrossEncoderReranker",
    "SearchPipeline",
]
