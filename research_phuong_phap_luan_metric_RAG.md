# Phương pháp luận & Metric đánh giá Chatbot RAG — Báo cáo tổng hợp

> **Ghi chú về độ tin cậy:** Báo cáo này tổng hợp từ **13 nguồn primary** (arXiv / ACM / ACL) do
> pipeline deep-research thu thập được. Bước kiểm chứng phản biện tự động (3 phiếu/claim) **chưa chạy
> được** do gặp session limit — vì vậy các con số cụ thể trích từ nguồn (vd điểm benchmark) nên được
> **đối chiếu lại với paper gốc** trước khi đưa vào luận văn. Định nghĩa metric và công thức là kiến
> thức chuẩn IR/NLP, đã được đối chiếu độc lập. Mỗi khẳng định đều ghi nguồn để bạn truy vết.

---

## 1. Khung phương pháp luận chuẩn để đánh giá chatbot RAG

Đánh giá RAG hiện được chia làm **2 trục tách biệt** (điểm mấu chốt phải nêu trong luận văn):

- **Retrieval** (truy xuất): chất lượng các chunk lấy về — đo bằng metric IR cổ điển.
- **Generation** (sinh): chất lượng câu trả lời cuối — đo bằng faithfulness, answer relevance...

Không được gộp hai trục: một câu trả lời sai có thể do retrieval trượt (lấy nhầm context) **hoặc** do
generation bịa (context đúng nhưng LLM không bám). Tách trục giúp chẩn đoán lỗi ở đâu.

### Các framework đánh giá (reference-free, dùng LLM-as-a-judge)

