"""
ablation_embedding.py -- Ablation 1 biến: đổi embedding MiniLM ↔ bge-m3 trên CÙNG
corpus sample (163 chunk), cùng golden set, cùng BM25. Tách bạch phần cải tiến do
KIẾN TRÚC (chọn embedding tiếng Việt) khỏi phần "corpus nhỏ dễ hơn".

- MiniLM = paraphrase-multilingual-MiniLM-L12-v2 (chính là embedding của HỆ LỚN).
- bge-m3 = AITeamVN/Vietnamese_Embedding (embedding của sample model).

Đo vector-only và hybrid (RRF) cho cả hai, K∈{1,5,10} với nhãn graded + full relevant.

Chạy: .venv/Scripts/python.exe -m sample_model.eval.ablation_embedding
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))
from sample_model.eval.run_eval import eval_ranking   # noqa: E402

IDX = ROOT / "index"
GOLDEN = ROOT / "golden" / "queries.json"
KS = [1, 5, 10]
RRF_K = 60
MODELS = {
    "MiniLM (như hệ lớn)": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "bge-m3 (sample)": "AITeamVN/Vietnamese_Embedding",
}


def rrf(order_a, order_b, n):
    ra = {int(i): 1.0 / (RRF_K + r) for r, i in enumerate(order_a)}
    rb = {int(i): 1.0 / (RRF_K + r) for r, i in enumerate(order_b)}
    return {i: ra.get(i, 0.0) + rb.get(i, 0.0) for i in range(n)}


def main():
    docs = json.load(open(IDX / "docs.json", encoding="utf-8"))
    texts = [d["text"] for d in docs]
    ids = [d["chunk_id"] for d in docs]
    n = len(docs)
    bm25 = pickle.load(open(IDX / "bm25.pkl", "rb"))["bm25"]

    golden = [q for q in json.load(open(GOLDEN, encoding="utf-8"))["queries"]
              if q["query_type"] != "FALLBACK"]

    from sentence_transformers import SentenceTransformer
    results = {}
    for label, mid in MODELS.items():
        print(f"\n⏳ Nạp {label} ...")
        m = SentenceTransformer(mid)
        dvec = np.asarray(m.encode(texts, normalize_embeddings=True, batch_size=16),
                          dtype=np.float32)
        agg = {mode: {k: {x: [] for x in ["precision", "recall", "ndcg", "mrr", "map", "hit"]}
                      for k in KS} for mode in ("vector", "hybrid")}
        for q in golden:
            qv = np.asarray(m.encode([q["query"]], normalize_embeddings=True),
                            dtype=np.float32)[0]
            cos = dvec @ qv
            vorder = np.argsort(-cos)
            bm = np.asarray(bm25.get_scores(q["query"].lower().split()), dtype=np.float32)
            border = np.argsort(-bm)
            fused = rrf(vorder, border, n)
            ranked = {
                "vector": [ids[i] for i in vorder],
                "hybrid": [ids[i] for i, _ in sorted(fused.items(), key=lambda kv: -kv[1])],
            }
            grades = {k: int(v) for k, v in q["relevant_grades"].items()}
            full = set(q["full_relevant_ids"])
            for mode in ("vector", "hybrid"):
                for k in KS:
                    mm = eval_ranking(ranked[mode], grades, full, k)
                    for x in agg[mode][k]:
                        agg[mode][k][x].append(mm[x])
        results[label] = {mode: {k: {x: round(sum(v) / len(v), 4)
                                     for x, v in agg[mode][k].items()} for k in KS}
                          for mode in ("vector", "hybrid")}
        del m

    print("\n" + "=" * 74)
    print("ABLATION EMBEDDING — cùng corpus sample (163 chunk), cùng golden, cùng BM25")
    print("=" * 74)
    for mode in ("vector", "hybrid"):
        print(f"\n### {mode.upper()}")
        print(f"{'embedding':22} {'K':>3} {'P@K':>7} {'R@K':>7} {'nDCG':>7} {'MRR':>7} {'MAP':>7} {'Hit':>6}")
        for label in MODELS:
            for k in KS:
                r = results[label][mode][k]
                print(f"{label:22} {k:>3} {r['precision']:>7.3f} {r['recall']:>7.3f} "
                      f"{r['ndcg']:>7.3f} {r['mrr']:>7.3f} {r['map']:>7.3f} {r['hit']:>6.2f}")
    # Điểm nhấn: vector@1 hai model
    v_mini = results["MiniLM (như hệ lớn)"]["vector"][1]["precision"]
    v_bge = results["bge-m3 (sample)"]["vector"][1]["precision"]
    print(f"\n>>> Vector P@1: MiniLM={v_mini:.3f}  →  bge-m3={v_bge:.3f}  "
          f"(+{(v_bge-v_mini):.3f}) — cùng corpus, chỉ đổi embedding.")

    out = ROOT / "results" / "ablation_embedding.json"
    json.dump(results, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"💾 Lưu: {out}")


if __name__ == "__main__":
    main()
