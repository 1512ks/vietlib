# Đánh giá toàn diện Sample Model theo khung phương pháp luận RAG (bộ test 50)

> Nguồn khung: `research_phuong_phap_luan_metric_RAG.md`. Chạy ngày 2026-07-20 (bộ golden nâng lên **50 câu**).
> Corpus: **51 tác phẩm / 163 chunk** (dữ liệu sạch, ground-truth ĐẦY ĐỦ).
> Golden set: **50 truy vấn** = 44 in-scope (14 Factual · 11 Author · 12 Semantic · 7 Multi-turn) + 6 Fallback (OOS); cả 50 câu có ground-truth answer.
> Embedding: `AITeamVN/Vietnamese_Embedding` (bge-m3). Tách từ BM25: whitespace (âm tiết) — hạn chế đã ghi.
> Giám khảo generation: Gemini 2.5-flash, temperature 0. Chấm generation trên subset **28 câu** có GT (13 Factual + 8 Semantic + 7 Multi-turn).

---

## A. Retrieval — 4 pipeline (ablation), n=44 in-scope

> **BM25 tách TỪ tiếng Việt bằng pyvi** (research §5): thay `.split()` (âm tiết) bằng `ViTokenizer` ('thư viện'→'thư_viện'), dùng CÙNG hàm `vi_tokenize` ở index + query. Kết quả dưới đây là **SAU cải tiến**.

| Pipeline | K | P@K | R@K (thật) | MRR | **nDCG@K** | MAP@K |
|---|--:|--:|--:|--:|--:|--:|
| BM25 | 1 | 0.818 | 0.246 | 0.818 | 0.621 | 0.818 |
| BM25 | 5 | 0.554 | 0.719 | 0.901 | 0.710 | 0.712 |
| BM25 | 10 | 0.345 | 0.829 | 0.901 | 0.742 | 0.711 |
| Vector | 1 | 0.909 | 0.271 | 0.909 | 0.788 | 0.909 |
| Vector | 5 | 0.568 | 0.727 | 0.936 | 0.745 | 0.763 |
| Vector | 10 | 0.366 | 0.858 | 0.939 | 0.799 | 0.767 |
| Hybrid | 5 | 0.605 | 0.772 | 0.962 | 0.781 | 0.799 |
| **Hybrid+group (app)** | 1 | 0.932 | 0.277 | 0.932 | 0.765 | 0.932 |
| **Hybrid+group (app)** | 5 | **0.668** | **0.840** | **0.966** | **0.842** | **0.887** |
| **Hybrid+group (app)** | 10 | 0.405 | 0.930 | 0.966 | 0.871 | 0.880 |

**Latency (app):** p50 161ms / p95 184ms (pyvi thêm ~6ms — không đáng kể). Recall là **Recall THẬT**. nDCG dùng **graded 0/1/2**.

**Tác động tách từ pyvi (trước → sau), nổi bật ở BM25 và lan sang hybrid:**
| Metric@5 | BM25 | Hybrid | Hybrid+group (app) |
|---|--:|--:|--:|
| nDCG | 0.624 → **0.710** | 0.725 → **0.781** | 0.812 → **0.842** |
| MRR | 0.823 → **0.901** | 0.939 → **0.962** | 0.943 → **0.966** |
| MAP | 0.569 → **0.712** | 0.696 → **0.799** | 0.846 → **0.887** |
| Recall | 0.630 → **0.719** | 0.705 → **0.772** | 0.822 → **0.840** |

### Hybrid+group @5 theo loại câu
| Loại | P@5 | R@5 | nDCG@5 | MRR |
|---|--:|--:|--:|--:|
| FACTUAL | 0.571 | 0.976 | 0.955 | 1.000 |
| AUTHOR | 0.873 | 0.619 | 0.664 | 0.955 |
| SEMANTIC | 0.667 | 0.723 | 0.755 | 0.875 |
| MULTI_TURN | 0.400 | 1.000 | 0.856 | 0.929 |

AUTHOR với **K thích ứng**: Recall TB **0.918** (so với trần 0.408 tại K=5 cố định).

---

## B. Kiểm định thống kê — paired t-test + permutation (n=44, K=5)

**nDCG@5 (SAU khi tách từ pyvi):**
| Cặp pipeline | Δmean | t | p (t-test) | p (perm) | Ý nghĩa |
|---|--:|--:|--:|--:|:--:|
| BM25 vs Vector | −0.040 | −1.39 | 0.172 | 0.171 | **không** (BM25 đã bắt kịp) |
| BM25 vs Hybrid | −0.080 | −3.46 | 0.001 | 0.001 | có ý nghĩa |
| BM25 vs Hybrid+group | −0.138 | −4.91 | 0.000 | 0.000 | có ý nghĩa |
| Vector vs Hybrid | −0.040 | −1.40 | 0.169 | 0.172 | không |
| **Vector vs Hybrid+group** | −0.098 | −3.23 | **0.002** | 0.001 | **có ý nghĩa** |
| **Hybrid vs Hybrid+group** | −0.058 | −3.15 | **0.003** | 0.003 | **có ý nghĩa** |

