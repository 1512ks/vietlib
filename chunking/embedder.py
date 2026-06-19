"""
embedder.py -- Tạo embedding vectors cho TextChunk dùng sentence-transformers.

Model mặc định: intfloat/multilingual-e5-base
  - Hỗ trợ tiếng Việt tốt
  - Kích thước: 278MB, vector 768 chiều
  - Dùng prefix "query: " khi embed câu hỏi, "passage: " khi embed chunk

Thay thế nếu cần nhanh hơn:
  - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2  (117MB, 384d)
"""

from __future__ import annotations
import json
import logging
import time
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================
#  Embedder
# ============================================================
class Embedder:
    """
    Wrapper sentence-transformers để embed TextChunk.

    Args:
        model_name: HuggingFace model ID
        batch_size: Số chunk embed mỗi lần (điều chỉnh theo RAM/VRAM)
        device: "cpu" | "cuda" | None (tự phát hiện)
        use_prefix: Thêm "passage: " cho chunk, "query: " cho query (cần cho E5)
    """

    DEFAULT_MODEL = "intfloat/multilingual-e5-base"
    FAST_MODEL    = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        batch_size: int = 32,
        device: Optional[str] = None,
        use_prefix: bool = True,
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.use_prefix = use_prefix
        self._model = None  # lazy load

        # Tự phát hiện device
        if device is None:
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"
        else:
            self.device = device

    def _load(self):
        """Lazy-load model (chỉ load khi cần)."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading model '{self.model_name}' trên {self.device}...")
            t0 = time.time()
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"  → Load xong trong {time.time()-t0:.1f}s")
        return self._model

    # ----------------------------------------------------------
    #  Embed danh sách chunk
    # ----------------------------------------------------------
    def embed_chunks(self, chunks) -> np.ndarray:
        """
        Embed danh sách TextChunk.

        Returns:
            np.ndarray shape (n_chunks, dim)
        """
        texts = [
            (f"passage: {c.text}" if self.use_prefix else c.text)
            for c in chunks
        ]
        return self._encode(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed 1 câu hỏi.

        Returns:
            np.ndarray shape (dim,)
        """
        text = f"query: {query}" if self.use_prefix else query
        vecs = self._encode([text])
        return vecs[0]

    # ----------------------------------------------------------
    #  Encode raw texts
    # ----------------------------------------------------------
    def _encode(self, texts: List[str]) -> np.ndarray:
        model = self._load()
        vecs = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=len(texts) > 50,
            normalize_embeddings=True,  # cosine similarity = dot product
            convert_to_numpy=True,
        )
        return vecs

    # ----------------------------------------------------------
    #  Dimension info
    # ----------------------------------------------------------
    @property
    def dim(self) -> int:
        return self._load().get_sentence_embedding_dimension()


# ============================================================
#  Simple retriever (dùng numpy, không cần vector DB)
# ============================================================
class NumpyRetriever:
    """
    Retriever đơn giản dùng numpy cosine similarity.
    Phù hợp để thử nghiệm trước khi dùng FAISS / ChromaDB.
    """

    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.chunks = []
        self.matrix: Optional[np.ndarray] = None  # (n, dim)

    def add_chunks(self, chunks):
        """Embed và lưu các chunk vào index."""
        logger.info(f"Embedding {len(chunks)} chunks...")
        vecs = self.embedder.embed_chunks(chunks)
        self.chunks.extend(chunks)
        if self.matrix is None:
            self.matrix = vecs
        else:
            self.matrix = np.vstack([self.matrix, vecs])
        logger.info(f"  → Index: {len(self.chunks)} chunks, shape {self.matrix.shape}")

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """
        Tìm top_k chunk liên quan nhất với query.

        Returns:
            List[dict] với keys: chunk, score
        """
        if self.matrix is None or len(self.chunks) == 0:
            return []

        q_vec = self.embedder.embed_query(query)
        scores = self.matrix @ q_vec  # cosine similarity (do normalize)

        top_idx = np.argsort(scores)[::-1][:top_k]
        return [
            {"chunk": self.chunks[i], "score": float(scores[i])}
            for i in top_idx
        ]

    def save(self, path: str | Path):
        """Lưu index ra file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(path) + "_vecs.npy", self.matrix)
        meta = [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "text": c.text,
                "word_count": c.word_count,
                "strategy": c.strategy,
                "metadata": c.metadata,
            }
            for c in self.chunks
        ]
        with open(str(path) + "_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        logger.info(f"Đã lưu index → {path}_vecs.npy + {path}_meta.json")
