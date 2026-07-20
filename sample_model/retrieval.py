"""
retrieval.py -- Hybrid retrieval CHUNK-LEVEL tự chứa cho sample model.

Đọc index đã build ở sample_model/index/ (không đụng Qdrant production):
  - docs.json    : 163 chunk (chunk_id, work_id, title, author, section, text)
  - vectors.npy  : embedding bge-m3 (AITeamVN/Vietnamese_Embedding, 1024d, đã chuẩn hóa)
  - bm25.pkl     : BM25Okapi + tokens
  - corpus/metadata.csv : nguồn sự thật THƯƠNG MẠI (giá, tiki_link, tuyển tập) — join theo work_id

Hybrid = RRF (Reciprocal Rank Fusion) của bảng xếp hạng vector và BM25.

Dùng:
    from sample_model.retrieval import Retriever
    r = Retriever.load()
    hits = r.search("Vì sao lão Hạc chọn cái chết?", top_k=5)
"""
from __future__ import annotations

import csv
import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "corpus" / "metadata.csv"
IDX = ROOT / "index"

EMBED_MODEL = "AITeamVN/Vietnamese_Embedding"  # bge-m3, khớp index_meta.json
RRF_K = 60                                     # hằng số RRF chuẩn
DEFAULT_TOP_K = 5

# Ngưỡng tin cậy trên cosine cao nhất (bge-m3 chuẩn hóa → cosine).
# Hiệu chỉnh trên index CHUNK-LEVEL (xem README): câu trong kho vs ngoài kho.
CONFIDENCE_MIN = 0.40


@dataclass
class Hit:
    """Một chunk trả về, kèm đủ metadata cho thẻ sách + đánh giá."""
    source_idx: int          # số nguồn [1], [2]... trong prompt (1-based)
    chunk_id: str
    work_id: str
    title: str
    author: str
    year: str
    genre: str
    section: str             # tóm tắt / nhân vật / chủ đề / ...
    text: str                # nội dung chunk (đã kèm title+author ở đầu)
    price: str               # gia_tham_khao_vnd ("" nếu chưa có) — join từ metadata.csv
    tiki: str                # tiki_link (URL tìm kiếm Tiki)
    edition: str             # ban_thuong_mai (bản lẻ hay tên tuyển tập)
    price_note: str          # ghi_chu_gia
    score: float             # điểm RRF hợp nhất
    vector_score: float      # cosine gốc (đo độ tin cậy)

    @property
    def in_collection(self) -> bool:
        return "tuyển tập" in (self.price_note or "").lower()

    @property
    def price_int(self) -> Optional[int]:
        try:
            return int(str(self.price).strip()) if str(self.price).strip() else None
        except ValueError:
            return None


