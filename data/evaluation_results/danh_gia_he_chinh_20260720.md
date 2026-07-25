# Đánh giá hệ chính (main app) theo khung phương pháp luận RAG (bộ test 50)

> Nguồn khung: `research_phuong_phap_luan_metric_RAG.md`. Chạy 2026-07-20 (bộ test nâng lên **50**).
> Corpus THẬT: **11.759 chunk** (Qdrant Cloud `vn_literature`, dữ liệu crawl, có nhiễu).
> Test retrieval: **50 truy vấn** (14 Factual · 15 Author · 21 Semantic) — `search/test_queries.py`.
> Test generation: **50 kịch bản** (16 Factual · 13 Author · 14 Semantic · 7 HARD ngoài corpus) — `test_chatbot.py`.
> Embedding: `paraphrase-multilingual-MiniLM-L12-v2` (FAST_MODEL). Reranker: `ms-marco-MiniLM-L-6-v2`.
> Giám khảo generation: keyword-match + citation + fallback (KHÔNG có RAGAS LLM-judge như sample model).

---

## A. Retrieval — 4 pipeline (ablation), n=50

| Pipeline | K | P@K | R@K | MRR | **nDCG@K** | MAP@K | Hit@K |
|---|--:|--:|--:|--:|--:|--:|--:|
| BM25 | 1 | 0.820 | 0.820 | 0.891 | 0.820 | 0.820 | 0.82 |
| BM25 | 5 | 0.728 | 0.728 | 0.891 | 0.809 | 0.878 | 1.00 |
| BM25 | 10 | 0.666 | 0.666 | 0.891 | 0.903 | 0.833 | 1.00 |
| Vector | 1 | 0.300 | 0.300 | 0.414 | 0.300 | 0.300 | 0.30 |
| Vector | 5 | 0.332 | 0.332 | 0.414 | 0.399 | 0.386 | 0.58 |
| Vector | 10 | 0.292 | 0.292 | 0.414 | 0.475 | 0.390 | 0.68 |
| **Hybrid** | 1 | 0.880 | 0.880 | 0.919 | 0.880 | 0.880 | 0.88 |
| **Hybrid** | 5 | 0.712 | 0.712 | 0.919 | 0.866 | 0.896 | 1.00 |
| **Hybrid** | 10 | 0.538 | 0.538 | 0.919 | 0.921 | 0.867 | 1.00 |
| Hybrid+rerank | 5 | 0.712 | 0.712 | 0.919 | 0.866 | 0.896 | 1.00 |

**Latency TB:** BM25 46ms · Vector 610ms · Hybrid 837ms · Hybrid+rerank 608ms.

**Nhận xét:**
- **Hybrid tốt nhất** (nDCG@5 0.866, MRR 0.919, Hit@5 1.00). Ổn định so với bộ 30 câu trước (0.841).
- **Vector đơn lẻ YẾU** (nDCG@5 0.40, Hit@5 0.58) — FAST_MODEL MiniLM trên corpus lớn nhiễu; **ngược với sample model** (vector mạnh nhờ bge-m3 + data sạch).
- **Rerank trùng hybrid** ở metric thứ hạng (relevant đã nằm trong top-K), chỉ giảm latency.
- ⚠️ **P@K = R@K** mọi mode → **ground-truth keyword** (Recall xấp xỉ). Hạn chế mà **sample model khắc phục**.

---

## B. Generation / End-to-End — 50 kịch bản

| Chỉ số | Giá trị |
|---|---|
| **Pass rate (auto, keyword)** | **46/50 = 92.0%** |
| Có trích dẫn nguồn | 43/50 = 86.0% |
| Latency TB toàn pipeline | 6.008 ms |
| Độ dài TB | 174 từ |

**Theo loại:**
| Loại | Pass | Citation | Latency TB |
|---|--:|--:|--:|
| FACTUAL | 16/16 | 16/16 | 6.369 ms |
| AUTHOR | 13/13 | 13/13 | 4.970 ms |
| SEMANTIC | 12/14 | 12/14 | 7.472 ms |
| HARD (ngoài corpus) | 5/7 | 2/7 | 4.181 ms |

**4 ca FAIL:**
- TC_H01 (câu cảm xúc "buồn, cô đơn") → fallback, thiếu citation.
- TC_S10 (thơ cách mạng kháng chiến) → fallback, thiếu keyword.
- ⚠️ **TC_HARD03 (Trăm năm cô đơn) & TC_HARD04 (Nhà giả kim) → HALLUCINATE**: hệ **trả lời nội dung 2 tiểu thuyết nước ngoài KHÔNG có trong kho** (sinh từ kiến thức LLM, không grounding). Đây là **lỗ hổng thật**: hệ chính chỉ chặn OOS phi văn học (Naruto, One Piece, toán, ẩm thực, thể thao — 5/7 từ chối đúng) nhưng **để lọt tiểu thuyết nước ngoài nổi tiếng**.

> **So sánh mấu chốt:** sample model chặn được CẢ 6 câu OOS (kể cả Harry Potter, Trăm năm cô đơn) nhờ **ngưỡng confidence cosine < 0.40**; hệ chính chưa áp cổng confidence chặt như vậy → hallucinate 2 ca. → **Kiến nghị: port cơ chế confidence-gate của sample model sang hệ chính.**

- Chống hallucination OOS phi văn học: **5/7 từ chối đúng, không bịa**.
- Pass rate trình bày **2 con số trung thực**: auto **92.0%** / thủ công (tính cả fallback hợp lý ở ca cảm xúc) ~**96%**.

---

## C. Ánh xạ tiêu chí + so sánh với sample model

| § | Tiêu chí | Hệ chính (11.759 chunk, n=50) | Sample model (163 chunk, n=50) |
|---|---|---|---|
| 2 | nDCG@5 (pipeline tốt nhất) | **0.866** (hybrid) | 0.812 (hybrid+group) |
| 2 | MRR@5 | 0.919 | 0.943 |
| — | Recall THẬT | ❌ xấp xỉ (P=R keyword) | ✅ full relevant |
| — | nDCG graded | ❌ nhị phân | ✅ graded 0/1/2 |
| 2.9 | Paired t-test | ❌ (qrels không đủ) | ✅ |
| 3.1 | Faithfulness / Answer Rel (RAGAS) | ❌ chỉ keyword pass | ✅ 0.968 / 0.911 |
| 3.1 | Hallucination | ⚠️ lọt 2 tiểu thuyết NN | ✅ rate 0.032, chặn 6/6 OOS |
| 4 | Citation | ✅ 86% | ✅ 100% valid |
| 4 | OOS / False Refusal | ⚠️ 5/7 HARD (lọt 2) | ✅ recall 1.0 / false-refuse 2.3% |
| 4 | Pass rate E2E | ✅ 92% auto / ~96% thủ công | — (đo bằng RAGAS) |
| — | Latency | retrieval 46–837ms, gen 6.0s | retrieval ~155ms, gen ~5.0s |

**Kết luận:** Hệ chính mạnh về **quy mô thật + retrieval hybrid (nDCG@5 0.87) + pass rate 92%**, nhưng lộ **lỗ hổng grounding** với tiểu thuyết nước ngoài nổi tiếng (hallucinate 2/7 HARD) và bị giới hạn đo lường bởi keyword ground-truth. Sample model bù đúng các khoảng trống này (Recall thật, graded nDCG, RAGAS, confidence-gate chặn 6/6 OOS). Bộ đôi = **quy mô thật + đo lường chuẩn học thuật**.