**MRR@5:** BM25 vs Vector không còn khác biệt (p=0.15); hybrid_group vẫn dẫn đầu.

**Kết luận (đổi so với trước pyvi):** Tách từ tiếng Việt nâng BM25 đến mức **không còn thua Vector có ý nghĩa** (p=0.17) — chứng minh lexical + word-segmentation cạnh tranh được với dense embedding trên miền này. **Hybrid+group giờ vượt CẢ Vector lẫn Hybrid có ý nghĩa** (p=0.002 / 0.003) → cấu hình app là winner có bằng chứng thống kê.

---

## C. Generation — kiểu RAGAS (Gemini t=0, n=28 câu có GT)

| Metric | Giá trị | Ngưỡng | Đạt? |
|---|--:|---|:--:|
| **Faithfulness** | **0.968** | > 0.9 | ✅ |
| Hallucination rate (1 − faith) | 0.032 | thấp | ✅ |
| **Answer Relevance** | **0.911** | > 0.8 | ✅ |
| **Context Precision@5** (RAGAS rank-aware) | **0.933** | > 0.8 tốt | ✅ |
| Context Precision@5 (naive ∩/5, tham chiếu) | 0.543 | — | — |
| Context Recall@5 | 0.902 | chẩn đoán | ✅ |

> **Ghi chú Context Precision:** bản đầu dùng công thức thô `|top5∩rel|/5` (0.543) — bị phạt oan vì trung bình mỗi câu chỉ có 3.36 chunk relevant (< 5) nên trần đã ~0.61. Đã sửa `eval/judge.py` dùng **đúng định nghĩa RAGAS rank-aware** (chuẩn hóa theo số relevant lấy được, có trọng số thứ hạng) → **0.933**. Đây là con số đúng chuẩn để báo cáo.
| Coherence / Fluency (1–5) | 5.0 / 5.0 | — | ✅ |
| Citation valid rate | 1.00 | — | ✅ |
| Latency sinh câu (ms) | p50 5028 / p95 6945 | — | — |

---

## D. Fallback / OOS — ma trận nhầm lẫn (n=50)

| | Hệ **từ chối** | Hệ **trả lời** | |
|---|:--:|:--:|---|
| **OOS** (n=6) | 6 (TP) | 0 (FN) | → **OOS Recall = 1.000** |
| **In-scope** (n=44) | 1 (FP) | 43 (TN) | → **False Refusal = 0.023** |

- OOS Recall **100%** (≥90% ✅) · False Refusal **2.3%** (≤10% ✅) · Refusal Precision 0.857.
- 6/6 OOS (kể cả **Harry Potter, Trăm năm cô đơn**) đều bị **chặn bằng ngưỡng confidence** → không bịa. Ca từ chối oan duy nhất: q13 (Nguyễn Tuân, conf 0.397 — ca biên).

---

## E. Stability (cặp paraphrase, n=4 nhóm)

| Cấu hình | Jaccard chunk@5 | Jaccard work@5 | Jaccard thẻ@3 | Trùng top-1 |
|---|--:|--:|--:|--:|
| Baseline (không gộp) | 0.441 | 0.607 | 0.633 | 60% |
| **App (gộp tác phẩm)** | **0.500** | **0.683** | **0.683** | 60% |

Gộp theo tác phẩm cải thiện ổn định ở cả 3 mức Jaccard.

---

## F. Ánh xạ tiêu chí khung → đã đo (bộ 50)

| § | Tiêu chí | Trạng thái | Kết quả |
|---|---|:--:|---|
| 2.1–2.7 | P/R/F1/MRR/nDCG/MAP/Hit@K | ✅ | nDCG@5 app 0.812, MRR 0.943 |
| 2.8 | bpref / pooling bias | N/A | qrels ĐẦY ĐỦ → không cần |
| 2.9 | Paired t-test | ✅ | Bảng B |
| 3.1 | Faithfulness / Hallucination | ✅ | 0.968 / 0.032 |
| 3.1 | Answer Relevance | ✅ | 0.911 |
| 3.1 | Context Precision/Recall | ✅ | 0.543 / 0.902 |
| 3.2 | LLM-as-a-judge | ✅ | Gemini 2.5-flash |
| 4 | OOS Recall / False Refusal | ✅ | 1.000 / 0.023 |
| 4 | Robustness / Stability | ✅ | Bảng E |
| 4 | TSR / SUS | ⏳ | cần người dùng thật |
| 5 | Tách từ tiếng Việt cho BM25 | ✅ | pyvi ViTokenizer (word-level) — đã triển khai |
| 5 | Embedding VN | ✅ | bge-m3 |
| 6 | Ablation + Threats to Validity | ✅ | 4 pipeline + mẫu §6 |
