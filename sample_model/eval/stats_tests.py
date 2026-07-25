"""
stats_tests.py -- Bổ sung 2 tiêu chí file phương pháp luận yêu cầu mà run_eval chưa có:

  (§2.9) Kiểm định ý nghĩa thống kê khi so 4 pipeline trên tập truy vấn nhỏ.
         Theo Urbano et al. 2019 / Smucker et al. 2007: dùng PAIRED T-TEST
         (và permutation test đối chứng), TRÁNH Wilcoxon ở cỡ mẫu nhỏ.
         So từng cặp pipeline trên nDCG@5 và MRR (per-query).

  (§4)   Ma trận nhầm lẫn OOS (in-scope × out-of-scope) → định lượng khả năng
         từ chối đúng lúc: OOS Recall + False Refusal Rate + Precision từ chối,
         thay cho con số "4/4 pass" định tính.

Chạy: .venv/Scripts/python.exe -m sample_model.eval.stats_tests
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy import stats

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))

from sample_model.retrieval import Retriever, CONFIDENCE_MIN          # noqa: E402
from sample_model.eval.run_eval import eval_ranking, MODES, MODE_KW   # noqa: E402

GOLDEN = ROOT / "golden" / "queries.json"
RESULTS = ROOT / "results"
K_STAT = 5          # cắt K để kiểm định (chatbot chỉ hiện vài kết quả)
N_PERM = 10000      # số hoán vị cho permutation test


def permutation_pvalue(a: np.ndarray, b: np.ndarray, n_perm: int = N_PERM) -> float:
    """Two-sided paired permutation test trên hiệu d = a - b (đối chứng t-test)."""
    d = a - b
    obs = abs(d.mean())
    if obs == 0:
        return 1.0
    rng = np.random.default_rng(20260720)
    signs = rng.choice([1.0, -1.0], size=(n_perm, len(d)))
    means = np.abs((signs * d).mean(axis=1))
    return float((means >= obs - 1e-12).mean())


def main():
    RESULTS.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    golden = json.load(open(GOLDEN, encoding="utf-8"))["queries"]
    retriever = Retriever.load()
    retriever.warm_up()

    inscope = [q for q in golden if q["query_type"] != "FALLBACK"]
    oos = [q for q in golden if q["query_type"] == "FALLBACK"]

    # ---------- per-query nDCG@5, MRR, MAP@5, P@5 cho từng pipeline ----------
    metrics = ["ndcg", "mrr", "map", "precision"]
    scores = {m: {metric: [] for metric in metrics} for m in MODES}
    for q in inscope:
        grades = {k: int(v) for k, v in q["relevant_grades"].items()}
        full = set(q["full_relevant_ids"])
        for mode in MODES:
            hits = retriever.search(q["query"], top_k=10, **MODE_KW[mode])
            ranked = [h.chunk_id for h in hits]
            r = eval_ranking(ranked, grades, full, K_STAT)
            for metric in metrics:
                scores[mode][metric].append(r[metric])
    for mode in MODES:
        for metric in metrics:
            scores[mode][metric] = np.array(scores[mode][metric], dtype=float)

    # ---------- paired t-test + permutation cho mọi cặp ----------
    stat_report = {"n_queries": len(inscope), "k": K_STAT, "pairs": {}}
    print(f"=== KIỂM ĐỊNH THỐNG KÊ (n={len(inscope)} câu in-scope, cắt K={K_STAT}) ===")
    for metric in ["ndcg", "mrr"]:
        print(f"\n--- Metric: {metric.upper()}@{K_STAT} (paired t-test / permutation, 2 phía) ---")
        print(f"{'cặp pipeline':30} {'Δmean':>8} {'t':>7} {'p(t)':>8} {'p(perm)':>9}  ý nghĩa")
        for a, b in combinations(MODES, 2):
            xa, xb = scores[a][metric], scores[b][metric]
            t, p = stats.ttest_rel(xa, xb)
            pp = permutation_pvalue(xa, xb)
            dmean = xa.mean() - xb.mean()
            sig = "*" if p < 0.05 else "ns"
            if np.isnan(p):
                t, p, sig = 0.0, 1.0, "ns"
            print(f"{a+' vs '+b:30} {dmean:>+8.3f} {t:>7.2f} {p:>8.3f} {pp:>9.3f}  {sig}")
            stat_report["pairs"].setdefault(metric, {})[f"{a}_vs_{b}"] = {
                "delta_mean": round(float(dmean), 4),
                "t": round(float(t), 3), "p_ttest": round(float(p), 4),
                "p_perm": round(float(pp), 4), "significant_0.05": bool(p < 0.05)}
    stat_report["mean_per_pipeline"] = {
        m: {metric: round(float(scores[m][metric].mean()), 4) for metric in metrics}
        for m in MODES}

    # ---------- Ma trận nhầm lẫn OOS (in-scope × out-of-scope) ----------
    # "Từ chối" = confidence < CONFIDENCE_MIN (hệ coi là ngoài kho → fallback).
    def refused(q):
        hits = retriever.search(q["query"], top_k=5, mode="hybrid", group_works=True)
        return retriever.confidence(hits) < CONFIDENCE_MIN

    tp = sum(refused(q) for q in oos)            # OOS bị từ chối đúng
    fn = len(oos) - tp                           # OOS lọt (trả lời bừa)
    fp = sum(refused(q) for q in inscope)        # in-scope bị từ chối oan
    tn = len(inscope) - fp                       # in-scope được trả lời đúng
    oos_recall = tp / len(oos) if oos else None
    false_refusal = fp / len(inscope) if inscope else None
    refuse_prec = tp / (tp + fp) if (tp + fp) else None

    cm = {"n_inscope": len(inscope), "n_oos": len(oos),
          "TP_oos_refused": tp, "FN_oos_leaked": fn,
          "FP_inscope_false_refuse": fp, "TN_inscope_answered": tn,
          "oos_recall": round(oos_recall, 4) if oos_recall is not None else None,
          "false_refusal_rate": round(false_refusal, 4) if false_refusal is not None else None,
          "refusal_precision": round(refuse_prec, 4) if refuse_prec is not None else None,
          "confidence_min": CONFIDENCE_MIN}
    stat_report["oos_confusion_matrix"] = cm

    print(f"\n=== MA TRẬN NHẦM LẪN OOS (ngưỡng cosine {CONFIDENCE_MIN}) ===")
    print(f"                     │  từ chối   trả lời")
    print(f"  OOS (n={len(oos):>2})          │   {tp:>4}      {fn:>4}   → OOS recall     = {cm['oos_recall']}")
    print(f"  In-scope (n={len(inscope):>2})    │   {fp:>4}      {tn:>4}   → false refusal  = {cm['false_refusal_rate']}")
    print(f"                                        → refusal precision = {cm['refusal_precision']}")

    out = RESULTS / f"stats_tests_{ts}.json"
    json.dump(stat_report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n💾 Lưu: {out}")


if __name__ == "__main__":
    main()
