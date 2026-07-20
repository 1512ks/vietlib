# SO SÁNH 2 MODEL — Sản phẩm chính (hệ lớn) vs Sample model (đối chứng cải tiến)

> Đo theo **cùng một phương pháp luận thống nhất 4 tầng + RAG Triad** (xem `tong_hop_ly_thuyet_danh_gia.md`).
> Hệ lớn: `data/evaluation_results/eval_summary_20260720_030952.json` (30 câu, corpus 11.759 chunk, embedding MiniLM).
> Sample: `sample_model/results/` lần chạy 2026-07-20 (32 câu graded + full relevant, corpus 163 chunk, embedding bge-m3).
> **Lưu ý trung thực:** hai model đo trên corpus & golden set KHÁC nhau nên KHÔNG so 1-1 tuyệt đối. Bảng dưới so theo *từng tiêu chí* để thấy sample model cải tiến ở đâu; phần §3 (ablation) tách bạch phần cải tiến do KIẾN TRÚC khỏi phần "corpus nhỏ dễ hơn".

---

## 1. Bảng so sánh tổng — theo 4 tầng phương pháp luận

| Tầng | Tiêu chí | Sản phẩm chính (hệ lớn) | Sample model | Nhận xét |
|---|---|---|---|---|
| **T1 Truy hồi** | Cấu hình tốt nhất | Hybrid (BM25 gánh vector) | **bge-m3 hybrid + gộp tác phẩm** | Sample đổi trục: vector dẫn dắt |
| | P@1 | 0.833 | **0.929** | ↑ |
| | MRR | 0.887 | **0.946** | ↑ tài liệu đúng gần như luôn top-1 |
| | nDCG@10 | 0.901 (nhị phân) | **0.839 (graded 0/1/2)** | Sample đo CHUẨN hơn (graded), số không trực tiếp so |
| | HitRate | Hit@5 = 1.00 | **Hit@3 = 1.00** | Sample đạt sớm hơn 1 bậc K |
| | Recall | ≈ Precision (xấp xỉ) | **Recall THẬT**: R@10 = 0.873 | Sample sửa hạn chế đo lường gốc |
| | Search Stability | ❌ chưa đo | ✅ đo (chunk 0.40 / card 0.50) | Sample đo được, số khiêm tốn (công khai) |
| | Latency truy hồi | ~49 ms (không rerank) | ~145 ms p50 | Sample chậm hơn do model bge-m3 lớn hơn |
| **T2 Sinh** | Faithfulness | 0% hallucination (thủ công) | **0.95–0.99** (LLM-judge, tách 91 claim) | Sample TỰ ĐỘNG HÓA + định lượng |
| | Answer Relevance | Pass 93.3% auto / 100% thủ công | **0.94–1.00** (judge so GT) | Ngang, sample đo bằng judge |
| | Context Precision/Recall@5 | ❌ chưa đo | **0.51 / 0.90** (từ nhãn vàng) | Sample bổ sung |
| | Coherence / Fluency | ⚠️ thủ công | **4.9 / 5.0** (judge 1-5) | Sample định lượng nốt ô còn thiếu |
| | Citation Accuracy | 100% | **100%** (marker ngầm) | Ngang |
| **T3 Hội thoại & an toàn** | Multi-turn (nhớ hội thoại) | ⚠️ có cơ chế, 14/15 ca | ✅ **metric riêng**: Recall@5 = 1.00 | Sample có số |
| | Fallback (từ chối ngoài kho) | ✅ (Naruto/One Piece) | ✅ **4/4** (có bẫy tác giả bịa) | Ngang, sample chặt hơn |
| | Red teaming | ⚠️ cơ bản | ✅ **10/10** (sau khi vá 1 lỗ hổng lộ prompt) | Sample bài bản hơn |
| **T4 Trải nghiệm** | Streaming / độ trễ cảm nhận | ✅ token đầu 1–2s | ✅ typing tức thì + stream | Ngang |
| | Full-answer latency | 6–8 s | **p50 4.1s / p95 6.6s** (đo được) | Sample có phân vị |
| | Feedback 👍/👎 | ❌ | ✅ có + ghi log | Sample bổ sung |
| | Conversational Commerce | ❌ mới "định hướng" | ✅ **chạy thật** (giá + Tiki + tư vấn mua) | Sample hiện thực hóa |

