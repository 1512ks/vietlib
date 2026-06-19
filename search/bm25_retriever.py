"""
bm25_retriever.py -- BM25 keyword search trên corpus tiếng Việt.

Sử dụng rank_bm25 (BM25Okapi) với tokenizer đơn giản (split + lowercase).
Hỗ trợ lưu/load index để tránh rebuild mỗi lần chạy.

Cách dùng:
    from search.bm25_retriever import BM25Retriever

    retriever = BM25Retriever.from_chroma(chroma_manager)
    results = retriever.search("truyện ngắn Nam Cao", top_k=10)
"""

from __future__ import annotations

import json
import logging
import pickle
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================
#  SearchResult dataclass (dung chung trong toan bo module)
# ============================================================
@dataclass
class BM25Result:
    doc_id: str
    text: str
    score: float
    rank: int
    metadata: dict = field(default_factory=dict)


# ============================================================
#  Tokenizer tieng Viet co ban
# ============================================================
def _tokenize_vi(text: str) -> List[str]:
    """
    Tokenizer tiếng Việt đơn giản:
      - Lowercase
      - Xóa dấu tiếng Việt (accent folding)
      - Giữ chữ cái Latin + số
      - Tách theo khoảng trắng
    Nếu cài underthesea/pyvi, có thể thay thế bằng word tokenizer tốt hơn.
    """
    text = text.lower()
    
    # Xoa dau tieng Viet (accent folding)
    text = re.sub(r'[đ]', 'd', text)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    
    # Giữ Unicode chữ cái, số, khoảng trắng
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    tokens = text.split()
    # Bỏ stopwords ngắn (≤1 ký tự)
    return [t for t in tokens if len(t) > 1]


# ============================================================
#  BM25Retriever
# ============================================================
class BM25Retriever:
    """
    BM25 retriever sử dụng rank_bm25 (BM25Okapi).

    Args:
        index_cache_path: Đường dẫn lưu BM25 index (pickle). None = không cache.
    """

    def __init__(self, index_cache_path: Optional[Path] = None):
        self.index_cache_path = Path(index_cache_path) if index_cache_path else None
        self._bm25 = None
        self._doc_ids: List[str] = []
        self._texts: List[str] = []
        self._metadatas: List[dict] = []

    # ----------------------------------------------------------
    #  Build index từ lists
    # ----------------------------------------------------------
    def build(self, doc_ids: List[str], texts: List[str], metadatas: List[dict]):
        """Build BM25 index từ danh sách documents."""
        logger.info(f"Building BM25 index cho {len(texts)} documents...")
        t0 = time.time()

        self._doc_ids = doc_ids
        self._texts = texts
        self._metadatas = metadatas

        # Tokenize
        tokenized_corpus = [_tokenize_vi(t) for t in texts]

        # Build BM25
        from rank_bm25 import BM25Okapi
        self._bm25 = BM25Okapi(tokenized_corpus)

        logger.info(f"  → Build xong trong {time.time()-t0:.1f}s (vocab={len(self._bm25.idf)} terms)")

        # Cache nếu có path
        if self.index_cache_path:
            self._save_cache()

        return self

    # ----------------------------------------------------------
    #  Factory: load từ Qdrant
    # ----------------------------------------------------------
    @classmethod
    def from_qdrant(
        cls,
        qdrant_manager,
        index_cache_path: Optional[Path] = None,
        force_rebuild: bool = False,
    ) -> "BM25Retriever":
        """
        Build BM25 index từ Qdrant collection.
        Nếu có cache và force_rebuild=False thì load cache.
        """
        retriever = cls(index_cache_path=index_cache_path)

        # Thử load cache
        if not force_rebuild and index_cache_path and Path(index_cache_path).exists():
            logger.info(f"Loading BM25 cache từ {index_cache_path}...")
            retriever._load_cache()
            return retriever

        # Lấy toàn bộ documents từ Qdrant
        logger.info("Lấy toàn bộ documents từ Qdrant...")
        t0 = time.time()
        client = qdrant_manager.client
        col_name = qdrant_manager.collection_name

        total = client.count(collection_name=col_name).count
        logger.info(f"  → Tổng số documents: {total}")

        all_ids, all_docs, all_metas = [], [], []
        
        offset = None
        while True:
            records, offset = client.scroll(
                collection_name=col_name,
                limit=5000,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            for r in records:
                all_ids.append(r.id)
                payload = r.payload or {}
                all_docs.append(payload.get("text", ""))
                # Tách text ra khỏi meta
                meta = {k: v for k, v in payload.items() if k != "text"}
                all_metas.append(meta)
                
            logger.info(f"  → Đã load {len(all_ids)}/{total} documents")
            if offset is None:
                break

        logger.info(f"  → Load xong {len(all_ids)} docs trong {time.time()-t0:.1f}s")
        retriever.build(all_ids, all_docs, all_metas)
        return retriever

    # ----------------------------------------------------------
    #  Search
    # ----------------------------------------------------------
    def search(self, query: str, top_k: int = 10) -> List[BM25Result]:
        """
        Tìm kiếm BM25. Trả về list BM25Result sắp xếp theo score giảm dần.
        """
        if self._bm25 is None:
            raise RuntimeError("BM25 index chưa được build. Gọi build() hoặc from_chroma() trước.")

        query_tokens = _tokenize_vi(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)  # np.ndarray

        # O(n) argpartition thay vì O(n log n) sorted() — nhanh hơn ~3x với 11k docs
        n = len(scores)
        k = min(top_k, n)
        top_indices = np.argpartition(scores, -k)[-k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        results = []
        for rank, idx in enumerate(top_indices):
            results.append(BM25Result(
                doc_id=self._doc_ids[idx],
                text=self._texts[idx],
                score=float(scores[idx]),
                rank=rank,
                metadata=self._metadatas[idx],
            ))

        return results

    # ----------------------------------------------------------
    #  Cache
    # ----------------------------------------------------------
    def _save_cache(self):
        """Lưu index ra file pickle."""
        self.index_cache_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "bm25": self._bm25,
            "doc_ids": self._doc_ids,
            "texts": self._texts,
            "metadatas": self._metadatas,
        }
        with open(self.index_cache_path, "wb") as f:
            pickle.dump(data, f)
        logger.info(f"Đã lưu BM25 cache → {self.index_cache_path}")

    def _load_cache(self):
        """Load index từ file pickle."""
        with open(self.index_cache_path, "rb") as f:
            data = pickle.load(f)
        self._bm25 = data["bm25"]
        self._doc_ids = data["doc_ids"]
        self._texts = data["texts"]
        self._metadatas = data["metadatas"]
        logger.info(f"Đã load BM25 cache ({len(self._doc_ids)} docs)")

    @property
    def size(self) -> int:
        return len(self._doc_ids)
