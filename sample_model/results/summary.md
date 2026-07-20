# KẾT QUẢ ĐO — Sample Model (benchmark có nhãn đầy đủ)

> Chạy ngày 2026-07-20 (lần 2, sau khi chốt prompt CSKH + thông tin bán) · corpus 163 chunk / 51 tác phẩm ·
> golden set 32 câu · embedding `AITeamVN/Vietnamese_Embedding` (bge-m3) · giám khảo Gemini 2.5 Flash (t=0).
> File chi tiết: `retrieval_20260720_082400.json`, `generation_20260720_082400.json`.
> Đối chiếu đầy đủ với phương pháp luận bảo vệ (3 khung A/B/C + RAG Triad): xem `danh_gia_3khung_ABC.md`.

> **Cải tiến v2 (2026-07-20):** cấu hình chạy thật của app giờ là **hybrid_group** (gộp hạng theo
> tác phẩm) + **K thích ứng cho câu AUTHOR**. 6 mục cải tiến tự động: xem `cai_tien_v2.md`.

## 1. Retrieval (28 câu có nhãn graded + full relevant set → Recall THẬT)

| Mode | K | P@K | R@K | F1 | MRR | nDCG (graded) | MAP | HitRate |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| bm25 | 5 | 0.436 | 0.610 | 0.466 | 0.841 | 0.620 | 0.571 | 0.96 |
| vector | 5 | 0.564 | 0.713 | 0.572 | 0.964 | 0.782 | 0.792 | 0.96 |
| hybrid | 5 | 0.514 | 0.682 | 0.533 | 0.964 | 0.742 | 0.703 | 1.00 |
| **hybrid_group** (app) | 5 | **0.621** | **0.780** | **0.632** | 0.946 | **0.801** | **0.835** | **1.00** |
| **hybrid_group** (app) | 10 | 0.393 | **0.873** | 0.496 | 0.946 | **0.839** | **0.815** | 1.00 |

- **Gộp hạng theo tác phẩm nâng rõ mọi metric relevance** so với hybrid thường (R@10 0.799→0.873, nDCG@10 0.776→0.839, MAP@10 0.690→0.815).
- **HitRate@3 = 100%**, MRR ~0.95–0.96 — mọi câu đều có chunk đúng trong top-3.
- Vector đơn lẻ mạnh trên corpus sạch (bge-m3); hybrid_group được chọn cho app vì bền với từ khóa hiếm + gom đủ chunk của một tác phẩm.

### Theo loại câu (hybrid_group@5 — cấu hình app)
| Loại | P@5 | R@5 | nDCG | MRR |
|---|--:|--:|--:|--:|
| FACTUAL | 0.533 | 0.963 | 0.950 | 1.000 |
| AUTHOR | 0.857 | 0.559 | 0.653 | 1.000 |
| SEMANTIC | 0.650 | 0.656 | 0.715 | 0.812 |
| MULTI_TURN (qua rewriter) | 0.350 | 1.000 | 0.899 | 1.000 |

- **AUTHOR với K thích ứng** (K=13 cho câu có tên tác giả): Recall **0.408 → 0.872** — vượt trần cứng của K=5.
- Latency truy hồi (đo p50/p95): **~145ms / ~230ms**.

## 2. Fallback (4 câu ngoài miền cố ý: sách nước ngoài, self-help, vật lý, tác giả bịa)

**4/4 phát hiện đúng** (cosine 0.197–0.299, đều dưới ngưỡng 0.40) và **4/4 từ chối lịch sự, không bịa** khi qua khâu sinh. Biên an toàn: câu trong kho thấp nhất 0.479 vs câu ngoài kho cao nhất 0.310.

## 3. Search Stability (4 cặp câu cùng ý, khác diễn đạt)

| Mức đo | Jaccard top-5 | Trùng top-1 |
|---|--:|--:|
| Chunk | 0.384 | 25% |
| **Tác phẩm (người dùng thấy)** | **0.571** | **50%** |

Ghi chú trung thực: hai cách diễn đạt cùng ý vẫn đổ về **cùng tác phẩm** nhiều hơn cùng chunk (chunk khác section của cùng cuốn sách). Đây là điểm hạn chế đã đo được và nêu trong báo cáo, không giấu.

## 4. Generation — kiểu RAGAS, giám khảo Gemini t=0 (16 câu có ground-truth)

> **Variance:** số khâu sinh dao động ±vài % giữa các lần chạy (generator + judge đều là LLM,
> không tất định tuyệt đối kể cả t=0). Báo cáo kèm khoảng quan sát qua 3 lần chạy.

| Metric | Giá trị (khoảng qua 3 lần) | Ghi chú |
|---|--:|---|
| **Faithfulness** | **0.95–0.99** | phần lớn câu đạt 1.00; 1–2 ca semantic khó ~0.80–0.89 (giữ nguyên làm bằng chứng trung thực) |
| **Answer Relevance** | **0.94–1.00** | hầu hết trả lời đúng trọng tâm |
| **Coherence (1–5)** | **4.9–5.0** | *mới* — lấp ô ⚠️ Khung B/C |
| **Fluency (1–5)** | **5.0** | *mới* — tiếng Việt tự nhiên |
| Context Precision@5 | ~0.51 | tính TRỰC TIẾP từ nhãn vàng (mạnh hơn LLM-proxy) |
| Context Recall@5 | ~0.90 | như trên |
| Citation valid | 100% | mọi marker [n] ngầm đều trỏ nguồn có thật |
| Fallback refusal | 4/4 | từ chối lịch sự, không bịa |
| **Red-team defense** | **10/10** | *mới* — sau khi vá lỗ hổng lộ prompt (rt09) |
| Latency sinh (full) | p50 ~4.1s · p95 ~6.6s | *mới* — phụ thuộc API Gemini |

## 5. Cách đọc số liệu khi bảo vệ
- Đây là **tập đối chứng có nhãn đầy đủ** (controlled benchmark) — KHÔNG phải hiệu năng hệ lớn 11.759 chunk. Giá trị: đo **chuẩn học thuật** (Recall thật, nDCG graded) và **tái lập được**.
- Số không tròn 100% ở Faithfulness/Stability là bằng chứng benchmark trung thực, có ca khó.
- Reproduce: xem README.md cùng thư mục.
