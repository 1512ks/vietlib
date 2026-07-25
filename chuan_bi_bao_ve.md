# CHUẨN BỊ BẢO VỆ — PHƯƠNG PHÁP LUẬN & TỰ ĐÁNH GIÁ CHATBOT
*(Tự học: bám đúng 2 tài liệu tham chiếu đã dùng — đối chiếu từng tiêu chí xem chatbot làm được gì, thiếu gì)*

**3 khung tham chiếu (phương pháp luận):**
- **Khung A — OMICall:** 6 tiêu chí đánh giá hiệu quả chatbot (góc *vận hành / sản phẩm*).
  <https://omicall.com/tieu-chi-danh-gia-hieu-qua-chatbot/>
- **Khung B — GeeksforGeeks:** Bộ metric đánh giá hệ thống RAG (góc *kỹ thuật*).
  <https://www.geeksforgeeks.org/nlp/evaluation-metrics-for-retrieval-augmented-generation-rag-systems/>
- **Khung C — Microsoft (Shimin Zhang):** Đánh giá chatbot LLM = metric Tìm kiếm + metric Sinh của LLM (góc *sản phẩm doanh nghiệp*).
  <https://medium.com/data-science-at-microsoft/evaluating-llm-based-chatbots-a-comprehensive-guide-to-performance-metrics-9c2388556d3e>

> Số liệu thật lấy từ lần chạy **2026-07-20**:
> Truy hồi → `data/evaluation_results/eval_summary_20260720_030952.json`
> Sinh → `data/chatbot_test_results/chatbot_test_hybrid_20260720_013318.json`
> Chú thích trạng thái: ✅ = đã làm & đo được | ⚠️ = có làm nhưng chưa đo/chưa đủ | ❌ = chưa làm (hướng phát triển)

---

# PHẦN 1 — PHƯƠNG PHÁP LUẬN (theo 2 tài liệu đã gửi)

Đồ án đánh giá chatbot theo **ba khung bổ trợ nhau**:
- **Khung A (OMICall)** nhìn chatbot như một **sản phẩm phục vụ người dùng**: tương tác, hài lòng, chuyển đổi, tự học, tốc độ, khả năng hiểu ngôn ngữ.
- **Khung B (GeeksforGeeks)** nhìn chatbot như một **hệ thống RAG kỹ thuật**: đo riêng khâu Truy hồi, khâu Sinh, và tổng thể End-to-end, cộng đánh giá bởi con người.
- **Khung C (Microsoft)** nhìn chatbot như một **sản phẩm doanh nghiệp thực chiến**: tách 2 nhóm — hiệu năng **Tìm kiếm** (độ liên quan + độ ổn định) và chất lượng **Sinh của LLM** (mạch lạc, trôi chảy, nhất quán, bám vai, nhớ hội thoại), cộng **red teaming** để dò lỗ hổng.

Dùng cả ba để vừa chứng minh **chất lượng kỹ thuật lõi** (Khung B), vừa soi được **những mặt sản phẩm còn thiếu** (Khung A, C) — chính là ranh giới giữa *đồ án nghiên cứu* và *sản phẩm thương mại*.

---

# PHẦN 2 — TỰ ĐÁNH GIÁ: CHATBOT LÀM ĐƯỢC GÌ / THIẾU GÌ

## 2.A — Đối chiếu Khung A (6 tiêu chí OMICall)

| # | Tiêu chí | Trạng thái | Đã làm được | Còn thiếu |
|---|---|:--:|---|---|
| 1 | **Tỷ lệ tương tác** | ⚠️ | Có cơ chế *thúc đẩy* tương tác: nút câu hỏi gợi ý tự sinh sau mỗi trả lời, chip câu hỏi khởi đầu, phản hồi streaming | **Chưa đo được con số thật** — chưa gắn analytics, chưa có lưu lượng người dùng thật |
| 2 | **Mức độ hài lòng KH** | ❌ | Gián tiếp tạo hài lòng qua trích dẫn nguồn để người dùng tự kiểm chứng | **Chưa có nút 👍/👎, chưa chạy khảo sát 1–5 sao** |
| 3 | **Tỷ lệ chuyển đổi** | ❌ | Mới ở mức **định hướng**: đã thiết kế schema siêu dữ liệu thương mại, đề xuất tích hợp Tiki/Fahasa trong báo cáo | **Chưa triển khai thật, chưa đo** — bản chất là công cụ tra cứu, không phải bán hàng |
| 4 | **Khả năng tự học** | ⚠️ | Kiến trúc RAG cho phép **cập nhật tri thức bằng cách thêm tài liệu, không cần train lại**; có cache nhiều tầng; có viết lại câu hỏi | **Không có tự học online / không tự tái huấn luyện / không có vòng phản hồi tự cải thiện** |
| 5 | **Thời gian phản hồi** | ✅ | **Đo được:** truy hồi ~554ms; nhờ streaming, token đầu chỉ **1–2s** → đạt mục tiêu cảm nhận < 2s | Full response vẫn **6–8s** do phụ thuộc API Gemini (hạn chế) |
| 6 | **Khả năng xử lý NLP** | ✅ | **Mạnh nhất:** P@1=0.83, MRR=0.89, nDCG@10=0.90; hiểu câu ngữ nghĩa/cảm xúc; xử lý hỏi nối tiếp đa lượt; từ chối đúng câu ngoài miền | Embedding tiếng Việt còn yếu (vector 0.33) → phụ thuộc BM25; câu cảm xúc mơ hồ đôi lúc từ chối nhầm |

