"""
judge.py -- Đánh giá khâu GENERATION kiểu RAGAS bằng giám khảo Gemini (temperature 0).

4 metric (định nghĩa bám RAGAS):
  - Faithfulness       : tách câu trả lời thành các claim, đếm tỉ lệ claim được ngữ cảnh đỡ
                         (giám khảo Gemini, JSON output).
  - Answer Relevance   : mức câu trả lời giải quyết đúng câu hỏi, thang 0-1 (giám khảo Gemini).
  - Context Precision@5: |top-5 ∩ full_relevant| / 5   — tính TRỰC TIẾP từ nhãn vàng
  - Context Recall@5   : |top-5 ∩ full_relevant| / |full_relevant| — từ nhãn vàng
    (mạnh hơn bản LLM-proxy của RAGAS vì golden set có tập relevant ĐẦY ĐỦ).

Thêm:
  - citation_valid : mọi marker [n] ngầm đều trỏ vào nguồn có thật trong prompt.
  - Fallback pass  : 4 câu ngoài miền → hệ thống từ chối lịch sự, không bịa.

Được gọi từ run_eval.py (--judge); cần GEMINI_API_KEY.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from sample_model.retrieval import Retriever, CONFIDENCE_MIN
from sample_model.generate import Generator, cited_indices, strip_citations

JUDGE_MODEL = "gemini-2.5-flash"
# Tập câu chấm generation (subset ~30 theo khuyến nghị RAGAS để tiết kiệm API):
# 13 FACTUAL + 8 SEMANTIC + 7 MULTI_TURN = 28 câu có ground-truth answer.
JUDGE_IDS = ["q01", "q02", "q03", "q04", "q05", "q06", "q07", "q08",
             "q33", "q34", "q35", "q36", "q37",
             "q15", "q17", "q19", "q20", "q42", "q43", "q44", "q45",
             "q21", "q22", "q23", "q24", "q46", "q47", "q48"]
REFUSAL_MARKERS = ["tiếc quá", "xin lỗi", "chưa giúp", "không tìm thấy",
                   "chỉ có các tác phẩm văn học việt nam", "ngoài phạm vi"]


def context_precision_at_k(ranked: list, relevant: set, k: int) -> float:
    """Context Precision@K theo ĐÚNG định nghĩa RAGAS (rank-aware):
        CP@K = Σ_{i=1..K} (Precision@i · v_i) / (số chunk relevant trong top-K)
    với v_i=1 nếu chunk ở hạng i relevant. Chuẩn hóa theo số relevant THỰC SỰ
    lấy được (không chia cứng cho K) → không bị phạt oan khi |relevant| < K.
    """
    top = ranked[:k]
    hits_rel = 0
    weighted = 0.0
    for i, cid in enumerate(top, start=1):
        if cid in relevant:
            hits_rel += 1
            weighted += hits_rel / i          # Precision@i tại vị trí relevant
    return weighted / hits_rel if hits_rel else 0.0


def _judge_json(gen: Generator, prompt: str, retries: int = 2):
    """Gọi giám khảo, ép JSON; thất bại → None."""
    for i in range(retries + 1):
        try:
            raw = gen.main.generate(prompt, temperature=0.0)
            m = re.search(r"\{.*\}", raw, re.S)
            if m:
                return json.loads(m.group(0))
        except Exception:
            pass
        time.sleep(2 * (i + 1))
    return None


def judge_faithfulness(gen: Generator, contexts: str, answer: str):
    """→ (score 0-1, n_claims, n_supported) hoặc (None,..) nếu judge lỗi."""
    prompt = (
        "Bạn là giám khảo đánh giá độ TRUNG THỰC (faithfulness) của câu trả lời RAG.\n"
        "Nhiệm vụ: (1) tách CÂU TRẢ LỜI thành các claim (khẳng định dữ kiện độc lập, "
        "bỏ qua câu chào/mời hỏi tiếp); (2) với từng claim, kiểm tra NGỮ CẢNH có thông tin "
        "đỡ cho claim đó không (supported=true/false). Chỉ dựa vào NGỮ CẢNH, không dùng "
        "kiến thức ngoài.\n"
        'Trả về JSON: {"claims": [{"claim": "...", "supported": true}]}\n\n'
        f"NGỮ CẢNH:\n{contexts}\n\nCÂU TRẢ LỜI:\n{answer}\n"
    )
    out = _judge_json(gen, prompt)
    if not out or "claims" not in out or not out["claims"]:
        return None, 0, 0
    claims = out["claims"]
    sup = sum(1 for c in claims if c.get("supported"))
    return sup / len(claims), len(claims), sup


def judge_fluency(gen: Generator, answer: str):
    """Chấm MẠCH LẠC (coherence: cấu trúc, liên kết ý) và TRÔI CHẢY (fluency:
    tiếng Việt tự nhiên) thang 1-5 — lấp ô 'chưa định lượng' của Khung B/C.
    → (coherence, fluency) hoặc (None, None)."""
    prompt = (
        "Bạn là giám khảo tiếng Việt. Chấm CÂU TRẢ LỜI của một trợ lý thư viện theo 2 tiêu chí, "
        "thang 1-5 (5 = xuất sắc):\n"
        "- coherence (mạch lạc): bố cục rõ, các ý nối nhau hợp lý, không lặp/đứt mạch.\n"
        "- fluency (trôi chảy): tiếng Việt tự nhiên, đúng ngữ pháp, không ngô nghê/dịch máy.\n"
        'Trả về JSON: {"coherence": 1-5, "fluency": 1-5}\n\n'
        f"CÂU TRẢ LỜI:\n{answer}\n"
    )
    out = _judge_json(gen, prompt)
    try:
        c = max(1, min(5, int(out["coherence"])))
        f = max(1, min(5, int(out["fluency"])))
        return c, f
    except Exception:
        return None, None


def judge_answer_relevance(gen: Generator, query: str, answer: str, gt: str):
    """→ score 0-1 hoặc None."""
    prompt = (
        "Bạn là giám khảo đánh giá độ LIÊN QUAN của câu trả lời với câu hỏi (answer relevance).\n"
        "Cho CÂU HỎI, CÂU TRẢ LỜI CỦA HỆ THỐNG và ĐÁP ÁN THAM CHIẾU. Chấm mức câu trả lời "
        "giải quyết đúng và đủ trọng tâm câu hỏi (không chấm văn phong): 1.0 = trả lời đúng "
        "trọng tâm và khớp đáp án; 0.5 = đúng một phần/thiếu ý chính; 0.0 = lạc đề hoặc sai.\n"
        'Trả về JSON: {"score": 0.0-1.0, "reason": "ngắn gọn"}\n\n'
        f"CÂU HỎI: {query}\nCÂU TRẢ LỜI CỦA HỆ THỐNG:\n{answer}\n\nĐÁP ÁN THAM CHIẾU:\n{gt}\n"
    )
    out = _judge_json(gen, prompt)
    try:
        return max(0.0, min(1.0, float(out["score"]))) if out else None
    except Exception:
        return None


def run_judge(retriever: Retriever, golden: list, results_dir: Path, ts: str):
    print("\n=== GENERATION JUDGE (kiểu RAGAS, giám khảo Gemini t=0) ===")
    gen = Generator()
    by_id = {q["query_id"]: q for q in golden}
    rows = []

    gen_latency = []
    for qid in JUDGE_IDS:
        q = by_id[qid]
        history = q.get("history")
        search_q = gen.contextualize_query(q["query"], history) if history else q["query"]
        hits = retriever.search(search_q, top_k=5, mode="hybrid", group_works=True)
        conf = retriever.confidence(hits)
        t0 = time.perf_counter()
        answer_raw = gen.answer(q["query"], hits, low_confidence=conf < CONFIDENCE_MIN,
                                history=history)
        gen_latency.append((time.perf_counter() - t0) * 1000)
        answer = strip_citations(answer_raw)

        contexts = "\n".join(f"[{h.source_idx}] ({h.chunk_id}) {h.text}" for h in hits)
        full = set(q["full_relevant_ids"])
        top5 = [h.chunk_id for h in hits]
        ctx_prec = context_precision_at_k(top5, full, 5)          # RAGAS chuẩn (rank-aware)
        ctx_prec_naive = len(set(top5) & full) / len(top5)        # bản thô (tham chiếu)
        ctx_rec = len(set(top5) & full) / len(full) if full else 0.0

        faith, n_claims, n_sup = judge_faithfulness(gen, contexts, answer)
        ans_rel = judge_answer_relevance(gen, q["query"], answer, q["ground_truth_answer"])
        coh, flu = judge_fluency(gen, answer)

        cited = cited_indices(answer_raw)
        citation_valid = all(1 <= n <= len(hits) for n in cited) if cited else False

        rows.append({
            "query_id": qid, "type": q["query_type"],
            "faithfulness": faith, "n_claims": n_claims, "n_supported": n_sup,
            "answer_relevance": ans_rel,
            "coherence_1_5": coh, "fluency_1_5": flu,
            "context_precision@5": round(ctx_prec, 4),
            "context_precision@5_naive": round(ctx_prec_naive, 4),
            "context_recall@5": round(ctx_rec, 4),
            "has_citation": bool(cited), "citation_valid": citation_valid,
            "confidence": round(conf, 3),
            "answer": answer,
        })
        f_str = f"{faith:.2f}" if faith is not None else "n/a"
        a_str = f"{ans_rel:.2f}" if ans_rel is not None else "n/a"
        print(f"  {qid} [{q['query_type']:10}] faith={f_str} ({n_sup}/{n_claims}) "
              f"ansrel={a_str} coh={coh} flu={flu} ctxP@5={ctx_prec:.2f} "
              f"ctxR@5={ctx_rec:.2f} cite={'✓' if citation_valid else '✗'}")
        time.sleep(1.0)   # tránh chạm rate limit free tier

    # ---------- Fallback pass (từ chối lịch sự, không bịa) ----------
    print("\n--- Fallback (từ chối) ---")
    fb_rows = []
    for q in golden:
        if q["query_type"] != "FALLBACK":
            continue
        hits = retriever.search(q["query"], top_k=5, mode="hybrid", group_works=True)
        conf = retriever.confidence(hits)
        ans = strip_citations(gen.answer(q["query"], hits,
                                         low_confidence=conf < CONFIDENCE_MIN))
        refused = any(m in ans.lower() for m in REFUSAL_MARKERS)
        fb_rows.append({"query_id": q["query_id"], "confidence": round(conf, 3),
                        "refused": refused, "answer": ans})
        print(f"  {q['query_id']} conf={conf:.3f} -> {'✓ từ chối' if refused else '✗ TRẢ LỜI BỪA'}")
        time.sleep(1.0)

    # ---------- tổng hợp ----------
    def avg(key):
        vals = [r[key] for r in rows if r[key] is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    import numpy as _np
    summary = {
        "judge_model": JUDGE_MODEL, "n_judged": len(rows),
        "avg_faithfulness": avg("faithfulness"),
        "avg_answer_relevance": avg("answer_relevance"),
        "avg_coherence_1_5": avg("coherence_1_5"),
        "avg_fluency_1_5": avg("fluency_1_5"),
        "avg_context_precision@5": avg("context_precision@5"),          # RAGAS chuẩn
        "avg_context_precision@5_naive": avg("context_precision@5_naive"),
        "avg_context_recall@5": avg("context_recall@5"),
        "citation_valid_rate": round(sum(r["citation_valid"] for r in rows) / len(rows), 4),
        "fallback_refusal_rate": round(sum(r["refused"] for r in fb_rows) / len(fb_rows), 4)
        if fb_rows else None,
        "full_answer_latency_ms": {
            "p50": round(float(_np.percentile(gen_latency, 50)), 0),
            "p95": round(float(_np.percentile(gen_latency, 95)), 0)},
    }
    print("\n=== TỔNG HỢP GENERATION ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    out = results_dir / f"generation_{ts}.json"
    json.dump({"summary": summary, "detail": rows, "fallback": fb_rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"💾 Lưu: {out}")
    return summary
