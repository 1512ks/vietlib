"""
run_search.py -- Demo CLI để thử nghiệm Semantic Search Engine.

Chạy:
    python run_search.py                          # Interactive mode
    python run_search.py "truyện của Nam Cao"     # Single query
    python run_search.py "..." --mode bm25        # BM25 only
    python run_search.py "..." --mode vector      # Vector only
    python run_search.py "..." --no-rerank        # Hybrid, không rerank
    python run_search.py "..." --top-k 10         # Lấy 10 kết quả
    python run_search.py "..." --compare          # So sánh cả 3 modes
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Cho phep import cac module trong thu muc goc
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================
#  Load pipeline (shared giua cac lan chay)
# ============================================================
def build_pipeline(use_reranker: bool = True, reranker_model: str = None):
    """Khoi tao SearchPipeline voi QdrantDB + Embedder."""
    from vector_store.qdrant_client_app import QdrantManager
    from chunking.embedder import Embedder
    from search.search_pipeline import SearchPipeline, PipelineConfig

    logger.info("Đang khởi tạo Qdrant & Embedder...")
    qdrant = QdrantManager(collection_name="vn_literature_gbooks")
    embedder = Embedder(model_name=Embedder.FAST_MODEL)  # MiniLM-L12 (384d, nhanh hơn)

    config = PipelineConfig(
        n_candidates=20,
        n_rerank=10,
        top_k=5,
        use_reranker=use_reranker,
        reranker_model=reranker_model or "cross-encoder/ms-marco-MiniLM-L-6-v2",
        bm25_cache_path=str(Path("data/bm25_index.pkl")),
    )

    pipeline = SearchPipeline.build(
        qdrant_manager=qdrant,
        embedder=embedder,
        config=config,
    )
    return pipeline


# ============================================================
#  Print so sánh 3 modes
# ============================================================
def compare_modes(pipeline, query: str, top_k: int = 5):
    """So sánh kết quả BM25 vs Vector vs Hybrid+Rerank."""
    from tabulate import tabulate

    print(f"\n{'='*70}")
    print(f"  So sánh 3 chiến lược search")
    print(f"  Query: \"{query}\"")
    print(f"{'='*70}")

    modes = [
        ("BM25 only",          "bm25",   False),
        ("Vector only",        "vector", False),
        ("Hybrid (no rerank)", "hybrid", False),
        ("Hybrid + Rerank",    "hybrid", True),
    ]

    for label, mode, rerank in modes:
        t0 = time.time()
        results = pipeline.search(query, top_k=top_k, use_reranker=rerank, mode=mode)
        elapsed = (time.time() - t0) * 1000

        print(f"\n  ── {label} ({elapsed:.0f}ms) ──")
        rows = []
        for i, r in enumerate(results[:top_k], 1):
            title = r.metadata.get("title", r.metadata.get("name", "N/A"))[:40]
            author = r.metadata.get("author", r.metadata.get("authors", "?"))[:20]
            score = f"{r.rerank_score:.3f}" if r.rerank_score else f"{r.score:.4f}"
            rows.append([i, title, author, score])

        print(tabulate(rows, headers=["#", "Tên sách", "Tác giả", "Score"], tablefmt="simple"))


# ============================================================
#  Interactive mode
# ============================================================
def interactive_mode(pipeline, top_k: int = 5, mode: str = "hybrid", use_reranker: bool = True):
    """Chạy interactive REPL."""
    print("\n" + "="*60)
    print("  🔍 Vietnamese Library Semantic Search")
    print("  Gõ 'quit' hoặc 'q' để thoát")
    print("  Gõ 'compare: <query>' để so sánh các mode")
    print("="*60 + "\n")

    while True:
        try:
            query = input("  Câu hỏi: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Thoát.")
            break

        if not query:
            continue
        if query.lower() in ("quit", "q", "exit"):
            print("  Thoát.")
            break

        # Compare mode
        if query.lower().startswith("compare:"):
            real_query = query[8:].strip()
            if real_query:
                compare_modes(pipeline, real_query, top_k=top_k)
            continue

        # Normal search
        t0 = time.time()
        results = pipeline.search(query, top_k=top_k, use_reranker=use_reranker, mode=mode)
        elapsed = (time.time() - t0) * 1000

        pipeline.print_results(results, query=query)
        print(f"  ⏱ {elapsed:.0f}ms | mode={mode} | rerank={use_reranker}\n")


# ============================================================
#  Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Semantic Search Engine CLI cho thư viện tiếng Việt"
    )
    parser.add_argument("query", nargs="?", default=None,
                        help="Câu hỏi tìm kiếm (bỏ trống để vào interactive mode)")
    parser.add_argument("--mode", choices=["hybrid", "bm25", "vector"],
                        default="hybrid", help="Chiến lược search (default: hybrid)")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Số kết quả trả về (default: 5)")
    parser.add_argument("--no-rerank", action="store_true",
                        help="Tắt Cross-Encoder reranking")
    parser.add_argument("--compare", action="store_true",
                        help="So sánh tất cả các mode")
    parser.add_argument("--reranker-model", default=None,
                        help="Override Cross-Encoder model")
    parser.add_argument("--verbose", action="store_true",
                        help="Log chi tiết")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    use_reranker = not args.no_rerank and args.mode == "hybrid"

    # Build pipeline
    print("\n⏳ Đang khởi tạo Search Engine...")
    t0 = time.time()
    pipeline = build_pipeline(
        use_reranker=use_reranker,
        reranker_model=args.reranker_model,
    )
    print(f"✅ Ready! ({(time.time()-t0)*1000:.0f}ms)\n")

    # Run
    if args.query:
        if args.compare:
            compare_modes(pipeline, args.query, top_k=args.top_k)
        else:
            t0 = time.time()
            results = pipeline.search(
                args.query,
                top_k=args.top_k,
                use_reranker=use_reranker,
                mode=args.mode,
            )
            elapsed = (time.time() - t0) * 1000
            pipeline.print_results(results, query=args.query)
            print(f"  ⏱ {elapsed:.0f}ms | mode={args.mode} | rerank={use_reranker}\n")
    else:
        interactive_mode(
            pipeline,
            top_k=args.top_k,
            mode=args.mode,
            use_reranker=use_reranker,
        )


if __name__ == "__main__":
    main()
