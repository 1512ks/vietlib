"""
eval_group_works_main.py -- Port cải tiến 'group_works' (gộp hạng theo tác phẩm) từ
sample model sang HỆ CHÍNH và đo BEFORE/AFTER trên cùng candidate pool (hybrid RRF top-20).

Không tốn API (chỉ retrieval). Tái dùng metric keyword của search/evaluator.
Chạy: .venv/Scripts/python.exe eval_group_works_main.py
"""
import sys, json, time
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent))

from evaluate_search import build_pipeline
from search.test_queries import get_all_queries
from search.evaluator import _is_relevant, _ndcg_at_k, _ap_at_k

KS = [1, 3, 5, 10]
POOL = 20


def group_works(results):
    """Gộp theo tác phẩm: điểm sách = max điểm chunk; xếp chunk theo (hạng sách, -điểm)."""
    book_score = {}
    for r in results:
        key = (r.metadata.get("title") or r.metadata.get("name") or r.doc_id)
        book_score[key] = max(book_score.get(key, -1e9), r.score)
    book_rank = {k: i for i, (k, _) in
                 enumerate(sorted(book_score.items(), key=lambda kv: -kv[1]))}
    def keyfn(r):
        key = (r.metadata.get("title") or r.metadata.get("name") or r.doc_id)
        return (book_rank[key], -r.score)
    return sorted(results, key=keyfn)


def metrics_for(order, kws):
    flags = [_is_relevant(r, kws) for r in order]
    n_rel = sum(flags)
    out = {}
    for k in KS:
        fk = flags[:k]
        p = sum(fk) / k
        mrr = next((1.0 / i for i, f in enumerate(flags, 1) if f), 0.0)
        out[k] = {"precision": p,
                  "ndcg": _ndcg_at_k(fk, n_rel),
                  "map": _ap_at_k(fk),
                  "mrr": mrr,
                  "hit": 1.0 if any(fk) else 0.0}
    return out


def main():
    print("⏳ Build pipeline...")
    pipe = build_pipeline(use_reranker=False)
    queries = get_all_queries()
    print(f"✅ {len(queries)} truy vấn\n")

    agg = {tag: {k: defaultdict(list) for k in KS} for tag in ("before", "after")}
    for q in queries:
        results = pipe.hybrid.search(q.query, top_k=POOL,
                                     bm25_weight=0.5, vector_weight=0.5, parallel=True)
        kws = q.relevant_keywords
        base = metrics_for(results, kws)
        grp = metrics_for(group_works(results), kws)
        for k in KS:
            for m, v in base[k].items():
                agg["before"][k][m].append(v)
            for m, v in grp[k].items():
                agg["after"][k][m].append(v)

    def avg(tag, k, m):
        xs = agg[tag][k][m]
        return sum(xs) / len(xs)

    print(f"{'':6} {'K':>3} {'nDCG':>8} {'MRR':>8} {'MAP':>8} {'P@K':>8} {'Hit':>6}")
    for tag in ("before", "after"):
        label = "BEFORE" if tag == "before" else "AFTER "
        for k in KS:
            print(f"{label:6} {k:>3} {avg(tag,k,'ndcg'):>8.3f} {avg(tag,k,'mrr'):>8.3f} "
                  f"{avg(tag,k,'map'):>8.3f} {avg(tag,k,'precision'):>8.3f} {avg(tag,k,'hit'):>6.2f}")
    print("\n=== Δ (after − before) tại các K ===")
    for k in KS:
        d_ndcg = avg("after",k,"ndcg") - avg("before",k,"ndcg")
        d_mrr = avg("after",k,"mrr") - avg("before",k,"mrr")
        d_map = avg("after",k,"map") - avg("before",k,"map")
        print(f"  @{k:<2}  ΔnDCG={d_ndcg:+.3f}  ΔMRR={d_mrr:+.3f}  ΔMAP={d_map:+.3f}")

    out = {"n": len(queries), "ks": KS,
           "before": {k: {m: round(avg('before',k,m),4) for m in ['ndcg','mrr','map','precision','hit']} for k in KS},
           "after":  {k: {m: round(avg('after', k,m),4) for m in ['ndcg','mrr','map','precision','hit']} for k in KS}}
    p = Path("data/evaluation_results/group_works_main_beforeafter.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n💾 Lưu: {p}")


if __name__ == "__main__":
    main()