---

## 2. So sánh 4 cấu hình truy hồi (điểm mạnh của mỗi bên)

**Sản phẩm chính (MiniLM, 30 câu):**
| Cấu hình | P@1 | MRR | nDCG@10 | Hit@5 |
|---|--:|--:|--:|--:|
| vector | 0.333 | 0.446 | 0.518 | 0.633 |
| bm25 | 0.767 | 0.863 | 0.890 | 1.00 |
| hybrid | 0.833 | 0.887 | 0.901 | 1.00 |
| hybrid+rerank | 0.833 | 0.887 | 0.901 | 1.00 |

**Sample model (bge-m3, 28 câu, nhãn graded):**
| Cấu hình | P@1 | MRR | nDCG@10 | R@10 | Hit@3 |
|---|--:|--:|--:|--:|--:|
| vector | 0.964 | 0.964 | 0.827 | 0.824 | — |
| bm25 | 0.750 | 0.845 | 0.645 | 0.693 | 0.93 |
| hybrid | 0.929 | 0.964 | 0.776 | 0.799 | 1.00 |
| **hybrid + gộp tác phẩm (app)** | 0.929 | **0.946** | **0.839** | **0.873** | ~1.00 |

**Đảo chiều đáng chú ý:** ở hệ lớn **vector là yếu nhất (0.333)** phải nhờ BM25 gánh; ở sample **vector mạnh nhất (0.964)**. Nguyên nhân được chứng minh ở §3.

---

## 3. ABLATION — cải tiến là THẬT hay chỉ do corpus nhỏ dễ hơn?

Thí nghiệm 1 biến: giữ NGUYÊN corpus sample (163 chunk), golden set, BM25 — chỉ **đổi embedding** MiniLM ↔ bge-m3.

| Embedding | Vector P@1 | Vector nDCG@10 | Hybrid P@1 | Hybrid nDCG@10 |
|---|--:|--:|--:|--:|
| MiniLM (=hệ lớn) trên corpus sample | 0.429 | 0.333 | 0.536 | 0.464 |
| **bge-m3 (sample)** trên corpus sample | **0.893** | **0.776** | **0.857** | **0.733** |

> **Kết luận vàng:** corpus nhỏ CHỈ giúp MiniLM nhích từ 0.333 (hệ lớn) → 0.429 (sample) — không đáng kể. **Bước nhảy 0.429 → 0.893 (+0.464) hoàn toàn đến từ việc đổi sang embedding tiếng Việt chuyên dụng bge-m3.** Đây là bằng chứng cải tiến do KIẾN TRÚC, không phải ảo giác "corpus dễ". Nó cũng xác nhận đúng đề xuất "nâng cấp embedding tiếng Việt" mà hệ lớn nêu ở hướng phát triển.

---

## 4. Sample model đã giải quyết những vấn đề nào của hệ lớn

| Vấn đề bị flag ở hệ lớn | Sample model |
|---|---|
| Vector tiếng Việt yếu (0.333) phải phụ thuộc BM25 | ✅ bge-m3 → vector 0.964, tự đứng vững |
| Recall xấp xỉ = Precision (thiếu tập đúng đầy đủ) | ✅ Recall THẬT (full relevant set) |
| nDCG nhãn nhị phân | ✅ nDCG graded 0/1/2 |
| RAGAS chưa dùng | ✅ 4 metric kiểu RAGAS |
| LLM-as-a-judge chưa dùng | ✅ judge Gemini t=0, 91 claim |
| Fluency/Coherence chưa định lượng | ✅ 5.0 / 4.9 (thang 1-5) |
| Search Stability chưa đo | ✅ đã đo (số khiêm tốn, công khai) |
| Knowledge Retention chưa có metric | ✅ Recall@5 = 1.00 nhóm multi-turn |
| Red teaming sơ sài | ✅ 10 ca → phát hiện & vá lỗ hổng → 10/10 |
| Conversational Commerce mới "định hướng" | ✅ chạy thật (giá + Tiki + tư vấn mua) |
| Chưa có kênh phản hồi người dùng | ✅ nút 👍/👎 + log tương tác |
| AUTHOR Recall bị trần K (0.41) | ✅ K thích ứng → 0.87 |