@dataclass
class Retriever:
    docs: List[dict]
    vectors: np.ndarray
    bm25: object
    works: Dict[str, dict]                       # work_id → hàng metadata.csv
    _embedder: object = field(default=None, repr=False)

    # ------------------------------------------------------------
    @classmethod
    def load(cls) -> "Retriever":
        docs = json.load(open(IDX / "docs.json", encoding="utf-8"))
        vectors = np.load(IDX / "vectors.npy").astype(np.float32)
        with open(IDX / "bm25.pkl", "rb") as f:
            bm25 = pickle.load(f)["bm25"]
        works = {r["id"]: r for r in csv.DictReader(open(CSV_PATH, encoding="utf-8"))}
        if len(docs) != vectors.shape[0]:
            raise ValueError(
                f"Lệch số hàng: docs={len(docs)} vs vectors={vectors.shape[0]}. "
                "Hãy build lại index (eval/build_index.py).")
        return cls(docs=docs, vectors=vectors, bm25=bm25, works=works)

    # ------------------------------------------------------------
    def _embed(self, query: str) -> np.ndarray:
        if self._embedder is None:
            import os
            from sentence_transformers import SentenceTransformer
            kwargs = {}
            # EMBED_DTYPE=bfloat16 (đặt qua secret trên Streamlit Cloud): giảm RAM model
            # ~2.3GB → ~1.2GB để lọt free tier. Đã kiểm chứng: lệch cosine ~0.001-0.002,
            # không đổi top-1 câu trong kho, không ảnh hưởng ngưỡng 0.40 (biên ~0.09).
            if os.environ.get("EMBED_DTYPE", "").lower() in ("bfloat16", "bf16"):
                import torch
                kwargs["model_kwargs"] = {"torch_dtype": torch.bfloat16}
            self._embedder = SentenceTransformer(EMBED_MODEL, **kwargs)
        v = self._embedder.encode([query], normalize_embeddings=True)
        return np.asarray(v, dtype=np.float32)[0]

    def warm_up(self) -> None:
        """Nạp sẵn model embedding để câu hỏi đầu tiên không chịu trễ tải model."""
        self._embed("khởi động")

    # ------------------------------------------------------------
    @staticmethod
    def _rrf_rank(order: np.ndarray) -> dict:
        return {int(idx): 1.0 / (RRF_K + rank) for rank, idx in enumerate(order)}

    def search(self, query: str, top_k: int = DEFAULT_TOP_K,
               mode: str = "hybrid", group_works: bool = False) -> List[Hit]:
        """Truy hồi chunk. mode: "hybrid" (RRF) | "vector" | "bm25".

        group_works=True (cấu hình của app): xếp hạng THEO TÁC PHẨM trước —
        điểm tác phẩm = max điểm chunk của nó — rồi mới liệt kê chunk theo
        (thứ hạng tác phẩm, điểm chunk). Cùng ý khác diễn đạt thường đổi thứ
        hạng SECTION trong cùng cuốn sách chứ ít đổi cuốn sách → gộp theo tác
        phẩm làm kết quả ổn định hơn với người dùng (cải tiến Search Stability).
        """
        n = self.vectors.shape[0]
        top_k = max(1, min(top_k, n))

        qv = self._embed(query)
        cos = self.vectors @ qv
        vec_order = np.argsort(-cos)

        tokens = query.lower().split()
        bm = np.asarray(self.bm25.get_scores(tokens), dtype=np.float32)
        bm_order = np.argsort(-bm)

        if mode == "vector":
            fused = {int(i): float(cos[i]) for i in vec_order}
        elif mode == "bm25":
            fused = {int(i): float(bm[i]) for i in bm_order}
        else:
            rv = self._rrf_rank(vec_order)
            rb = self._rrf_rank(bm_order)
            fused = {i: rv.get(i, 0.0) + rb.get(i, 0.0) for i in range(n)}

        if group_works:
            # Điểm tác phẩm = max điểm chunk; tie-break bằng id để tất định
            cand = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:max(top_k * 4, 20)]
            wscore: Dict[str, float] = {}
            for i, sc in cand:
                w = self.docs[i]["work_id"]
                wscore[w] = max(wscore.get(w, 0.0), sc)
            worder = {w: r for r, (w, _) in enumerate(
                sorted(wscore.items(), key=lambda kv: (-kv[1], kv[0])))}
            ranked = sorted(
                cand,
                key=lambda kv: (worder[self.docs[kv[0]]["work_id"]], -kv[1],
                                self.docs[kv[0]]["chunk_id"]))[:top_k]
        else:
            ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:top_k]

        hits: List[Hit] = []
        for pos, (idx, sc) in enumerate(ranked, start=1):
            d = self.docs[idx]
            w = self.works.get(d["work_id"], {})
            hits.append(Hit(
                source_idx=pos,
                chunk_id=d["chunk_id"], work_id=d["work_id"],
                title=d["title"], author=d["author"],
                year=d["year"], genre=d["genre"], section=d["section"],
                text=d["text"],
                price=w.get("gia_tham_khao_vnd", ""),
                tiki=w.get("tiki_link", ""),
                edition=w.get("ban_thuong_mai", ""),
                price_note=w.get("ghi_chu_gia", ""),
                score=float(sc),
                vector_score=float(cos[idx]),
            ))
        return hits

    def confidence(self, hits: List[Hit]) -> float:
        """Độ tin cậy = cosine cao nhất trong các hit (0 nếu rỗng)."""
        return max((h.vector_score for h in hits), default=0.0)

    # ------------------------------------------------------------
    # Ý định LIỆT KÊ (hỏi "những/các cái nào") — kết hợp với việc có tên tác giả
    _LIST_HINT = ("nào", "những", "các", "kể tên", "gồm", "liệt kê",
                  "viết gì", "sáng tác", "là tác giả")

    def suggest_top_k(self, query: str, default_k: int = DEFAULT_TOP_K) -> int:
        """K thích ứng: câu dạng AUTHOR (nhắc tên tác giả + ý định liệt kê tác phẩm)
        cần vớt NHIỀU chunk hơn vì mỗi tác giả có tới 13 chunk liên quan mà K=5
        là trần cứng (cải tiến AUTHOR Recall). Trả về 13 cho câu AUTHOR."""
        q = query.lower()
        if not any(h in q for h in self._LIST_HINT):
            return default_k
        authors = {r["tac_gia"].lower() for r in self.works.values()}
        if any(a and a in q for a in authors):
            return 13
        return default_k


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = Retriever.load()
    q = sys.argv[1] if len(sys.argv) > 1 else "Vì sao lão Hạc chọn cái chết?"
    print(f"Truy vấn: {q}\n")
    hits = r.search(q, top_k=5)
    print(f"Độ tin cậy (cosine cao nhất): {r.confidence(hits):.3f}\n")
    for h in hits:
        price = f"{h.price_int:,}đ".replace(",", ".") if h.price_int else "—"
        print(f"[{h.source_idx}] {h.chunk_id} ({h.section}) | {h.title} — {h.author} | {price}")
        print(f"     RRF={h.score:.4f}  cos={h.vector_score:.3f}")
