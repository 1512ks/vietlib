"""
experiment.py -- Thử nghiệm các chiến lược chunking trên dữ liệu gbooks/wiki.

Chạy:
    python chunking/experiment.py                    # so sánh 3 chiến lược
    python chunking/experiment.py --embed            # + tạo embedding & test retrieval
    python chunking/experiment.py --embed --fast     # dùng model nhỏ (MiniLM)
    python chunking/experiment.py --n 50             # thử trên 50 tài liệu
"""

import sys
import json
import logging
import argparse
import time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from chunking.chunker import Chunker, compare_strategies, TextChunk
from chunking.embedder import Embedder, NumpyRetriever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "processed" / "gbooks"


# ============================================================
#  Load du lieu
# ============================================================
def load_docs(n: int = 100, min_words: int = 100) -> list:
    """Load n tai lieu tu data/raw_v2/books, loc ngon ngu vi."""
    files = list(DATA_DIR.glob("*.json"))
    docs = []
    for f in files:
        if len(docs) >= n:
            break
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            lang = d.get("language", "")
            content = d.get("content", "") or d.get("summary", "")
            wc = len(content.split())
            if lang != "vi" or wc < min_words:
                continue
            docs.append(d)
        except Exception:
            pass
    logger.info(f"Đã load {len(docs)} tài liệu (language=vi, words>={min_words})")
    return docs


# ============================================================
#  Thử nghiệm chunking
# ============================================================
def run_chunking_experiment(docs: list, chunk_size: int = 200, overlap: int = 50, stride: int = 100):
    """So sánh 3 chiến lược chunking trên toàn bộ docs."""
    print("\n" + "=" * 65)
    print(f"  CHUNKING EXPERIMENT — {len(docs)} tài liệu")
    print(f"  chunk_size={chunk_size}, overlap={overlap}, stride={stride}")
    print("=" * 65)

    strategies = ["fixed_size", "sliding_window", "sentence_aware"]
    agg = {s: defaultdict(list) for s in strategies}
    all_chunks = {s: [] for s in strategies}

    for doc in docs:
        text = doc.get("content", "") or doc.get("summary", "")
        doc_id = doc.get("id", "unknown")
        meta = {
            "title": doc.get("title", ""),
            "author": doc.get("author", ""),
            "source": doc.get("source", ""),
        }
        stats = compare_strategies(text, doc_id, chunk_size, overlap, stride)
        for s, info in stats.items():
            if info.get("n_chunks", 0) > 0:
                agg[s]["n_chunks"].append(info["n_chunks"])
                agg[s]["avg_words"].append(info["avg_words"])
                agg[s]["coverage"].append(info["coverage"])

        # Thu thập chunk thực tế (fixed_size)
        if doc_id:
            for s in strategies:
                chunker = Chunker(s, chunk_size, overlap, stride)
                chunks = chunker.chunk(text, doc_id=doc_id, metadata=meta)
                all_chunks[s].extend(chunks)

    # In bảng so sánh
    print(f"\n{'Chiến lược':<20} {'Tổng chunk':>12} {'Avg words':>12} {'Min avg':>10} {'Max avg':>10} {'Coverage':>10}")
    print("-" * 80)
    for s in strategies:
        a = agg[s]
        if not a["n_chunks"]:
            continue
        total = sum(a["n_chunks"])
        avg_w = round(sum(a["avg_words"]) / len(a["avg_words"]), 1)
        min_w = round(min(a["avg_words"]), 1)
        max_w = round(max(a["avg_words"]), 1)
        cov   = round(sum(a["coverage"]) / len(a["coverage"]), 2)
        print(f"  {s:<18} {total:>12,} {avg_w:>12} {min_w:>10} {max_w:>10} {cov:>10}")

    # In ví dụ chunk
    print("\n" + "─" * 65)
    print("  VÍ DỤ CHUNK (tài liệu đầu tiên đủ dài):")
    print("─" * 65)
    sample_doc = docs[0]
    sample_text = sample_doc.get("content", "") or sample_doc.get("summary", "")
    sample_id = sample_doc.get("id", "doc_0")

    for s in strategies:
        chunker = Chunker(s, chunk_size, overlap, stride)
        sample_chunks = chunker.chunk(sample_text, doc_id=sample_id)
        if not sample_chunks:
            continue
        c0 = sample_chunks[0]
        print(f"\n  [{s.upper()}] → {len(sample_chunks)} chunks")
        print(f"  Chunk #0 ({c0.word_count} từ):")
        preview = c0.text[:200] + ("..." if len(c0.text) > 200 else "")
        print(f"    \"{preview}\"")

    return all_chunks


