# ĐÁNH GIÁ SAMPLE MODEL THEO PHƯƠNG PHÁP LUẬN BẢO VỆ (3 KHUNG A/B/C + RAG TRIAD)

> Đối chiếu theo đúng hệ quy chiếu đã soạn trong `chuan_bi_bao_ve.md` và `plan bao ve` (mục 1.2).
> Số liệu từ lần chạy **2026-07-20 08:24** — `retrieval_20260720_082400.json`, `generation_20260720_082400.json`.
> Đối tượng đo: **sample model** (`sample_model/` — corpus 163 chunk/51 tác phẩm, nhãn ĐẦY ĐỦ).
> Trạng thái: ✅ = đã làm & đo được · ⚠️ = có làm nhưng chưa đo đủ · ❌ = chưa làm.
> **Nguyên tắc trung thực:** đây là kết quả trên *tập đối chứng có nhãn đầy đủ*, không thay thế số liệu hệ lớn; hai bộ số bổ trợ nhau.

---

## 0. RAG Triad (phương pháp luận lõi — plan bao ve mục 1.2)

| Đỉnh tam giác | Cách đo trên sample model | Kết quả |
|---|---|---|
| **1. Context Relevance** (truy vấn → ngữ cảnh) | P/R/F1/MRR/nDCG graded/MAP/HitRate trên golden set 28 câu có **full relevant set**; Context Precision/Recall@5 tính từ nhãn vàng | Hybrid: MRR **0.964**, HitRate@3 **1.00**, nDCG@5 0.742; CtxRecall@5 **0.852** |
| **2. Groundedness / Faithfulness** (ngữ cảnh → câu trả lời) | Giám khảo Gemini t=0 tách claim, đếm tỉ lệ claim được ngữ cảnh đỡ (16 câu có GT) | **0.990** (15/16 câu = 1.00; 1 ca khó q20 = 0.83) |
| **3. Answer Relevance** (truy vấn → câu trả lời) | Giám khảo Gemini t=0 so với ground-truth answer | **1.000** (16/16) |

→ Sample model là nơi **đầu tiên trong đồ án đo được trọn vẹn cả 3 đỉnh RAG Triad bằng số**, thay vì chỉ 2 đỉnh (hệ lớn đo Context Relevance định lượng + Groundedness thủ công).

---

## 1. Khung A — OMICall (6 tiêu chí vận hành/sản phẩm)

| # | Tiêu chí | Hệ lớn | Sample model | Bằng chứng / còn thiếu |
|---|---|:--:|:--:|---|
| 1 | Tỷ lệ tương tác | ⚠️ | ⚠️➕ | Có thêm cơ chế mới thúc tương tác: **followup chips neo vào tác phẩm trong kho** (luôn trả lời được) sau MỖI câu trả lời + chip khởi đầu + streaming. Vẫn **chưa có analytics/người dùng thật** để ra con số. |
| 2 | Mức độ hài lòng KH | ❌ | ❌ | Chưa có 👍/👎, chưa khảo sát. Giữ nguyên là hướng phát triển. |
| 3 | **Tỷ lệ chuyển đổi** | ❌ | **⚠️ (nâng cấp lớn)** | Từ "định hướng trong báo cáo" → **đã triển khai thật trong UI**: thẻ sách kèm giá tham khảo + nút **Mua trên Tiki** + note tuyển tập; bot trả lời được câu hỏi giá/cách mua (kể cả ca tuyển tập: Chữ người tử tù → mua 'Vang bóng một thời' 76.000đ); ≥1/3 chip gợi ý là câu hướng mua. **Chưa đo được conversion** vì chưa có người dùng thật. |
| 4 | Khả năng tự học | ⚠️ | ⚠️ | Như hệ lớn: cập nhật tri thức bằng thêm chunk + re-index (1 lệnh, ~1 phút), không train lại. Không tự học online. |
| 5 | Thời gian phản hồi | ✅ | ✅ | Typing indicator hiện NGAY (kể cả lúc nạp model) + streaming token đầu 1–2s. Full response vẫn phụ thuộc API Gemini (6–8s) — hạn chế chung. |
| 6 | Khả năng xử lý NLP | ✅ | ✅➕ | MRR 0.964, HitRate@3 100%; hiểu câu cảm xúc/ngữ nghĩa; đại từ đa lượt ("ông ấy" → Nam Cao) đo được Recall 1.0; từ chối đúng 4/4 câu ngoài miền. |

**Kết luận Khung A:** sample model đẩy tiêu chí 3 (chuyển đổi) từ ❌ lên ⚠️ — *Conversational Commerce đã chạy thật trong demo*, chỉ còn thiếu người dùng thật để đo số. Tiêu chí 2 vẫn là ranh giới nghiên cứu/sản phẩm.

---

## 2. Khung B — GeeksforGeeks (taxonomy metric RAG)

### I. Retrieval-level — ✅ đo ĐẦY ĐỦ, và SỬA XONG 2 hạn chế của hệ lớn

