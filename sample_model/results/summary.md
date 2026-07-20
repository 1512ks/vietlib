# KẾT QUẢ ĐO — Sample Model (benchmark có nhãn đầy đủ)

> Chạy ngày 2026-07-20 (lần 2, sau khi chốt prompt CSKH + thông tin bán) · corpus 163 chunk / 51 tác phẩm ·
> golden set 32 câu · embedding `AITeamVN/Vietnamese_Embedding` (bge-m3) · giám khảo Gemini 2.5 Flash (t=0).
> File chi tiết: `retrieval_20260720_082400.json`, `generation_20260720_082400.json`.
> Đối chiếu đầy đủ với phương pháp luận bảo vệ (3 khung A/B/C + RAG Triad): xem `danh_gia_3khung_ABC.md`.

## 1. Retrieval (28 câu có nhãn graded + full relevant set → Recall THẬT)

| Mode | K | P@K | R@K | F1 | MRR | nDCG (graded) | MAP | HitRate |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| bm25 | 5 | 0.436 | 0.610 | 0.466 | 0.841 | 0.620 | 0.571 | 0.96 |
| vector | 5 | 0.564 | 0.713 | 0.572 | 0.964 | 0.782 | 0.792 | 0.96 |
| **hybrid** | 5 | 0.514 | 0.682 | 0.533 | **0.964** | 0.742 | 0.703 | **1.00** |
| hybrid | 10 | 0.329 | 0.799 | 0.429 | 0.964 | 0.776 | 0.690 | 1.00 |

- **Hybrid đạt HitRate@3-10 = 100%** và MRR 0.964 — mọi câu đều có chunk đúng trong top-3.
- Vector đơn lẻ nhỉnh hơn hybrid trên corpus nhỏ sạch (bge-m3 rất mạnh tiếng Việt); hybrid vẫn được chọn cho app vì bền hơn với từ khóa hiếm (tên riêng, số liệu) — đúng vai trò "lưới an toàn" của BM25.
- **AUTHOR Recall@5 = 0.408 là trần lý thuyết**: tác giả 4 tác phẩm có 13 chunk relevant, K=5 chỉ vớt tối đa 5/13 = 0.385~0.4. Ở K=10: Recall tổng lên 0.799.

### Theo loại câu (hybrid@5)
| Loại | P@5 | R@5 | nDCG | MRR |
|---|--:|--:|--:|--:|
| FACTUAL | 0.533 | 0.963 | 0.963 | 1.000 |
| AUTHOR | 0.657 | 0.408 | 0.482 | 1.000 |
| SEMANTIC | 0.450 | 0.445 | 0.644 | 0.875 |
| MULTI_TURN (qua rewriter) | 0.350 | 1.000 | 0.891 | 1.000 |

## 2. Fallback (4 câu ngoài miền cố ý: sách nước ngoài, self-help, vật lý, tác giả bịa)

**4/4 phát hiện đúng** (cosine 0.197–0.299, đều dưới ngưỡng 0.40) và **4/4 từ chối lịch sự, không bịa** khi qua khâu sinh. Biên an toàn: câu trong kho thấp nhất 0.479 vs câu ngoài kho cao nhất 0.310.

## 3. Search Stability (4 cặp câu cùng ý, khác diễn đạt)

| Mức đo | Jaccard top-5 | Trùng top-1 |
|---|--:|--:|
| Chunk | 0.384 | 25% |
| **Tác phẩm (người dùng thấy)** | **0.571** | **50%** |

Ghi chú trung thực: hai cách diễn đạt cùng ý vẫn đổ về **cùng tác phẩm** nhiều hơn cùng chunk (chunk khác section của cùng cuốn sách). Đây là điểm hạn chế đã đo được và nêu trong báo cáo, không giấu.

## 4. Generation — kiểu RAGAS, giám khảo Gemini t=0 (16 câu có ground-truth)

| Metric | Giá trị | Ghi chú |
|---|--:|---|
| **Faithfulness** | **0.990** | 15/16 câu đạt 1.00; 1 ca khó: q20 (0.83). (Lần chạy đầu với prompt cũ: 0.955 — prompt CSKH kèm "Thông tin bán" giúp claim bám nguồn tốt hơn) |
| **Answer Relevance** | **1.000** | 16/16 trả lời đúng trọng tâm |
| Context Precision@5 | 0.475 | tính TRỰC TIẾP từ nhãn vàng (mạnh hơn LLM-proxy) |
| Context Recall@5 | 0.852 | như trên |
| Citation valid | 100% | mọi marker [n] ngầm đều trỏ nguồn có thật |
| Fallback refusal | 4/4 | từ chối lịch sự, không bịa |

## 5. Cách đọc số liệu khi bảo vệ
- Đây là **tập đối chứng có nhãn đầy đủ** (controlled benchmark) — KHÔNG phải hiệu năng hệ lớn 11.759 chunk. Giá trị: đo **chuẩn học thuật** (Recall thật, nDCG graded) và **tái lập được**.
- Số không tròn 100% ở Faithfulness/Stability là bằng chứng benchmark trung thực, có ca khó.
- Reproduce: xem README.md cùng thư mục.