# ============================================================
#  Thử nghiệm embedding + retrieval
# ============================================================
def run_embedding_experiment(all_chunks: dict, use_fast: bool = False):
    """Tạo embedding cho fixed_size chunks và test retrieval."""
    print("\n" + "=" * 65)
    print("  EMBEDDING EXPERIMENT")
    print("=" * 65)

    model_name = (
        Embedder.FAST_MODEL if use_fast else Embedder.DEFAULT_MODEL
    )
    print(f"  Model: {model_name}")
    print(f"  Device: {'GPU' if not use_fast else 'CPU'}")

    # Dùng fixed_size chunks để embed
    chunks = all_chunks["fixed_size"]
    print(f"  Số chunks cần embed: {len(chunks):,}")

    embedder = Embedder(model_name=model_name)
    retriever = NumpyRetriever(embedder)

    t0 = time.time()
    retriever.add_chunks(chunks)
    elapsed = time.time() - t0
    print(f"  Thời gian embed: {elapsed:.1f}s ({len(chunks)/elapsed:.0f} chunks/s)")
    print(f"  Vector dim: {embedder.dim}")

    # Test retrieval với các câu hỏi mẫu
    test_queries = [
        "Truyện Kiều là tác phẩm của tác giả nào?",
        "Những tác phẩm văn học nổi tiếng thời kỳ kháng chiến",
        "Nhà văn Nam Cao viết về chủ đề gì?",
        "Tiểu thuyết lịch sử Việt Nam",
        "Thơ tình yêu của Xuân Quỳnh",
    ]

    print("\n" + "─" * 65)
    print("  KẾT QUẢ RETRIEVAL:")
    print("─" * 65)

    for query in test_queries:
        results = retriever.search(query, top_k=3)
        print(f"\n  Q: \"{query}\"")
        for j, r in enumerate(results):
            chunk = r["chunk"]
            score = r["score"]
            meta = chunk.metadata
            preview = chunk.text[:120].replace("\n", " ")
            print(f"    [{j+1}] score={score:.3f} | {meta.get('title','?')[:40]} ({meta.get('author','?')[:20]})")
            print(f"         \"{preview}...\"")

    # Lưu index
    save_path = Path("data") / "embeddings" / "fixed_size_index"
    retriever.save(save_path)
    print(f"\n  → Index đã lưu: {save_path}_vecs.npy + _meta.json")

    return retriever


# ============================================================
#  So sánh sliding window vs fixed size (chi tiết hơn)
# ============================================================
def compare_sw_vs_fixed(all_chunks: dict, embedder: Embedder, query: str):
    """So sánh kết quả retrieval của 2 chiến lược trên cùng 1 query."""
    print(f"\n  SO SÁNH FIXED vs SLIDING cho query: \"{query}\"")
    print("─" * 65)

    for strategy in ["fixed_size", "sliding_window"]:
        chunks = all_chunks[strategy]
        retriever = NumpyRetriever(embedder)
        retriever.add_chunks(chunks[:500])  # Giới hạn 500 để nhanh
        results = retriever.search(query, top_k=2)
        print(f"\n  [{strategy.upper()}] ({len(chunks)} chunks total)")
        for r in results:
            c, s = r["chunk"], r["score"]
            print(f"    score={s:.3f} | {c.metadata.get('title','?')[:40]}")
            print(f"    \"{c.text[:100]}...\"")


# ============================================================
#  Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Chunking & Embedding Experiment")
    parser.add_argument("--n",       type=int,  default=100, help="Số tài liệu thử nghiệm")
    parser.add_argument("--size",    type=int,  default=200, help="Chunk size (số từ)")
    parser.add_argument("--overlap", type=int,  default=50,  help="Overlap (từ) cho fixed_size")
    parser.add_argument("--stride",  type=int,  default=100, help="Stride (từ) cho sliding_window")
    parser.add_argument("--embed",   action="store_true",    help="Chạy cả phần embedding")
    parser.add_argument("--fast",    action="store_true",    help="Dùng model nhỏ (MiniLM)")
    args = parser.parse_args()

    # 1. Load data
    docs = load_docs(n=args.n, min_words=50)
    if not docs:
        print("Không có tài liệu nào! Kiểm tra data/raw_v2/books/")
        return

    # 2. Chunking experiment
    all_chunks = run_chunking_experiment(
        docs,
        chunk_size=args.size,
        overlap=args.overlap,
        stride=args.stride,
    )

    # 3. Embedding experiment (tuỳ chọn)
    if args.embed:
        retriever = run_embedding_experiment(all_chunks, use_fast=args.fast)
        # So sánh thêm
        compare_sw_vs_fixed(
            all_chunks,
            retriever.embedder,
            query="Truyện Kiều của Nguyễn Du",
        )

    print("\n✓ Hoàn tất experiment!\n")


if __name__ == "__main__":
    main()
