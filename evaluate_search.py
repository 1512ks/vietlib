"""
evaluate_search.py -- Chạy đánh giá retrieval đầy đủ và in kết quả.

So sánh 3 chiến lược:
    1. BM25 only
    2. Vector only
    3. Hybrid + Cross-Encoder Rerank

Metrics: Precision@K, Recall@K, F1@K, MRR với K ∈ {1, 3, 5, 10}
Kết quả lưu ra: data/evaluation_results/

Chạy:
    python evaluate_search.py                    # Full evaluation
    python evaluate_search.py --mode hybrid      # Chỉ hybrid
    python evaluate_search.py --mode bm25        # Chỉ BM25
    python evaluate_search.py --ks 1 3 5         # Custom K values
    python evaluate_search.py --no-rerank        # Hybrid, không rerank
    python evaluate_search.py --query-type SEMANTIC  # Lọc theo query type
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Fix Unicode encoding tren Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/evaluation_results")


# ============================================================
#  Build Pipeline (shared voi run_search.py)
# ============================================================
def build_pipeline(use_reranker: bool = True):
    from vector_store.qdrant_client_app import QdrantManager
    from chunking.embedder import Embedder
    from search.search_pipeline import SearchPipeline, PipelineConfig

    qdrant = QdrantManager(collection_name="vn_literature")
    embedder = Embedder(model_name=Embedder.FAST_MODEL)

    config = PipelineConfig(
        n_candidates=20,
        n_rerank=10,
        top_k=10,
        use_reranker=use_reranker,
        reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        bm25_cache_path=str(Path("data/bm25_index.pkl")),
    )

    return SearchPipeline.build(qdrant_manager=qdrant, embedder=embedder, config=config, force_rebuild_bm25=False)


# ============================================================
#  Print so sánh tổng hợp
# ============================================================
def print_comparison_table(reports: dict):
    """In bảng so sánh tất cả modes."""
    try:
        from tabulate import tabulate
        has_tabulate = True
    except ImportError:
        has_tabulate = False

    print(f"\n{'='*75}")
    print("  📊 TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ RETRIEVAL")
    print(f"{'='*75}")

    # Bảng Precision@K
    for metric_name, attr in [("Precision@K", "avg_precision"), ("MRR", "avg_mrr")]:
        print(f"\n  {metric_name}:")
        ks = sorted(next(iter(reports.values())).ks)
        headers = ["Mode"] + [f"@{k}" for k in ks]
        rows = []
        for mode, report in reports.items():
            vals = getattr(report, attr)
            rows.append([mode] + [f"{vals.get(k, 0):.4f}" for k in ks])

        if has_tabulate:
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        else:
            print("  " + " | ".join(f"{h:>12}" for h in headers))
            for row in rows:
                print("  " + " | ".join(f"{str(v):>12}" for v in row))

    # Latency
    print("\n  Latency trung bình:")
    latency_rows = [
        [mode, f"{report.avg_latency_ms:.0f}ms"]
        for mode, report in reports.items()
    ]
    if has_tabulate:
        print(tabulate(latency_rows, headers=["Mode", "Avg Latency"], tablefmt="simple"))
    else:
        for row in latency_rows:
            print(f"    {row[0]}: {row[1]}")

    print()


# ============================================================
#  Single mode evaluation
# ============================================================
def run_single_mode(pipeline, mode: str, ks: list, use_reranker: bool, query_type: str = None):
    from search.evaluator import Evaluator
    from search.test_queries import get_all_queries, get_queries_by_type

    queries = get_queries_by_type(query_type) if query_type else get_all_queries()
    if not queries:
        logger.error(f"Không có queries cho type={query_type}")
        return None, None

    # Override reranker setting dựa trên mode
    _use_rerank = use_reranker and mode == "hybrid"

    evaluator = Evaluator(pipeline, mode=mode)
    # Chỉnh pipeline để không rerank khi mode != hybrid
    pipeline.config.use_reranker = _use_rerank

    logger.info(f"\n--- Đánh giá mode={mode}, rerank={_use_rerank} ({len(queries)} queries) ---")
    report = evaluator.evaluate(test_queries=queries, ks=ks)
    evaluator.print_report(report, title=f"Mode: {mode.upper()} {'+ Rerank' if _use_rerank else ''}")

    return evaluator, report


# ============================================================
#  Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Đánh giá Semantic Search Engine (Precision@K, Recall@K, MRR)"
    )
    parser.add_argument("--mode", choices=["all", "hybrid", "bm25", "vector"],
                        default="all", help="Mode cần đánh giá (default: all = so sánh tất cả)")
    parser.add_argument("--ks", type=int, nargs="+", default=[1, 3, 5, 10],
                        help="Danh sách K (default: 1 3 5 10)")
    parser.add_argument("--no-rerank", action="store_true",
                        help="Không dùng Cross-Encoder reranking")
    parser.add_argument("--query-type", choices=["FACTUAL", "AUTHOR", "SEMANTIC"],
                        default=None, help="Chỉ đánh giá một loại query")
    parser.add_argument("--save", action="store_true", default=True,
                        help="Lưu kết quả ra JSON (default: True)")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR),
                        help=f"Thư mục lưu kết quả (default: {OUTPUT_DIR})")
    args = parser.parse_args()

    use_reranker = not args.no_rerank
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Build pipeline
    print("\n⏳ Đang khởi tạo Search Engine...")
    t0 = time.time()
    pipeline = build_pipeline(use_reranker=use_reranker)
    print(f"✅ Pipeline ready ({(time.time()-t0)*1000:.0f}ms)\n")

    reports = {}

    if args.mode == "all":
        modes_to_run = [
            ("bm25",   False),
            ("vector", False),
            ("hybrid", False),   # Hybrid WITHOUT rerank
            ("hybrid", True),    # Hybrid WITH rerank
        ]
    else:
        modes_to_run = [(args.mode, use_reranker)]

    for (mode, rerank) in modes_to_run:
        label = f"{mode}{'_rerank' if rerank else ''}"
        evaluator, report = run_single_mode(
            pipeline, mode, args.ks, rerank, args.query_type
        )
        if report:
            reports[label] = report

            if args.save:
                out_path = output_dir / f"eval_{label}_{timestamp}.json"
                evaluator.save_report(report, str(out_path))

    # Comparison table (chỉ khi chạy all)
    if len(reports) > 1:
        print_comparison_table(reports)

        if args.save:
            # Lưu summary tổng hợp
            summary = {
                mode: {
                    "avg_precision": r.avg_precision,
                    "avg_recall": r.avg_recall,
                    "avg_mrr": r.avg_mrr,
                    "avg_latency_ms": r.avg_latency_ms,
                }
                for mode, r in reports.items()
            }
            summary_path = output_dir / f"eval_summary_{timestamp}.json"
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(f"  💾 Summary saved → {summary_path}")

    print("\n✅ Evaluation hoàn tất!\n")


if __name__ == "__main__":
    main()
