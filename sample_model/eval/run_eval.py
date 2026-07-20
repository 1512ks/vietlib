"""
run_eval.py -- Đo lường ĐẦY ĐỦ trên golden set (sample model, chunk-level).

Sửa đúng 2 hạn chế bị flag ở hệ lớn (search/evaluator.py):
  1. Recall@K THẬT  : mẫu số = |full_relevant_ids| (tập relevant đầy đủ), không xấp xỉ bằng P@K.
  2. nDCG GRADED    : DCG = Σ (2^rel_i - 1)/log2(i+1) với rel ∈ {0,1,2}; IDCG từ nhãn lý tưởng.

Đo:
  - Retrieval: P@K, Recall@K, F1@K, MRR, nDCG@K (graded), MAP@K, HitRate@K
               × 3 mode (bm25 / vector / hybrid), K ∈ {1,3,5,10}.
  - Fallback : 4 câu ngoài miền → confidence < CONFIDENCE_MIN?
  - Stability: các cặp câu cùng ý khác diễn đạt → Jaccard top-5 + trùng top-1.
  - Multi-turn: viết lại câu hỏi bằng rewriter (cần GEMINI_API_KEY; nếu thiếu → dùng câu gốc, có ghi chú).
  - Generation (--judge): gọi eval/judge.py — Faithfulness + Answer Relevance (giám khảo Gemini)
               + Context Precision/Recall@5 (tính TRỰC TIẾP từ nhãn vàng) + citation + fallback pass.

Chạy:
  .venv/Scripts/python.exe -m sample_model.eval.run_eval            # retrieval + fallback + stability
  .venv/Scripts/python.exe -m sample_model.eval.run_eval --judge    # thêm khâu generation (cần API key)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent          # sample_model/
sys.path.insert(0, str(ROOT.parent))

from sample_model.retrieval import Retriever, CONFIDENCE_MIN   # noqa: E402

GOLDEN = ROOT / "golden" / "queries.json"
RESULTS = ROOT / "results"
KS = [1, 3, 5, 10]
# hybrid_group = hybrid + gộp hạng theo tác phẩm (cấu hình chạy thật của app — cải tiến #1)
MODES = ["bm25", "vector", "hybrid", "hybrid_group"]
MODE_KW = {"bm25": {"mode": "bm25"}, "vector": {"mode": "vector"},
           "hybrid": {"mode": "hybrid"},
           "hybrid_group": {"mode": "hybrid", "group_works": True}}


# ------------------------------------------------------------------
#  Nạp secrets → env (chạy CLI ngoài Streamlit)
# ------------------------------------------------------------------
def load_api_key_env() -> bool:
    import os
    if os.environ.get("GEMINI_API_KEY"):
        return True
    secrets = ROOT.parent / ".streamlit" / "secrets.toml"
    if secrets.exists():
        for line in secrets.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GEMINI_API_KEY"):
                os.environ["GEMINI_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                return True
    return False


# ------------------------------------------------------------------
#  Metric mức 1 truy vấn
# ------------------------------------------------------------------
def eval_ranking(ranked_ids: list, grades: dict, full_relevant: set, k: int) -> dict:
    """Tính bộ metric tại cắt K cho một truy vấn (nhãn graded + full relevant)."""
    top = ranked_ids[:k]
    rel_flags = [1 if cid in full_relevant else 0 for cid in top]
    n_rel_ret = sum(rel_flags)
    n_rel_total = len(full_relevant)

    precision = n_rel_ret / k
    recall = n_rel_ret / n_rel_total if n_rel_total else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    mrr = 0.0
    for rank, flag in enumerate(rel_flags, start=1):
        if flag:
            mrr = 1.0 / rank
            break

    hit = 1.0 if n_rel_ret > 0 else 0.0

    # nDCG graded: rel lấy từ nhãn 0/1/2
    def g(cid):
        return grades.get(cid, 1 if cid in full_relevant else 0)
    dcg = sum((2 ** g(cid) - 1) / math.log2(rank + 1)
              for rank, cid in enumerate(top, start=1))
    ideal = sorted((grades.get(cid, 1) for cid in full_relevant), reverse=True)[:k]
    idcg = sum((2 ** r - 1) / math.log2(rank + 1) for rank, r in enumerate(ideal, start=1))
    ndcg = dcg / idcg if idcg > 0 else 0.0

    # MAP@K: AP chuẩn hóa theo min(R, K)
    cum, ap = 0, 0.0
    for rank, flag in enumerate(rel_flags, start=1):
        if flag:
            cum += 1
            ap += cum / rank
    denom = min(n_rel_total, k)
    ap = ap / denom if denom else 0.0

    return {"precision": precision, "recall": recall, "f1": f1,
            "mrr": mrr, "ndcg": ndcg, "map": ap, "hit": hit}


# ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="store_true",
                    help="Chạy thêm khâu generation (Gemini judge) — cần GEMINI_API_KEY")
    ap.add_argument("--top-k", type=int, default=10)
    args = ap.parse_args()

    RESULTS.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    golden = json.load(open(GOLDEN, encoding="utf-8"))["queries"]
    retriever = Retriever.load()
    retriever.warm_up()

    has_key = load_api_key_env()
    rewriter = None
    if has_key:
        try:
            from sample_model.generate import Generator
            rewriter = Generator()
        except Exception as e:
            print(f"⚠️ Không tạo được rewriter ({e}) — MULTI_TURN dùng câu gốc.")

    # ---------- chuẩn bị câu hỏi truy hồi (multi-turn → viết lại) ----------
    eval_queries = []      # (q, search_query, note)
    for q in golden:
        if q["query_type"] == "FALLBACK":
            continue
        sq, note = q["query"], ""
        if q["query_type"] == "MULTI_TURN":
            if rewriter:
                sq = rewriter.contextualize_query(q["query"], q.get("history"))
                note = f"rewritten: {sq}"
            else:
                note = "NO-API: dùng câu gốc (chưa qua rewriter)"
        eval_queries.append((q, sq, note))

    # ---------- 1) Retrieval theo mode ----------
    report = {"timestamp": ts, "n_queries": len(eval_queries), "ks": KS,
              "confidence_min": CONFIDENCE_MIN, "modes": {}, "by_type": {},
              "multi_turn_rewrites": [n for (_, _, n) in eval_queries if n],
              }
    import time as _time
    import numpy as _np
    report["latency_ms"] = {}
    for mode in MODES:
        agg = {k: {m: [] for m in ["precision", "recall", "f1", "mrr", "ndcg", "map", "hit"]}
               for k in KS}
        per_type = {}
        lat = []
        for q, sq, _ in eval_queries:
            t0 = _time.perf_counter()
            hits = retriever.search(sq, top_k=max(KS), **MODE_KW[mode])
            lat.append((_time.perf_counter() - t0) * 1000)
            ranked = [h.chunk_id for h in hits]
            grades = {k: int(v) for k, v in q["relevant_grades"].items()}
            full = set(q["full_relevant_ids"])
            for k in KS:
                m = eval_ranking(ranked, grades, full, k)
                for name, val in m.items():
                    agg[k][name].append(val)
                if k == 5:
                    per_type.setdefault(q["query_type"], []).append(m)
        report["modes"][mode] = {
            k: {name: round(sum(vals) / len(vals), 4) for name, vals in agg[k].items()}
            for k in KS}
        report["latency_ms"][mode] = {
            "p50": round(float(_np.percentile(lat, 50)), 1),
            "p95": round(float(_np.percentile(lat, 95)), 1)}
        if mode == "hybrid_group":
            report["by_type"] = {
                t: {name: round(sum(x[name] for x in ms) / len(ms), 4)
                    for name in ms[0]}
                for t, ms in per_type.items()}

    # ---------- 1b) AUTHOR với K thích ứng (cải tiến #2 — cấu hình app) ----------
    author_rec = []
    for q, sq, _ in eval_queries:
        if q["query_type"] != "AUTHOR":
            continue
        k = retriever.suggest_top_k(sq)
        hits = retriever.search(sq, top_k=k, mode="hybrid", group_works=True)
        full = set(q["full_relevant_ids"])
        got = len({h.chunk_id for h in hits} & full)
        author_rec.append({"query_id": q["query_id"], "adaptive_k": k,
                          "recall": round(got / len(full), 4)})
    report["author_adaptive_k"] = {
        "detail": author_rec,
        "avg_recall": round(sum(x["recall"] for x in author_rec) / len(author_rec), 4)
        if author_rec else None}

    # ---------- 2) Fallback ----------
    fb = []
    for q in golden:
        if q["query_type"] != "FALLBACK":
            continue
        hits = retriever.search(q["query"], top_k=5, mode="hybrid")
        conf = retriever.confidence(hits)
        fb.append({"query_id": q["query_id"], "query": q["query"],
                   "confidence": round(conf, 3),
                   "detected_out_of_corpus": conf < CONFIDENCE_MIN})
    report["fallback"] = {
        "detail": fb,
        "accuracy": round(sum(x["detected_out_of_corpus"] for x in fb) / len(fb), 4) if fb else None}

    # ---------- 3) Stability (cặp paraphrase) ----------
    groups = {}
    for q in golden:
        if q.get("stability_group"):
            groups.setdefault(q["stability_group"], []).append(q)
    def _dedup_works(hits, k):
        seen, out = set(), []
        for h in hits:
            if h.work_id not in seen:
                seen.add(h.work_id); out.append(h.work_id)
            if len(out) >= k:
                break
        return out

    def _stability(group_works: bool) -> dict:
        stab = []
        for gname, qs in groups.items():
            chunk_tops, work_tops, card_tops = [], [], []
            for q in qs:
                hits = retriever.search(q["query"], top_k=5, mode="hybrid",
                                        group_works=group_works)
                chunk_tops.append([h.chunk_id for h in hits])
                work_tops.append([h.work_id for h in hits])
                card_tops.append(_dedup_works(hits, 3))   # 3 thẻ sách người dùng thấy
            cj = len(set(chunk_tops[0]) & set(chunk_tops[1])) / len(set(chunk_tops[0]) | set(chunk_tops[1]))
            wj = len(set(work_tops[0]) & set(work_tops[1])) / len(set(work_tops[0]) | set(work_tops[1]))
            dj = len(set(card_tops[0]) & set(card_tops[1])) / len(set(card_tops[0]) | set(card_tops[1]))
            stab.append({"group": gname,
                         "jaccard_chunk_top5": round(cj, 4),
                         "jaccard_work_top5": round(wj, 4),
                         "jaccard_card_top3": round(dj, 4),  # THẺ SÁCH thực tế
                         "same_top1_work": work_tops[0][0] == work_tops[1][0]})
        return {
            "detail": stab,
            "avg_jaccard_chunk_top5": round(sum(s["jaccard_chunk_top5"] for s in stab) / len(stab), 4),
            "avg_jaccard_work_top5": round(sum(s["jaccard_work_top5"] for s in stab) / len(stab), 4),
            "avg_jaccard_card_top3": round(sum(s["jaccard_card_top3"] for s in stab) / len(stab), 4),
            "same_top1_work_rate": round(sum(s["same_top1_work"] for s in stab) / len(stab), 4)}

    # So sánh TRƯỚC (hybrid thường) vs SAU cải tiến #1 (gộp theo tác phẩm — cấu hình app)
    report["stability"] = _stability(group_works=True)
    report["stability_baseline_no_group"] = _stability(group_works=False)

    # ---------- in bảng ----------
    print(f"\n=== RETRIEVAL (n={len(eval_queries)} câu, graded + full relevant) ===")
    header = f"{'mode':13} {'K':>3} {'P@K':>7} {'R@K':>7} {'F1':>7} {'MRR':>7} {'nDCG':>7} {'MAP':>7} {'Hit':>6}"
    print(header)
    for mode in MODES:
        for k in KS:
            m = report["modes"][mode][k]
            print(f"{mode:13} {k:>3} {m['precision']:>7.3f} {m['recall']:>7.3f} {m['f1']:>7.3f} "
                  f"{m['mrr']:>7.3f} {m['ndcg']:>7.3f} {m['map']:>7.3f} {m['hit']:>6.2f}")
    print("\n=== LATENCY TRUY HỒI (ms) ===")
    for mode, l in report["latency_ms"].items():
        print(f"  {mode:13} p50={l['p50']:>7.1f}  p95={l['p95']:>7.1f}")
    print("\n=== HYBRID_GROUP @5 THEO LOẠI CÂU (cấu hình app) ===")
    for t, m in report["by_type"].items():
        print(f"{t:11} P={m['precision']:.3f} R={m['recall']:.3f} nDCG={m['ndcg']:.3f} MRR={m['mrr']:.3f}")
    aa = report["author_adaptive_k"]
    print(f"\n=== AUTHOR VỚI K THÍCH ỨNG (cải tiến #2) ===  Recall TB = {aa['avg_recall']:.3f} "
          f"(so với trần 0.408 tại K=5)")
    for x in aa["detail"]:
        print(f"  {x['query_id']} K={x['adaptive_k']} recall={x['recall']:.3f}")
    print(f"\n=== FALLBACK ===  phát hiện ngoài miền: "
          f"{sum(x['detected_out_of_corpus'] for x in fb)}/{len(fb)} "
          f"(ngưỡng cosine {CONFIDENCE_MIN})")
    for x in fb:
        print(f"  {x['query_id']} conf={x['confidence']:.3f} -> {'✓ từ chối' if x['detected_out_of_corpus'] else '✗ LỌT'}")
    print(f"\n=== STABILITY (cặp paraphrase) — TRƯỚC vs SAU cải tiến gộp tác phẩm ===")
    b, a = report["stability_baseline_no_group"], report["stability"]
    print(f"  {'':22} {'chunk J@5':>10} {'work J@5':>10} {'CARD J@3':>10} {'top1-work':>10}")
    print(f"  {'baseline (no group)':22} {b['avg_jaccard_chunk_top5']:>10.3f} "
          f"{b['avg_jaccard_work_top5']:>10.3f} {b['avg_jaccard_card_top3']:>10.3f} "
          f"{b['same_top1_work_rate']:>10.0%}")
    print(f"  {'app (group_works)':22} {a['avg_jaccard_chunk_top5']:>10.3f} "
          f"{a['avg_jaccard_work_top5']:>10.3f} {a['avg_jaccard_card_top3']:>10.3f} "
          f"{a['same_top1_work_rate']:>10.0%}")

    out = RESULTS / f"retrieval_{ts}.json"
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n💾 Lưu: {out}")

    # ---------- 4) Generation judge ----------
    if args.judge:
        if not has_key:
            print("⚠️ Bỏ qua judge: không tìm thấy GEMINI_API_KEY.")
        else:
            from sample_model.eval.judge import run_judge
            run_judge(retriever, golden, RESULTS, ts)


if __name__ == "__main__":
    main()