**Kết luận Khung A:** Chatbot **mạnh ở 2 tiêu chí kỹ thuật (5, 6)**; **4 tiêu chí vận hành–kinh doanh (1, 2, 3, 4) chưa đo/chưa triển khai** vì đây là **nguyên mẫu nghiên cứu**, chưa có người dùng thật. Đây chính là hướng phát triển thành sản phẩm.

## 2.B — Đối chiếu Khung B (taxonomy metric RAG của GeeksforGeeks)

### I. Retrieval-level (khâu Truy hồi) — **đo gần như đầy đủ** ✅
| Metric trong bài | Trạng thái | Số liệu thật (Hybrid+Rerank) |
|---|:--:|---|
| Precision@K | ✅ | P@1 = 0.83 |
| Recall@K | ✅ | = Precision (xấp xỉ — xem "còn thiếu") |
| F1-Score | ✅ | = Precision (do Recall = Precision) |
| Hit Rate | ✅ | Hit@5 = **1.00** |
| MRR | ✅ | **0.89** |
| MAP | ✅ | MAP@10 = 0.84 *(mới bổ sung)* |
| nDCG | ✅ | nDCG@10 = **0.90** *(mới bổ sung)* |
| Similarity (Cosine, BM25) | ✅ | Là *cơ chế* truy hồi (Bi-Encoder cosine + BM25 + RRF) |

**Còn thiếu ở khâu truy hồi:** nhãn liên quan mới ở mức **nhị phân**, chưa có **mức độ liên quan phân cấp (graded relevance)** để nDCG chuẩn xác hơn; **Recall thật** chưa tính được vì chưa có toàn bộ tập tài liệu đúng của corpus.

### II. Generation-level (khâu Sinh) — **chỉ đo nhóm liên quan trung thực**
| Metric trong bài | Trạng thái | Ghi chú |
|---|:--:|---|
| BLEU / ROUGE / METEOR / BERTScore | ❌ | **Cố ý không dùng** — là metric so khớp *đáp án mẫu*, không hợp bài toán sinh câu trả lời mở tiếng Việt (không có đáp án vàng) |
| Perplexity | ❌ | Không lấy được — Gemini là API đóng, không truy cập logprob |
| Factual Consistency | ✅ | Đo qua thủ công → **Hallucination 0%** |
| Fluency & Readability | ⚠️ | Chỉ đánh giá **thủ công**, chưa tính điểm định lượng (Flesch, distinct-n) |
| Diversity & Novelty | ❌ | Chưa đo |

### III. End-to-end — **đo được nhóm cốt lõi chống ảo tưởng** ✅
| Metric trong bài | Trạng thái | Số liệu |
|---|:--:|---|
| Answer Relevance | ✅ | Pass Rate 93.3% (auto) / 100% (thủ công) |
| Context Utilization | ✅ | Trích dẫn nguồn → Citation Accuracy 100% |
| Groundedness | ✅ | Hallucination 0% |
| Hallucination Rate | ✅ | **0% (0/15)** |
| Response Coherence | ⚠️ | Đánh giá thủ công, chưa định lượng |
| Relevancy Score | ✅ | Gián tiếp qua pass rate |

### IV. Human Evaluation — **có, nhưng quy mô nhỏ**
- ✅ **Expert Review** với thang đạt/không-đạt trên 4 tiêu chí (Relevance, Informativeness, Factual Accuracy, Clarity).
- ⚠️ Mới dùng thang **nhị phân**, chưa dùng thang 1–5.
- ❌ Chưa có **Pairwise Comparison**; **chỉ 1 người chấm** → chưa tính được độ đồng thuận (inter-annotator agreement).