| Framework | Bản chất | 3 trục cốt lõi | Phù hợp hệ nhỏ? |
|---|---|---|---|
| **RAGAS** (Es et al., 2023, [arXiv:2309.15217](https://arxiv.org/abs/2309.15217)) | Đánh giá **không cần ground-truth answer** | faithfulness, answer relevance, context relevance/precision/recall | ✅ Chuẩn de-facto cho luận văn; cần LLM API |
| **ARES** (Saad-Falcon et al., NAACL 2024, [arXiv:2311.09476](https://arxiv.org/abs/2311.09476)) | Huấn luyện **LLM judge riêng** + PPI (prediction-powered inference) | context relevance, answer faithfulness, answer relevance | ⚠️ Cần dữ liệu train judge + human-annotation nhỏ → nặng hơn |
| **TruLens — RAG Triad** (TruEra/Snowflake) | Bộ 3 "feedback function" nhẹ | context relevance, groundedness, answer relevance | ✅ Nhẹ nhất, dễ cắm; tốt để minh hoạ |
| **DeepEval** (Confident AI) | Thư viện test kiểu pytest cho LLM | G-Eval, faithfulness, các metric RAGAS | ✅ Tốt nếu muốn viết test tự động |
| **Arize Phoenix / Galileo** | Observability + eval production | tương tự | ➖ Thiên về vận hành, hơi thừa cho ĐATN |

### Các benchmark học thuật (để trích dẫn, không nhất thiết chạy)

- **BEIR** (Thakur et al., 2021, [arXiv:2104.08663](https://arxiv.org/abs/2104.08663)) — benchmark zero-shot retrieval, chuẩn so sánh BM25 vs dense.
- **KILT** (Petroni et al., 2021) — knowledge-intensive tasks.
- **RGB** (Chen et al., AAAI 2024) — đo robustness của RAG: noise, negative rejection, information integration, counterfactual.
- **RAGBench** ([arXiv:2407.11005](https://arxiv.org/abs/2407.11005)) — 100k ví dụ, khung TRACe.

> **Khuyến nghị cho hệ của bạn (<200 chunk, ít ngân sách API):** dùng **RAGAS** làm framework chính
> (đã là chuẩn được hội đồng công nhận) + **TruLens RAG Triad** để minh hoạ trực quan. Tránh ARES
> (cần train judge). Nếu lo chi phí API: chạy RAGAS trên **subset** (vd 30 câu) chứ không cần toàn corpus.

---

## 2. Metric Retrieval — công thức, ví dụ, khi nào dùng

Ký hiệu: `K` = số kết quả top đầu xét; `rel_i ∈ {0,1}` = tài liệu ở hạng `i` có liên quan không;
`R` = tổng số tài liệu liên quan trong corpus.

### 2.1 Precision@K
```
Precision@K = (số tài liệu relevant trong top-K) / K
```
**Ví dụ:** top-5 có 3 tài liệu đúng → P@5 = 3/5 = 0.60.
**Dùng khi:** quan tâm "trong những gì lấy về, bao nhiêu là đúng". **Không phản ánh** đã bỏ sót bao nhiêu.

### 2.2 Recall@K
```
Recall@K = (số tài liệu relevant trong top-K) / R
```
**Ví dụ:** có R=4 tài liệu đúng, top-5 lấy được 3 → Recall@5 = 3/4 = 0.75.
**⚠️ Điểm yếu chí mạng của hệ bạn:** vì `R` không biết đầy đủ (chỉ gán 1–2 tài liệu/truy vấn bằng
keyword), bạn đang xấp xỉ `Recall@K = Precision@K`. **Đây là hạn chế phải nêu rõ** (xem §2.5).

### 2.3 F1@K
```
F1@K = 2 · P@K · R@K / (P@K + R@K)
```
Trung bình điều hoà. Khi bạn đặt R@K = P@K thì F1@K = P@K → **F1 hiện tại không thêm thông tin gì**.

### 2.4 MRR — Mean Reciprocal Rank
```
MRR = (1/|Q|) · Σ_q  1 / rank_q(tài liệu relevant đầu tiên)
```
**Ví dụ:** 3 truy vấn, tài liệu đúng đầu tiên nằm ở hạng 1, 3, 2 → MRR = (1/1 + 1/3 + 1/2)/3 ≈ 0.61.
**Dùng khi:** chỉ cần 1 câu trả lời đúng ở càng cao càng tốt (rất hợp chatbot tư vấn — user đọc top đầu).

### 2.5 nDCG@K — Normalized Discounted Cumulative Gain
```
DCG@K = Σ_{i=1..K} (2^rel_i − 1) / log2(i + 1)
nDCG@K = DCG@K / IDCG@K     (IDCG = DCG của thứ tự lý tưởng)
```
**Ví dụ:** rel = [1,0,1] → DCG = 1/log2(2) + 0 + 1/log2(4) = 1 + 0.5 = 1.5; IDCG (thứ tự [1,1,0]) =
1 + 1/log2(3) ≈ 1.63 → nDCG ≈ 0.92.
**Dùng khi:** có mức độ liên quan (graded) và quan tâm thứ hạng. **Metric mạnh nhất, nên báo cáo chính.**

### 2.6 MAP — Mean Average Precision
```
AP@K = (Σ_{i: rel_i=1} P@i) / R ;   MAP = trung bình AP trên mọi truy vấn
```
**Ví dụ:** relevant ở hạng 1 và 3, R=2 → AP = (P@1 + P@3)/2 = (1/1 + 2/3)/2 ≈ 0.83.

### 2.7 Hit Rate@K (Acc@K)
```
Hit@K = 1 nếu có ít nhất 1 relevant trong top-K, ngược lại 0 ; rồi lấy trung bình
```
Metric "dễ dãi" nhất, thường bão hoà = 1.0 ở K=5 (đúng như eval của bạn).

### 2.8 ⭐ Vấn đề ground-truth không đầy đủ — cách khắc phục chuẩn IR

Đây là phần **quan trọng nhất** để bảo vệ phương pháp luận của bạn:

- **Pooling bias** (Buckley & Voorhees, SIGIR 2007, [ACM 1277741.1277755](https://dl.acm.org/doi/10.1145/1277741.1277755)):
  khi qrels không đầy đủ, metric như Recall@K/MAP **thiên vị hệ đã đóng góp vào pool** và **phạt oan**
  hệ lấy được tài liệu đúng-nhưng-chưa-được-gán. Với bạn: pipeline **vector/rerank có thể bị chấm thấp
  oan** vì lấy chunk đúng mà keyword ground-truth chưa đánh dấu.
- **bpref** (Buckley & Voorhees, SIGIR 2004, [ACM 1008992.1009000](https://dl.acm.org/doi/10.1145/1008992.1009000)):
  metric thiết kế riêng cho qrels không đầy đủ, chỉ tính trên tài liệu **đã được phán xét**, phân biệt
  "đã xét là không liên quan" với "chưa xét". Theo nguồn: xếp hạng hệ thống theo bpref giữ ổn định
  (Kendall τ > 0.9) ngay cả khi giảm qrels xuống 25–50%, trong khi MAP/P@10/R-precision suy giảm nhanh hơn.
- **Cách làm tối thiểu khả thi cho ĐATN:** thay vì kéo bpref, hãy (a) **báo cáo Precision@K và nDCG@K
  là metric chính** (ít phụ thuộc R hơn Recall), (b) **thừa nhận rõ** Recall@K chỉ là xấp xỉ, (c) nếu
  có thời gian: mở rộng ground-truth bằng **pooling thủ công** — gộp top-K của cả 4 pipeline, đọc và
  gán nhãn tay tập gộp đó → có qrels đầy đủ hơn nhiều mà chỉ tốn vài giờ với 30 truy vấn.

### 2.9 Nên báo K nào & có cần kiểm định thống kê?

- **Báo K = {1, 3, 5, 10}** (bạn đang làm đúng). Nhấn mạnh **K nhỏ (1,3)** vì chatbot chỉ hiển thị vài kết quả.
- **Kiểm định thống kê khi so 4 pipeline trên 30 truy vấn:** nên có. Theo Urbano et al.
  ([arXiv:1905.11096](https://arxiv.org/pdf/1905.11096)) và Smucker et al. (CIKM 2007,
  [ACM 1321440.1321528](https://dl.acm.org/doi/10.1145/1321440.1321528)): **paired t-test** và
  **permutation/randomization test** cho kết quả gần tương đương và ổn định ngay ở cỡ mẫu ~25–50 truy vấn;
  các nguồn này **khuyến cáo tránh Wilcoxon signed-rank & sign test** (dễ phát hiện sai). → **Dùng
  paired t-test** (hoặc permutation test) khi so từng cặp pipeline; báo p-value và đánh dấu khác biệt
  có ý nghĩa. *(Lưu ý: đây là khuyến nghị đi ngược thói quen "mặc định Wilcoxon" — nên trích dẫn cẩn thận.)*

---

## 3. Metric Generation / End-to-End

### 3.1 Định nghĩa (theo khung RAGAS / TruLens)

| Metric | Đo cái gì | Công thức khái niệm |
|---|---|---|
| **Faithfulness / Groundedness** | Câu trả lời có bám vào context lấy về không (không bịa) | (số câu/claim được context hỗ trợ) / (tổng claim trong câu trả lời) |
| **Answer Relevance** | Câu trả lời có đúng trọng tâm câu hỏi không | độ tương đồng giữa câu hỏi gốc và các câu hỏi "sinh ngược" từ câu trả lời |
| **Context Precision** | Context lấy về có "sạch" không (chunk đúng xếp trên) | trung bình precision có trọng số theo thứ hạng chunk relevant |
| **Context Recall** | Context có đủ để trả lời không | (số claim của đáp án chuẩn được context bao phủ) / tổng claim |
| **Correctness** | Đáp án có đúng sự thật không (cần reference) | so với đáp án chuẩn (LLM judge hoặc human) |
| **Hallucination rate** | Tỉ lệ câu trả lời chứa thông tin bịa | 1 − faithfulness (xấp xỉ) |

> **faithfulness bạn đã đo** chính là trục quan trọng nhất chống hallucination — giữ nguyên và nêu bật.

### 3.2 LLM-as-a-judge — quy trình & bias

**Cơ sở lý thuyết** (Zheng et al., NeurIPS 2023, MT-Bench/Chatbot Arena,
[arXiv:2306.05685](https://arxiv.org/abs/2306.05685)): LLM judge mạnh (GPT-4) đạt **>80% agreement với
con người** — tương đương mức đồng thuận giữa 2 người → chấp nhận được như xấp xỉ rẻ & mở rộng được của
human eval.

**Các bias đã ghi nhận** (Zheng 2023; survey [arXiv:2411.15594](https://arxiv.org/abs/2411.15594)):
- **Position bias** — thiên vị đáp án đặt trước.
- **Verbosity/length bias** — thiên vị đáp án dài.
- **Self-enhancement/self-preference bias** — thiên vị đáp án do chính model đó sinh.
- **Concreteness bias** — thiên vị đáp án nhiều số/chi tiết.

**Cách giảm thiểu:** (1) **hoán đổi vị trí** đáp án và chấm 2 lần rồi lấy trung bình (chống position bias);
(2) **rubric decomposition** — tách tiêu chí thành các bước rõ ràng thay vì hỏi 1 điểm tổng thể;
(3) dùng **pairwise comparison** thay vì chấm điểm tuyệt đối — nguồn [arXiv:2411.15594] cho thấy LLM judge
**khớp con người tốt hơn khi so cặp** hơn là chấm thang điểm; (4) tránh dùng chính model sinh đáp án làm judge.

### 3.3 Human evaluation — cỡ mẫu & độ đồng thuận

- **Thang điểm:** Likert 1–5 (tuyệt đối) hoặc pairwise (A tốt hơn B). Pairwise ổn định hơn.
- **Inter-annotator agreement (IAA):**
  - **Cohen's kappa** — chỉ dùng khi **đúng 2 người chấm** cùng tập.
  - **Fleiss' kappa** — tổng quát hoá cho **>2 người**, nhãn danh mục.
  - **Krippendorff's alpha** — linh hoạt nhất (nominal/ordinal/interval, nhiều người, thiếu nhãn).
  - Nguồn: [arXiv:2603.06865] — *(lưu ý: mã arXiv này bất thường, cần kiểm tra lại; nội dung định
    nghĩa kappa/alpha là kiến thức chuẩn nên vẫn dùng được)*.
- **Ngưỡng diễn giải (Landis & Koch 1977):** <0.20 kém, 0.21–0.40 vừa phải, 0.41–0.60 trung bình,
  **0.61–0.80 tốt (đáng để công bố)**, 0.81–1.0 gần như hoàn hảo. Các ngưỡng này là **quy ước, không
  phải chuẩn tuyệt đối** — nên ghi chú khi trích.

### 3.4 BLEU / ROUGE / BERTScore còn dùng cho RAG không?

**Phần lớn nghiên cứu RAG gần đây đã bỏ** các metric n-gram overlap này cho câu trả lời tự do, vì:
chúng đo **trùng lặp bề mặt** với một đáp án tham chiếu, trong khi một câu trả lời RAG **đúng nhưng
diễn đạt khác** vẫn bị chấm thấp; ngược lại câu **sai nhưng trùng từ** lại được điểm cao. Chúng **không
đo được faithfulness/hallucination**. → Chỉ nên nhắc như "baseline lịch sử"; metric chính là faithfulness
+ answer relevance (LLM-judge) và human eval.

---

## 4. Đánh giá chatbot hội thoại (ngoài RAG)

- **Task Success Rate (TSR):** % phiên người dùng đạt mục tiêu (vd tìm được sách phù hợp). Metric
  end-to-end quan trọng nhất với hệ tư vấn.
- **PARADISE framework** (Walker et al.): mô hình hoá user satisfaction = f(task success, các loại chi
  phí như số lượt hội thoại, thời gian). Cổ điển nhưng vẫn được trích cho spoken/dialogue systems.
- **SUS (System Usability Scale):** 10 câu, thang 0–100; **>68 = trên trung bình** (xem chi tiết ở báo
  cáo human-centric). Đo trải nghiệm tổng thể, không riêng nội dung.
- **Fallback / Out-of-Scope (OOS) handling:** đo khả năng **từ chối đúng lúc** khi câu hỏi ngoài phạm vi.
  - Cách đo: xây tập **câu hỏi OOS** (ngoài kho sách) + tập **in-scope**, tính:
    - **OOS Recall** = % câu OOS được từ chối đúng (không bịa).
    - **False Refusal Rate** = % câu in-scope bị từ chối oan.
  - Bạn đã có "kiểm tra fallback 4/4" — nên **mở rộng thành ma trận nhầm lẫn** (in-scope vs OOS ×
    trả lời vs từ chối) để có số liệu định lượng thay vì chỉ pass/fail.
- **Robustness:** thử câu hỏi nhiễu/mơ hồ/sai chính tả, xem hệ có sập hay trả lời hợp lý (tham chiếu RGB benchmark).

> **Không có "ngưỡng vàng" phổ quát cho tỉ lệ fallback** — nên bạn tự đặt mục tiêu (vd OOS recall ≥ 90%,
> false refusal ≤ 10%) và biện luận theo bối cảnh thư viện (thà từ chối còn hơn bịa thông tin sai về sách).

---

## 5. Đặc thù tiếng Việt & tài nguyên thấp

- **Word segmentation ảnh hưởng BM25:** trong tiếng Việt, **khoảng trắng không phải ranh giới từ** —
  theo nguồn ([ACL L18-1410](https://aclanthology.org/L18-1410.pdf)), ~85% word types gồm ≥2 âm tiết,
  nên cần **tách từ** trước khi index BM25. Nếu để nguyên âm tiết, BM25 sẽ khớp sai đơn vị nghĩa. → Nên
  nêu rõ bạn dùng bộ tách từ nào (VnCoreNLP / underthesea / pyvi) và điều đó ảnh hưởng BM25 ra sao.
- **Syllable-level vs word-level cho dense retrieval:** có nghiên cứu so sánh trực tiếp hai mức
  tokenization cho retrieval tiếng Việt ([arXiv:2209.14494](https://arxiv.org/abs/2209.14494)) → chứng
  minh đây là **biến thực nghiệm đo được**, đáng làm ablation.
- **Benchmark embedding tiếng Việt:**
  - **VN-MTEB** ([arXiv:2507.21500](https://arxiv.org/abs/2507.21500)): benchmark kiểu MTEB cho tiếng
    Việt, theo nguồn gồm **41 dataset / 6 loại task** (retrieval, classification, pair-classification,
    clustering, rerank, STS), đã benchmark ~18 embedding model → **dùng làm căn cứ chọn embedding**.
  - **BKAI bi-encoder** (ĐH Bách Khoa HN, [arXiv:2403.01616](https://arxiv.org/html/2403.01616v2)):
    trên Legal Text Retrieval Zalo 2021 dùng **Acc@K (Hit Rate) + MRR@10** (không dùng nDCG/MAP);
    theo nguồn PhoBERT-base-v2 đạt Acc@1≈73.28, Acc@10≈93.59, MRR@10≈80.73. *(Cần kiểm lại số từ paper.)*
- **Gợi ý embedding thực tế cho tiếng Việt:** các model thường được dùng gồm `bkai-foundation-models/
  vietnamese-bi-encoder`, `AITeamVN/Vietnamese_Embedding`, hoặc multilingual `intfloat/multilingual-e5`,
  `BAAI/bge-m3`. Nên đối chiếu bảng VN-MTEB để chọn và **trích dẫn lý do chọn**.

---

## 6. Chuẩn trình bày chương đánh giá trong luận văn

**Cấu trúc điển hình** (theo RAGAS paper, ARES paper, survey RAG của Gao et al. 2023):

1. **Experimental setup:** mô tả corpus (51 tác phẩm/163 chunk), tập test (30 truy vấn retrieval + 15
   câu E2E), cách xây ground-truth, model/embedding dùng, tham số (K, chunk size).
2. **Retrieval results:** bảng Precision/nDCG/MRR/MAP @K cho 4 pipeline + latency; **đánh dấu khác biệt
   có ý nghĩa thống kê** (paired t-test).
3. **Generation results:** faithfulness, answer relevance, pass rate (auto + human), fallback matrix.
4. **Ablation study:** so BM25 vs vector vs hybrid vs hybrid+rerank — chính là 4 pipeline của bạn → đây
   **đã là một ablation study hoàn chỉnh**, nên gọi tên đúng như vậy trong luận văn.
5. **Threats to validity / Limitations.**

### Mẫu viết "Threats to Validity" cho bộ test nhỏ (~30 truy vấn)

> *"Nghiên cứu này có một số hạn chế về tính hợp lệ. **(1) Construct validity:** ground-truth mức liên
> quan được gán bán tự động theo keyword nên tập qrels không đầy đủ; theo Buckley & Voorhees (2007),
> pooling với qrels không đầy đủ có thể thiên vị và phạt oan các pipeline (đặc biệt vector/rerank) lấy
> được tài liệu đúng nhưng chưa được gán nhãn. Do đó Recall@K trong nghiên cứu chỉ mang tính xấp xỉ và
> chúng tôi ưu tiên diễn giải theo Precision@K và nDCG@K. **(2) External validity:** bộ test gồm 30 truy
> vấn / 15 câu hỏi end-to-end trên miền văn học Việt, nên kết quả có thể không tổng quát hoá sang miền
> khác hoặc quy mô corpus lớn hơn. **(3) Statistical conclusion validity:** với cỡ mẫu ~30, chúng tôi
> dùng paired t-test (Urbano et al., 2019) thay vì Wilcoxon do độ tin cậy tốt hơn ở cỡ mẫu nhỏ, nhưng
> lực thống kê (power) vẫn hạn chế. **(4) Đánh giá tự động bằng LLM-as-a-judge** kế thừa các bias đã biết
> (position, verbosity, self-preference; Zheng et al., 2023); chúng tôi giảm thiểu bằng hoán đổi vị trí
> và đối chiếu với chấm tay trên toàn bộ tập."*

---

## Bảng tổng hợp: Metric → đo gì → công cụ → ngưỡng tham khảo

| Metric | Đo cái gì | Công cụ đo | Ngưỡng/diễn giải tham khảo |
|---|---|---|---|
| Precision@K | Độ chính xác top-K | Tự code / RAGAS | Càng gần 1 càng tốt; báo K=1,3,5,10 |
| Recall@K | Độ bao phủ (cần R đầy đủ) | Tự code | ⚠️ Xấp xỉ nếu qrels thiếu → dùng thận trọng |
| nDCG@K | Chất lượng thứ hạng (graded) | Tự code / pytrec_eval | **Metric retrieval chính**; >0.8 rất tốt |
| MRR | Vị trí kết quả đúng đầu tiên | Tự code | Hợp chatbot; >0.8 tốt |
| MAP | Precision trung bình theo hạng | pytrec_eval | Báo kèm nDCG |
| bpref | Robust với qrels không đầy đủ | pytrec_eval | Dùng nếu qrels thiếu; ổn định tới 25–50% qrels |
| Faithfulness | Bám nguồn, chống hallucination | RAGAS / TruLens | **Trục generation chính**; >0.9 mong muốn |
| Answer Relevance | Đúng trọng tâm câu hỏi | RAGAS / TruLens | >0.8 tốt |
| Context Precision/Recall | Chất lượng context lấy về | RAGAS | Chẩn đoán lỗi retrieval vs generation |
| OOS Recall / False Refusal | Fallback đúng lúc | Tự xây tập OOS | Tự đặt mục tiêu (vd OOS recall ≥90%) |
| SUS | Usability tổng thể | Bảng hỏi 10 câu | **>68 = trên trung bình** |
| Cohen's/Fleiss' κ | Đồng thuận người chấm | statsmodels/sklearn | **0.61–0.80 = tốt** (Landis & Koch) |
| Latency | Tốc độ phản hồi | Tự đo | Báo trung bình + p95 |

---

## Kết luận & Khuyến nghị cho hệ thống của bạn

**Bộ metric + quy trình tối thiểu đủ chuẩn để bảo vệ:**

1. **Retrieval:** báo **nDCG@K và MRR làm chính**, Precision@K bổ trợ; giữ MAP/Hit như phụ. **Hạ vai trò
   Recall@K/F1@K** (đang trùng Precision) và nêu rõ lý do. So 4 pipeline kèm **paired t-test**.
2. **Generation:** giữ **faithfulness** làm điểm nhấn; thêm **answer relevance** (RAGAS, chạy trên 30 câu
   để tiết kiệm API). Trình bày pass rate **2 con số trung thực** (auto + human) — đúng hướng bạn đang làm.
3. **Fallback:** nâng "4/4 pass" thành **ma trận in-scope × OOS** để có số định lượng.
4. **Tiếng Việt:** nêu rõ bộ tách từ dùng cho BM25 + trích **VN-MTEB** để biện minh lựa chọn embedding.
5. **Trình bày:** gọi đúng tên phần so-4-pipeline là **ablation study**; viết đủ mục **Threats to Validity** (mẫu ở §6).

**Điểm yếu phương pháp luận cần CHỦ ĐỘNG thừa nhận trước hội đồng:**

- Ground-truth theo keyword → qrels không đầy đủ → **Recall/MAP có thể phạt oan vector/rerank** (pooling bias).
- Cỡ mẫu nhỏ (30 truy vấn / 15 câu) → power thống kê hạn chế, khó tổng quát hoá.
- LLM-as-a-judge có bias → đã giảm thiểu bằng đối chiếu chấm tay.

> Chủ động nêu 3 điểm này **trước khi hội đồng hỏi** sẽ được đánh giá cao về tính trung thực khoa học —
> đây chính là điểm mạnh, không phải điểm trừ.

---

### Nguồn primary đã thu thập (13)

1. Buckley & Voorhees 2004 — bpref / incomplete judgments — [ACM 1008992.1009000](https://dl.acm.org/doi/10.1145/1008992.1009000)
2. Buckley & Voorhees 2007 — pooling bias — [ACM 1277741.1277755](https://dl.acm.org/doi/10.1145/1277741.1277755)
3. Smucker et al. 2007 — comparison of significance tests — [ACM 1321440.1321528](https://dl.acm.org/doi/10.1145/1321440.1321528)
4. Urbano et al. 2019 — statistical significance testing in IR — [arXiv:1905.11096](https://arxiv.org/pdf/1905.11096)
5. Zheng et al. 2023 — LLM-as-a-judge / MT-Bench — [arXiv:2306.05685](https://arxiv.org/abs/2306.05685)
6. Survey LLM-as-a-judge 2024 — biases & mitigation — [arXiv:2411.15594](https://arxiv.org/abs/2411.15594)
7. Inter-annotator agreement (kappa/alpha) — [arXiv:2603.06865](https://arxiv.org/html/2603.06865) *(cần kiểm mã arXiv)*
8. VN-MTEB — [arXiv:2507.21500](https://arxiv.org/abs/2507.21500)
9. Vietnamese retrieval / syllable vs word — [arXiv:2209.14494](https://arxiv.org/abs/2209.14494)
10. BKAI bi-encoder tiếng Việt — [arXiv:2403.01616](https://arxiv.org/html/2403.01616v2)
11. Vietnamese word segmentation — [ACL L18-1410](https://aclanthology.org/L18-1410.pdf)
12. RAG-related — [arXiv:2412.00657](https://arxiv.org/abs/2412.00657)
13. RAG-related — [arXiv:2108.08787](https://arxiv.org/abs/2108.08787)
