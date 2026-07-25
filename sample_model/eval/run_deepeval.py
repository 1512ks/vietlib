"""
run_deepeval.py -- Chạy DeepEval THẬT với Gemini làm judge trên dataset đã cache.

Đọc results/ragas_dataset.json (đầu vào GIỐNG RAGAS để đối chứng công bằng).
Metric: Faithfulness, AnswerRelevancy, ContextualPrecision, ContextualRecall (G-Eval kiểu RAGAS).
Judge: gemini-2.5-flash (temperature 0) — dùng GeminiModel gốc của DeepEval nếu có.

Chạy: .venv/Scripts/python.exe -m sample_model.eval.run_deepeval [--n 12]
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))
DATASET = ROOT / "results" / "ragas_dataset.json"
OUT = ROOT / "results" / "deepeval_real_results.json"


def load_key():
    if os.environ.get("GEMINI_API_KEY"):
        return
    sec = ROOT.parent / ".streamlit" / "secrets.toml"
    if sec.exists():
        for l in sec.read_text(encoding="utf-8").splitlines():
            if l.strip().startswith("GEMINI_API_KEY"):
                os.environ["GEMINI_API_KEY"] = l.split("=", 1)[1].strip().strip('"').strip("'")


def get_judge():
    """GeminiModel gốc của DeepEval (xử lý đúng schema structured output)."""
    from deepeval.models import GeminiModel
    return GeminiModel(model="gemini-2.5-flash",
                       api_key=os.environ["GEMINI_API_KEY"], temperature=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    args = ap.parse_args()
    load_key()

    data = json.load(open(DATASET, encoding="utf-8"))[: args.n]

    from deepeval.test_case import LLMTestCase
    from deepeval.metrics import (FaithfulnessMetric, AnswerRelevancyMetric,
                                  ContextualPrecisionMetric, ContextualRecallMetric)
    judge = get_judge()

    m_faith = FaithfulnessMetric(model=judge, threshold=0.7)
    m_ansrel = AnswerRelevancyMetric(model=judge, threshold=0.7)
    m_ctxp = ContextualPrecisionMetric(model=judge, threshold=0.7)
    m_ctxr = ContextualRecallMetric(model=judge, threshold=0.7)

    rows, agg = [], {"faithfulness": [], "answer_relevancy": [],
                     "contextual_precision": [], "contextual_recall": []}
    print(f"Chạy DeepEval trên {len(data)} mẫu (judge=gemini-2.5-flash)...")
    for d in data:
        tc = LLMTestCase(input=d["question"], actual_output=d["answer"],
                         retrieval_context=d["contexts"], expected_output=d["ground_truth"])
        r = {"query_id": d["query_id"], "type": d["type"]}
        for key, metric in [("faithfulness", m_faith), ("answer_relevancy", m_ansrel),
                            ("contextual_precision", m_ctxp), ("contextual_recall", m_ctxr)]:
            try:
                metric.measure(tc)
                r[key] = round(float(metric.score), 4)
                agg[key].append(metric.score)
            except Exception as e:
                r[key] = None
                print(f"    {d['query_id']} {key} ERR: {str(e)[:80]}")
        rows.append(r)
        print(f"  {d['query_id']} [{d['type']:10}] "
              + " ".join(f"{k}={r[k]}" for k in agg))

    summary = {k: (round(sum(v)/len(v), 4) if v else None) for k, v in agg.items()}
    out = {"n": len(data), "judge": "gemini-2.5-flash", "summary": summary, "per_query": rows}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n=== DeepEval (thư viện thật) TB ===\n{summary}\n💾 Lưu: {OUT}")


if __name__ == "__main__":
    main()