### V. Emerging Approaches & Tools — **chưa dùng (hướng phát triển)**
- ❌ **RAGAS** (framework chuẩn tự động đo Faithfulness / Answer Relevance / Context Precision).
- ❌ **LLM-as-a-judge** để tự động hóa chấm khâu sinh ở quy mô lớn.
- ❌ Chưa dùng thư viện NLTK / ROUGE-score / BERTScore / Textstat.

**Kết luận Khung B:** Khâu **Truy hồi đo gần đầy đủ và mạnh**; khâu **Sinh chỉ đo nhóm trung thực/dẫn nguồn** (đúng mục tiêu chống ảo tưởng), **bỏ nhóm reference-based và fluency định lượng**; **thiếu RAGAS & LLM-judge** — là 3 hướng hoàn thiện rõ ràng nhất.

## 2.C — Đối chiếu Khung C (Microsoft — Shimin Zhang)

### Nhóm 1: Hiệu năng TÌM KIẾM
| Tiêu chí | Trạng thái | Đã làm được | Còn thiếu |
|---|:--:|---|---|
| **Search Relevance** (độ liên quan truy hồi) | ✅ | Đo đầy đủ bằng Precision@K, MRR, nDCG, MAP → P@1=0.83, nDCG@10=0.90 | — |
| **Search Stability** (cùng ý, diễn đạt khác → kết quả có ổn định không) | ⚠️ | Có **viết lại câu hỏi (query rewriting)** giúp chuẩn hóa cách diễn đạt; có phân tích theo nhóm câu (Factual/Author/Semantic) | **Chưa đo định lượng độ ổn định** — chưa test 1 câu hỏi với nhiều cách diễn đạt để so kết quả |

### Nhóm 2: Chất lượng SINH của LLM
| Tiêu chí | Trạng thái | Đã làm được | Còn thiếu |
|---|:--:|---|---|
| **Relevance** (đúng trọng tâm) | ✅ | Pass Rate 93.3% (auto) / 100% (thủ công) | — |
| **Consistency** (không tự mâu thuẫn) | ✅ | Nhờ prompt ràng buộc + chỉ bám ngữ cảnh → Hallucination 0% | Chưa đo tự động |
| **Coherence** (mạch lạc) | ⚠️ | Câu trả lời có cấu trúc, mạch lạc (đánh giá thủ công) | Chưa tính điểm định lượng |
| **Fluency** (trôi chảy) | ⚠️ | Gemini viết tiếng Việt tự nhiên (quan sát thủ công) | Chưa đo bằng chỉ số (Flesch...) |
| **Role Adherence** (bám vai "trợ lý thư viện") | ✅ | Có system prompt định vai; giữ vai kể cả khi từ chối câu ngoài miền | Chưa đo tự động |
| **Knowledge Retention** (nhớ hội thoại đa lượt) | ⚠️ | **Có cơ chế**: bộ nhớ hội thoại + tóm tắt lịch sử + viết lại câu ("tác giả đó" → "Kim Lân"); qua 14/15 ca đa lượt | **Chưa có metric riêng** đo khả năng nhớ |
| **Conversation Relevancy / Completeness** | ⚠️ | Xử lý tốt câu nối tiếp, trả lời đủ ý (thủ công) | Chưa định lượng riêng |

### Nhóm 3: Phương pháp đánh giá
| Phương pháp | Trạng thái | Ghi chú |
|---|:--:|---|
| **Red teaming** (prompt tấn công dò lỗ hổng) | ⚠️ | **Có một phần**: các ca Hard (Naruto, One Piece, giá vàng, cách nấu ăn) là kiểu adversarial để thử chống ảo tưởng/fallback | Chưa dùng bộ chuẩn (RedEval), chưa red-team về prompt injection / bảo mật |
| **LLM-as-a-judge** | ❌ | Chưa dùng — hướng phát triển |

**Kết luận Khung C:** **Search Relevance** và nhóm **Relevance/Consistency/Role Adherence** ở khâu sinh là **điểm mạnh có bằng chứng**; **Search Stability, Knowledge Retention, Coherence/Fluency** thì **có cơ chế nhưng chưa đo định lượng**; **LLM-as-a-judge chưa làm**, **red teaming mới ở mức cơ bản**. → Trùng khớp với kết luận 2 khung kia: mạnh phần lõi, thiếu phần đo lường tự động & vận hành.

---

# PHẦN 3 — Ý NGHĨA TỪNG METRIC (giải thích dễ hiểu + số liệu + file code)