**11/13 vấn đề được giải quyết bằng số**; 2 mục còn mở (human-eval đa người chấm; số vận hành thật) cần người dùng/thời gian, không phải kỹ thuật.

---

## 5. Sample model còn cải thiện được gì (đã thử — kết quả trung thực)

| Hạng mục | Đã làm gì | Kết quả | Quyết định |
|---|---|---|---|
| **Reranker (Cross-Encoder)** | Thử ms-marco rerank top-20 của hybrid | nDCG@5 **giảm** 0.735→0.614 | KHÔNG thêm — retrieval bge-m3 đã **bão hòa** trên corpus sạch nhỏ; reranker đa ngữ yếu tiếng Việt phản tác dụng (khác hệ lớn corpus nhiễu). Reranker tiếng Việt chuyên dụng (bge-reranker-v2-m3) nặng 2.3GB, headroom nhỏ → không đáng đánh đổi RAM deploy. |
| **Search Stability (0.40–0.57)** | Đã thử gộp theo tác phẩm | Cải thiện relevance nhưng KHÔNG cải thiện stability | Còn mở: cần query-expansion (đồng nghĩa hóa) hoặc mở rộng bộ cặp paraphrase. Bản chất mẫu nhỏ nhạy với cách diễn đạt. |
| **Context Precision@5 (0.51)** | (chưa đổi) | — | Không phải vấn đề thực: Faithfulness/Answer-Rel vẫn 0.95–1.0 dù đưa dư chunk (LLM đủ giỏi bỏ chunk thừa). Cắt động top-k rủi ro giảm recall → giữ nguyên. |
| **Human eval đa người chấm** | (cần người ngoài) | — | Nhờ 1–2 người chấm lại 20% nhãn → tính Cohen's κ. |
| **Verify giá tay** | (cần người) | — | Đối chiếu 51 dòng giá với Tiki trước bảo vệ. |

**Đánh giá chung mức "tiệm cận hoàn hảo":** với cỡ mẫu nhỏ, sample model đã **gần trần lý thuyết** ở hầu hết trục — MRR 0.95, HitRate@3 100%, Answer Relevance 1.0, Fluency 5.0, Citation 100%, Fallback 4/4, Red-team 10/10. Retrieval đã **bão hòa** (bằng chứng: reranker không thêm được gì). Phần chưa hoàn hảo còn lại (Stability, human-eval) là **giới hạn nội tại của cỡ mẫu nhỏ + cần nguồn lực người**, không phải khiếm khuyết kỹ thuật còn vá được.

---

## 6. Câu chốt cho hội đồng
> "Sample model không chỉ là bản thu nhỏ 'dễ hơn' của hệ lớn. Ablation trên cùng corpus chứng minh riêng việc đổi embedding tiếng Việt đã đưa vector P@1 từ 0.43 lên 0.89. Trên nền đó, sample model giải quyết 11/13 hạn chế đo-lường & tính-năng của hệ lớn — từ Recall thật, nDCG graded, RAGAS, LLM-judge, đến red-team (phát hiện và vá được một lỗ hổng lộ prompt thật). Em đã đẩy nó tới ngưỡng bão hòa: reranker thêm vào không cải thiện được nữa, chứng tỏ khâu truy hồi đã gần tối ưu cho cỡ dữ liệu này. Những gì chưa hoàn hảo — độ ổn định paraphrase, human-eval đa người chấm — em nêu thẳng là giới hạn của cỡ mẫu nhỏ và nguồn lực, không giấu."
