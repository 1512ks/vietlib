"""
build_ragas_dataset.py -- Dựng dataset chuẩn cho RAGAS & DeepEval (đầu vào GIỐNG HỆT nhau).

Mỗi mẫu gồm: query_id, question, answer (sinh thật), contexts (list text chunk top-5),
ground_truth (đáp án chuẩn). Lưu 1 lần → 2 framework đọc cùng file, không sinh lại.

Chạy: .venv/Scripts/python.exe -m sample_model.eval.build_ragas_dataset
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))

from sample_model.retrieval import Retriever, CONFIDENCE_MIN
from sample_model.generate import Generator, strip_citations
from sample_model.eval.judge import JUDGE_IDS

OUT = ROOT / "results" / "ragas_dataset.json"


def load_key():
    if os.environ.get("GEMINI_API_KEY"):
        return
    sec = ROOT.parent / ".streamlit" / "secrets.toml"
    if sec.exists():
        for l in sec.read_text(encoding="utf-8").splitlines():
            if l.strip().startswith("GEMINI_API_KEY"):
                os.environ["GEMINI_API_KEY"] = l.split("=", 1)[1].strip().strip('"').strip("'")


def main():
    load_key()
    golden = {q["query_id"]: q for q in json.load(open(ROOT / "golden" / "queries.json", encoding="utf-8"))["queries"]}
    r = Retriever.load(); r.warm_up()
    gen = Generator()

    rows = []
    for qid in JUDGE_IDS:
        q = golden[qid]
        hist = q.get("history")
        sq = gen.contextualize_query(q["query"], hist) if hist else q["query"]
        hits = r.search(sq, top_k=5, mode="hybrid", group_works=True)
        conf = r.confidence(hits)
        ans = strip_citations(gen.answer(q["query"], hits,
                                         low_confidence=conf < CONFIDENCE_MIN, history=hist))
        rows.append({
            "query_id": qid,
            "type": q["query_type"],
            "question": q["query"],
            "answer": ans,
            "contexts": [h.text for h in hits],
            "ground_truth": q["ground_truth_answer"],
        })
        print(f"  {qid} [{q['query_type']:10}] ans={len(ans)} ký tự, {len(hits)} contexts")

    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n💾 Lưu {len(rows)} mẫu → {OUT}")


if __name__ == "__main__":
    main()