| Metric | Hệ lớn (30 câu, nhãn keyword nhị phân) | Sample model (28 câu, graded + full relevant) |
|---|---|---|
| Precision@1 / @5 | 0.83 / — | 0.929 / 0.514 (hybrid) |
| **Recall@K** | ⚠️ *xấp xỉ = Precision* (thiếu tập đúng đầy đủ) | ✅ **Recall THẬT**: R@5 = 0.682, R@10 = 0.799 (mẫu số = full relevant set) |
| F1 | = P (do R=P) | ✅ F1 thật: 0.533@5 |
| MRR | 0.887 | **0.964** |
| Hit Rate | Hit@5 = 1.00 | Hit@3 = **1.00** (sớm hơn 1 bậc K) |
| **nDCG** | ⚠️ nhãn nhị phân | ✅ **nDCG graded 0/1/2** chuẩn học thuật: 0.742@5, 0.776@10 |
| MAP | 0.84@10 | 0.690@10 (chuẩn hóa theo min(R,K) — chặt hơn) |
| So sánh cấu hình | Vector 0.33 « BM25 0.77 « Hybrid 0.83 (P@1) | Vector **0.964** ≥ Hybrid 0.929 » BM25 0.750 (P@1) |

**Phát hiện đáng giá khi bảo vệ:** trên hệ lớn (embedding MiniLM) vector thuần yếu (P@1=0.33) phải nhờ BM25 gánh; trên sample (embedding **bge-m3 tiếng Việt**) vector thuần vươn lên mạnh nhất. → Đây là **bằng chứng thực nghiệm** cho khuyến nghị "nâng cấp embedding tiếng Việt" ở phần hướng phát triển của hệ lớn, đo trên cùng phương pháp luận.

### II. Generation-level

| Metric | Hệ lớn | Sample model |
|---|:--:|---|
| BLEU/ROUGE/BERTScore | ❌ (cố ý — không hợp bài toán mở) | ❌ giữ nguyên lập luận |
| Perplexity | ❌ (API đóng) | ❌ như cũ |
| **Factual Consistency** | ✅ thủ công (Hallucination 0%) | ✅ **tự động hóa bằng giám khảo**: Faithfulness 0.990, tách 91 claim/16 câu, từng claim đối chiếu ngữ cảnh |
| Fluency & Readability | ⚠️ thủ công | ⚠️ vẫn thủ công (quan sát giọng CSKH tự nhiên) — chưa định lượng |
| Diversity & Novelty | ❌ | ❌ |

### III. End-to-end

| Metric | Hệ lớn | Sample model |
|---|:--:|---|
| Answer Relevance | ✅ Pass 93.3% auto / 100% thủ công | ✅ **1.000** (LLM-judge so với GT answer) |
| Context Utilization / Citation | ✅ 100% (marker hiển thị) | ✅ **100%** — marker `[n]` NGẦM (UI ẩn theo yêu cầu UX CSKH) vẫn chấm được |
| Groundedness / Hallucination | ✅ 0% (thủ công) | ✅ Faithfulness 0.990 (tự động) + fallback 4/4 không bịa |
| Response Coherence | ⚠️ thủ công | ⚠️ thủ công |

### IV. Human Evaluation
- Hệ lớn: ✅ expert review nhị phân, 1 người chấm. Sample model: **chưa lặp lại human eval riêng** (⚠️) — thay bằng LLM-judge + GT answers; **cần user nghiệm thu độ chính xác văn học của 163 chunk** (đã ghi trong README).

### V. Emerging Approaches — **3 mục "chưa làm" của hệ lớn đã làm xong trên sample**

| Mục | Hệ lớn | Sample model |
|---|:--:|:--:|
| **RAGAS** (Faithfulness/AnswerRel/Context P-R) | ❌ | ✅ tự viết theo đúng định nghĩa RAGAS (`eval/judge.py`); Context P/R tính từ **nhãn vàng** — chặt hơn bản LLM-proxy gốc |
| **LLM-as-a-judge** | ❌ | ✅ Gemini 2.5 Flash, temperature 0, JSON output, retry |
| Graded relevance cho nDCG | ❌ | ✅ nhãn 0/1/2 toàn bộ golden set |

**Kết luận Khung B:** khâu truy hồi từ "gần đầy đủ" → **đầy đủ và chuẩn học thuật**; khâu sinh từ "chỉ đo thủ công nhóm trung thực" → **tự động hóa bằng LLM-judge**. Còn mở: fluency định lượng, diversity, human eval đa người chấm.

---

## 3. Khung C — Microsoft (Shimin Zhang)

### Nhóm 1: Hiệu năng TÌM KIẾM
| Tiêu chí | Hệ lớn | Sample model |
|---|:--:|---|
| Search Relevance | ✅ | ✅ MRR 0.964 · nDCG graded 0.776@10 · phân tích theo 4 loại câu (FACTUAL R@5=0.963, AUTHOR 0.408*, SEMANTIC 0.445, MULTI_TURN 1.0). *AUTHOR bị trần lý thuyết 13 relevant/K=5 — nêu rõ, không phải lỗi hệ thống. |
| **Search Stability** | ⚠️ chưa đo | ✅ **ĐÃ ĐO** trên 4 cặp paraphrase: Jaccard top-5 mức chunk 0.384, mức tác phẩm (người dùng thấy) **0.571**, trùng sách top-1 50%. Con số khiêm tốn được báo cáo **công khai như hạn chế** — đúng tinh thần benchmark trung thực. |

