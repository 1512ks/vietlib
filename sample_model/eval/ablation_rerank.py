"""
ablation_rerank.py -- Thử thêm Cross-Encoder RERANK lên top-N của hybrid (sample model)
để xem có đẩy nDCG/MRR/Precision lên "tiệm cận hoàn hảo" không.

So 3 cấu hình trên cùng golden set: hybrid | hybrid_group | hybrid_group + rerank.
Reranker: cross-encoder tiếng Việt nếu chỉ định, mặc định ms-marco đa ngữ (nhẹ).

Chạy: .venv/Scripts/python.exe -m sample_model.eval.ablation_rerank [--model <ce>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))
from sample_model.retrieval import Retriever            # noqa: E402
from sample_model.eval.run_eval import eval_ranking     # noqa: E402

GOLDEN = ROOT / "golden" / "queries.json"
KS = [1, 5, 10]
RERANK_POOL = 20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="cross-encoder/ms-marco-MiniLM-L-6-v2")
    args = ap.parse_args()

    r = Retriever.load()
    golden = [q for q in json.load(open(GOLDEN, encoding="utf-8"))["queries"]
              if q["query_type"] != "FALLBACK"]

    from sentence_transformers import CrossEncoder
    print(f"⏳ Nạp reranker: {args.model}")
    ce = CrossEncoder(args.model)

    configs = ["hybrid", "hybrid_group", "hybrid_group+rerank"]
    agg = {c: {k: {x: [] for x in ["precision", "recall", "ndcg", "mrr", "map", "hit"]}
               for k in KS} for c in configs}

    for q in golden:
        grades = {k: int(v) for k, v in q["relevant_grades"].items()}
        full = set(q["full_relevant_ids"])

        base = {
            "hybrid": r.search(q["query"], top_k=max(KS), mode="hybrid"),
            "hybrid_group": r.search(q["query"], top_k=max(KS), mode="hybrid", group_works=True),
        }
        # rerank: lấy pool lớn từ hybrid_group rồi cross-encoder xếp lại
        pool = r.search(q["query"], top_k=RERANK_POOL, mode="hybrid", group_works=True)
        scores = ce.predict([[q["query"], h.text] for h in pool])
        reranked = [h for h, _ in sorted(zip(pool, scores), key=lambda z: -z[1])]
        base["hybrid_group+rerank"] = reranked

        for c in configs:
            ranked = [h.chunk_id for h in base[c]]
            for k in KS:
                m = eval_ranking(ranked, grades, full, k)
                for x in agg[c][k]:
                    agg[c][k][x].append(m[x])

    print("\n" + "=" * 66)
    print(f"RERANK ABLATION (pool={RERANK_POOL}, reranker={args.model})")
    print("=" * 66)
    print(f"{'config':22} {'K':>3} {'P@K':>7} {'R@K':>7} {'nDCG':>7} {'MRR':>7} {'MAP':>7}")
    res = {}
    for c in configs:
        res[c] = {}
        for k in KS:
            m = {x: round(sum(v) / len(v), 4) for x, v in agg[c][k].items()}
            res[c][k] = m
            print(f"{c:22} {k:>3} {m['precision']:>7.3f} {m['recall']:>7.3f} "
                  f"{m['ndcg']:>7.3f} {m['mrr']:>7.3f} {m['map']:>7.3f}")
    d5, r5 = res["hybrid_group"][5], res["hybrid_group+rerank"][5]
    print(f"\n>>> @5 nDCG: group={d5['ndcg']:.3f} → +rerank={r5['ndcg']:.3f} "
          f"({r5['ndcg']-d5['ndcg']:+.3f}) | MRR {d5['mrr']:.3f}→{r5['mrr']:.3f} "
          f"({r5['mrr']-d5['mrr']:+.3f})")
    json.dump(res, open(ROOT / "results" / "ablation_rerank.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