**File tính metric truy hồi:** `search/evaluator.py` · **Chạy:** `evaluate_search.py` · **Câu hỏi:** `search/test_queries.py`

- **Precision@K** — *Trong K kết quả đầu, bao nhiêu phần đúng?* Trả 5 cái, 4 đúng → 0.8. → **P@1 = 0.83**. (biến `precision`)
- **Recall@K** — *Trong tất cả tài liệu đúng, lấy về được bao nhiêu?* Vì chưa có tập đúng đầy đủ nên **xấp xỉ = Precision** (hạn chế). (biến `recall`)
- **F1@K** — *Trung bình điều hòa P và R*, phạt nếu 1 trong 2 thấp. Ở đồ án **= Precision** (do R=P). (biến `f1`)
- **MRR** — *Tài liệu đúng đầu tiên nằm vị trí mấy?* Vị trí 1→1.0, vị trí 2→0.5... **Quan trọng nhất với RAG** vì LLM chỉ đọc vài cái đầu. → **0.887**. (biến `mrr`)
- **Hit Rate@K** — *Trong K cái đầu có ít nhất 1 cái đúng không?* → **Hit@5 = 100%** (tới top-5 luôn có tài liệu đúng). (biến `hit`)
- **nDCG@K** — *Precision có thưởng vị trí*: đúng mà nằm cao thì điểm cao, nằm thấp bị chiết khấu, rồi chuẩn hóa về [0,1]. Metric **nhạy thứ hạng**. → **nDCG@10 = 0.90** (cao nhất). (hàm `_ndcg_at_k`)
- **MAP@K** — *Mỗi lần gặp tài liệu đúng ghi lại Precision tại đó rồi lấy trung bình*; phản ánh chất lượng sắp xếp tổng thể. → **MAP@10 = 0.84** (cao nhất). (hàm `_ap_at_k`)

**File tính metric sinh:** `test_chatbot.py` (hàm `has_citation`, `is_fallback`, `run_tests`)

- **Pass Rate** — *Bao nhiêu kịch bản đạt / tổng.* → **93.3% auto / 100% thủ công**. Chênh 1 ca cảm xúc mơ hồ bị máy tính trượt vì từ chối lịch sự (không bịa).
- **Citation Accuracy** — *Thẻ nguồn [1][2] có trỏ đúng tài liệu không?* → **100%**.
- **Hallucination Rate** — *Bao nhiêu câu bịa thông tin ngoài ngữ cảnh?* → **0%**.
- **Fallback đúng** — *Câu ngoài kho có biết nói "không tìm thấy" không?* → Đạt (Naruto, One Piece). Triết lý *"thà từ chối còn hơn trả lời sai"*.
- **Response Time** — truy hồi ~554ms; token đầu 1–2s; full 6–8s.

### 📊 Bảng so sánh 4 cấu hình (bảo vệ lựa chọn Hybrid)
| Cấu hình | P@1 | MRR | nDCG@10 | MAP@10 | Hit@5 |
|---|---|---|---|---|---|
| Vector | 0.33 | 0.45 | 0.52 | 0.42 | 0.63 |
| BM25 | 0.77 | 0.86 | 0.89 | 0.82 | 1.00 |
| **Hybrid + Rerank** | **0.83** | **0.89** | **0.90** | **0.84** | **1.00** |

*Câu chốt:* "Hybrid thắng/hòa trên mọi metric, đặc biệt cao nhất ở nDCG@10 và MAP@10 (nhạy thứ hạng). Vector yếu do embedding đa ngữ chưa tối ưu tiếng Việt → BM25 gánh tên riêng, hai thành phần bù trừ nhau."

---

# PHẦN 4 — CHẠY LẠI ĐỂ DEMO + BẢN ĐỒ CODE

```powershell
.venv\Scripts\Activate.ps1
python evaluate_search.py --mode all     # 7 metric truy hồi, 4 cấu hình
python test_chatbot.py --save            # 15 kịch bản khâu sinh
```

| Nội dung | File |
|---|---|
| Định nghĩa & tính 7 metric truy hồi | `search/evaluator.py` |
| Hàm nDCG, MAP | `search/evaluator.py` → `_ndcg_at_k()`, `_ap_at_k()` |
| Chạy đánh giá truy hồi 4 cấu hình | `evaluate_search.py` |
| 30 câu golden có nhãn | `search/test_queries.py` |
| 15 kịch bản test chatbot + tiêu chí chấm | `test_chatbot.py` |
| Pipeline tìm kiếm (BM25+Vector+RRF+Rerank) | `search/search_pipeline.py` |
| Lớp sinh câu trả lời (Gemini) | `retrieval_qa.py` |