### Nhóm 2: Chất lượng SINH
| Tiêu chí | Hệ lớn | Sample model |
|---|:--:|---|
| Relevance | ✅ | ✅ 1.000 (judge) |
| Consistency | ✅ thủ công | ✅ Faithfulness 0.990 tự động |
| Coherence / Fluency | ⚠️ | ⚠️ thủ công (giọng CSKH đã duyệt qua demo) |
| Role Adherence (bám vai) | ✅ | ✅ vai "nhân viên thư viện thân thiện" giữ ổn định kể cả khi từ chối (4/4 từ chối đúng mẫu lịch sự + gợi ý hướng khác) |
| **Knowledge Retention** (nhớ đa lượt) | ⚠️ có cơ chế, chưa metric | ✅ **CÓ METRIC RIÊNG**: 4 câu MULTI_TURN chứa đại từ, đi qua rewriter → Recall@5 = **1.000**, MRR = 1.000; judge 4/4 faithfulness ≥ 0.95 |
| Conversation Relevancy | ⚠️ | ✅ gián tiếp qua nhóm MULTI_TURN + demo live ("Ông ấy viết Chí Phèo năm nào?" → đúng 1941) |

### Nhóm 3: Phương pháp đánh giá
| Phương pháp | Hệ lớn | Sample model |
|---|:--:|---|
| Red teaming | ⚠️ cơ bản | ⚠️➕ 4 ca ngoài miền có chủ đích **gồm 1 bẫy tác giả không tồn tại** ("Vầng trăng máu" — Trần Văn Đô) → không bịa. Chưa red-team prompt injection/bảo mật. |
| LLM-as-a-judge | ❌ | ✅ đã dùng làm trụ chính khâu sinh |

**Kết luận Khung C:** 2 tiêu chí "có cơ chế nhưng chưa đo" của hệ lớn (**Search Stability, Knowledge Retention**) đều đã **đo được bằng số** trên sample model; LLM-judge từ ❌ → ✅.

---

## 4. Bảng tổng hợp: sample model lấp những khoảng trống nào của hệ lớn

| Khoảng trống bị flag (trong chuan_bi_bao_ve.md) | Trạng thái trên sample model |
|---|---|
| Recall ≈ Precision (thiếu tập đúng đầy đủ) | ✅ Recall thật (full relevant set) |
| nDCG nhãn nhị phân | ✅ nDCG graded 0/1/2 |
| RAGAS chưa dùng | ✅ 4 metric kiểu RAGAS, judge Gemini t=0 |
| LLM-as-a-judge chưa dùng | ✅ đã dùng (16 câu, 91 claim) |
| Search Stability chưa đo | ✅ đo 4 cặp paraphrase (kết quả khiêm tốn, công khai) |
| Knowledge Retention chưa có metric | ✅ nhóm MULTI_TURN riêng, R@5=1.0 |
| Conversational Commerce mới là "định hướng" | ✅ chạy thật: giá + nút Tiki + note tuyển tập + chip hướng mua + bot tư vấn giá/cách mua |
| Quy mô đánh giá nhỏ, nhãn 1 người | ⚠️ vẫn mở: 32 câu/1 người gán nhãn; cần user nghiệm thu 163 chunk |

## 5. Hạn chế còn lại (nói thẳng khi bảo vệ)
1. **Chưa có người dùng thật** → Khung A tiêu chí 1–3 vẫn không có số vận hành (tương tác, hài lòng, conversion).
2. **Stability mức chunk thấp (0.384)** — paraphrase đổi cách diễn đạt làm xáo trộn thứ hạng section trong cùng tác phẩm; mức tác phẩm 0.571 chấp nhận được cho demo nhưng là hướng cải thiện (đồng nghĩa hóa truy vấn, gộp điểm theo tác phẩm khi rank).
3. **Nhãn và chunk do 1 người soạn/gán** — thiếu inter-annotator agreement; chunk tự soạn cần nghiệm thu chuyên môn văn học.
4. **Fluency/Coherence/Diversity chưa định lượng** — giữ nguyên như hệ lớn.
5. **Giá bán là AI-searched tham khảo** — bot đã tự khai "giá tham khảo, có thể thay đổi"; cần verify tay trước công bố.

## 6. Câu chốt đề xuất cho slide
> "Sample model là tập đối chứng có nhãn đầy đủ: nó đo trọn RAG Triad bằng số (Context Recall 0.85 · Faithfulness 0.99 · Answer Relevance 1.0), sửa xong 2 hạn chế đo lường của hệ lớn (Recall thật, nDCG graded), tự động hóa khâu chấm bằng LLM-judge kiểu RAGAS, và lần đầu đo được Search Stability + Knowledge Retention. Những con số chưa đẹp — stability 0.57, AUTHOR recall 0.41 — được công bố nguyên trạng kèm giải thích, vì giá trị của benchmark nằm ở tính trung thực và tái lập được."
