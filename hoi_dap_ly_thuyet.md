# HỎI ĐÁP LÝ THUYẾT — chuẩn bị bảo vệ ĐATN

> Cách trả lời ăn điểm: **định nghĩa ngắn gọn → liên hệ ngay với đồ án của em**.
> Hiểu ý rồi diễn đạt tự nhiên. Số liệu in đậm cần nhớ.

---

## A. KHÁI NIỆM NỀN TẢNG

### 1. LLM (Large Language Model) là gì?
Mô hình ngôn ngữ lớn — mạng nơ-ron (Transformer) huấn luyện trên lượng văn bản khổng lồ,
học **dự đoán từ (token) tiếp theo**. Đồ án dùng **Gemini 2.5 Flash** làm bộ sinh câu trả lời.

### 2. RAG (Retrieval-Augmented Generation) là gì?
"Sinh có tăng cường truy hồi": thay vì để LLM trả lời bằng trí nhớ (dễ bịa), ta **truy hồi
các đoạn liên quan từ kho tri thức**, đưa vào ngữ cảnh, rồi LLM sinh câu trả lời **dựa trên
tài liệu đó**. Lợi ích: giảm ảo tưởng, có trích dẫn kiểm chứng được, cập nhật kho không cần
huấn luyện lại. Đây là kiến trúc cốt lõi của đồ án.

### 3. Semantic Search (tìm kiếm ngữ nghĩa) là gì?
Tìm **theo ý nghĩa** thay vì khớp mặt chữ. Câu hỏi và tài liệu đều thành **vector** (embedding),
tìm vector "gần" nhau (đo **cosine**). Hỏi "truyện về nông dân nghèo" vẫn ra *Tắt đèn* dù câu
hỏi không chứa chữ "Tắt đèn". Chịu được diễn đạt khác và lỗi gõ sai.

### 4. Embedding là gì?
Biến đoạn văn thành **vector số chiều cố định** (đồ án: **384 chiều**). Nghĩa gần nhau → vector
gần nhau. Model: `paraphrase-multilingual-MiniLM-L12-v2` (hỗ trợ tiếng Việt).

### 5. Vector Database / Qdrant là gì?
DB chuyên lưu **vector** và tìm nhanh vector gần nhất. Đồ án dùng **Qdrant** (cosine, chỉ mục
**HNSW**), lưu **11.759 vector** + metadata (năm, thể loại, tác giả). Chạy cả local lẫn Cloud.

### 6. HNSW là gì?
*Hierarchical Navigable Small World* — chỉ mục dạng **đồ thị nhiều tầng**, tìm vector gần nhất
**gần đúng (ANN)** rất nhanh thay vì vét cạn. Đánh đổi chút chính xác lấy tốc độ.

### 7. BM25 là gì?
Thuật toán xếp hạng **theo từ khóa** (cải tiến TF-IDF): tài liệu chứa nhiều từ khóa hiếm của
câu hỏi thì điểm cao. Mạnh với **tên riêng, tên tác phẩm** — thứ ngữ nghĩa hay bỏ sót.

### 8. Hybrid Search — vì sao cần?
Kết hợp **BM25 (từ khóa) + Vector (ngữ nghĩa)** song song rồi hợp nhất. Mỗi phương pháp bù
điểm yếu của nhau. Số liệu: Vector **33%**, BM25 **77%**, **Hybrid 83%** (Precision@1).

### 9. RRF (Reciprocal Rank Fusion) — vì sao k=60?
Điểm mỗi tài liệu = **Σ 1/(k + hạng)** qua các danh sách. Chỉ dùng **thứ hạng** → không cần
chuẩn hóa điểm giữa BM25 và cosine (hai thang khác nhau). **k=60** là giá trị chuẩn từ bài
báo gốc (Cormack, 2009).

### 10. Cross-Encoder khác Bi-Encoder chỗ nào?
- **Bi-Encoder** (truy hồi): mã hóa câu hỏi và tài liệu **riêng rẽ** thành 2 vector rồi so
  cosine — nhanh, quét hàng nghìn.
- **Cross-Encoder** (rerank): đưa **cặp (câu hỏi, tài liệu) vào cùng lúc** chấm điểm — chính
  xác hơn nhưng chậm, chỉ áp **top nhỏ**. Đồ án dùng `ms-marco-MiniLM-L-6-v2`.

### 11. Chunking — vì sao chia nhỏ?
Chia văn bản dài thành **đoạn nhỏ (chunk)** trước khi embed: embedding chính xác hơn trên đoạn
ngắn, đưa vào prompt gọn đúng trọng tâm. Đồ án có **11.759 chunk**.

### 12. Hallucination (ảo tưởng) — chống thế nào?
LLM **bịa thông tin nghe hợp lý nhưng sai**. Đồ án chống **3 lớp**: (1) ngưỡng RRF 0.003 —
dưới ngưỡng coi ngoài kho, từ chối; (2) prompt yêu cầu **chỉ dùng ngữ cảnh** + từ chối khi
thiếu; (3) mọi câu trả lời **kèm nguồn** để đối chiếu.

### 13. Cosine similarity là gì?
Đo độ giống nhau giữa 2 vector bằng **góc** giữa chúng (−1…1, gần 1 = giống). Không phụ thuộc
độ dài vector — hợp so sánh ngữ nghĩa.

### 14. Temperature / Top-K trong hệ thống?
- **Temperature**: độ "sáng tạo" của LLM (thấp = bám sát). Đồ án đặt ~0.2 để bám tài liệu.
- **Top-K**: số đoạn tài liệu đưa vào ngữ cảnh (mặc định **5**).

---

## B. VỀ HỆ THỐNG CỦA EM

### 15. Kiến trúc tổng thể hoạt động thế nào? (câu hay hỏi nhất)
"Người dùng gõ câu hỏi → nếu là câu nối tiếp thì **viết lại** thành câu độc lập → **truy hồi
song song** BM25 + Vector trên Qdrant → hợp nhất **RRF** → **Cross-Encoder** sắp lại top →
kiểm **ngưỡng chống ảo tưởng** → top-5 đoạn vào prompt cho **Gemini** sinh câu trả lời kèm
**trích dẫn**, hiển thị dần (streaming)."

### 16. Dữ liệu lấy từ đâu, xử lý thế nào?
Crawler từ nguồn văn học mở (vnthuquan) → làm sạch, phân mảnh → **khử trùng lặp** → **làm giàu
metadata** (Gemini + kiểm chứng Wikidata) → embed + nạp Qdrant + BM25. Độ phủ canon **~89%**.

### 17. Đánh giá hệ thống — số liệu phải nhớ
Bộ **30 câu có nhãn**, đo **Precision@K, Recall@K, MRR**:

| Chế độ | P@1 | MRR |
|--------|-----|-----|
| Vector only | 33,3% | 0,446 |
| BM25 only | 76,7% | 0,863 |
| **Hybrid** | **83,3%** | **0,887** |

### 18. MRR / Precision@K là gì?
- **Precision@K**: trong K kết quả đầu, tỷ lệ kết quả đúng.
- **MRR**: trung bình **nghịch đảo thứ hạng** của kết quả đúng đầu tiên — "kết quả đúng có ở
  trên đầu không". Gần 1 là tốt.

---

## C. CẢI TIẾN / ĐÓNG GÓP (câu "bot cải tiến được gì")

**6 cải tiến** so với chatbot RAG cơ bản:
1. **Hybrid thay vì vector thuần** — chứng minh bằng số liệu với tiếng Việt (83% vs 33%).
2. **Tái xếp hạng Cross-Encoder** — ngữ cảnh sạch hơn trước khi đưa cho LLM.
3. **Làm giàu metadata** — trả lời được cả câu hỏi năm/thể loại, không chỉ nội dung.
4. **Chống ảo tưởng nhiều lớp** — từ chối thay vì bịa.
5. **Bộ nhớ hội thoại có kiểm soát** — hiểu câu nối tiếp, ngân sách 20.000 token, tự tóm tắt.
6. **Robustness** — vẫn đúng khi gõ **sai chính tả** (nhờ tìm ngữ nghĩa).

---

## D. CÂU PHẢN BIỆN / HẠN CHẾ

### 19. Vì sao không fine-tune mô hình riêng?
RAG cho chất lượng tốt **không cần dữ liệu huấn luyện lớn + GPU**; cập nhật kiến thức chỉ bằng
sửa kho. Fine-tune tốn kém, dễ lỗi thời, vẫn ảo tưởng.

### 20. Vì sao dùng Gemini / không tự host?
Gemini 2.5 Flash **miễn phí mức đủ dùng**, tiếng Việt tốt, nhanh. Tự host cần GPU mạnh, vượt
phạm vi đồ án. RAG **tách rời** bộ sinh nên thay LLM khác dễ.

### 21. Hạn chế?
(1) embedder **chưa fine-tune** cho văn học VN; (2) bộ đánh giá mới **30 câu**; (3) phụ thuộc
**API Gemini** (cần mạng); (4) câu **không dấu/khẩu ngữ** đôi khi chưa tốt.

### 22. Hướng phát triển?
Fine-tune embedder; mở rộng đánh giá + đo **faithfulness**; chuẩn hóa câu hỏi (không dấu → có
dấu); cân nhắc self-host LLM.

### 23. Nếu kho không có thông tin thì sao?
Hệ thống **từ chối** ("không tìm thấy trong thư viện") thay vì bịa — đúng thiết kế, không phải lỗi.

### 24. Làm sao đảm bảo không bịa?
Ba lớp (câu 12) + temperature thấp + luôn hiển thị nguồn. Ưu tiên "**thà từ chối còn hơn trả lời sai**".

---

## E. MEMORY & CONTEXT BAR (câu dễ hỏi khi thấy thanh "Ngữ cảnh")

### 25. Bộ nhớ hội thoại (memory) hoạt động thế nào?
Gồm **3 cơ chế** (ở `retrieval_qa.py`, Pha 4):
1. **Viết lại câu hỏi** (`contextualize_query`): câu nối tiếp *"tác giả đó mất năm nào?"* được
   Gemini (temperature 0.0) viết lại thành *"Nam Cao mất năm nào?"* **trước khi truy hồi** —
   thay đại từ bằng tên cụ thể lấy từ lịch sử. Có bộ lọc: kết quả rỗng/quá dài → dùng câu gốc.
2. **Cửa sổ nguyên văn + tóm tắt chạy** (`fit_memory` + `summarize_history`): giữ vài lượt gần
   nhất **nguyên văn**, dồn lượt cũ vào **bản tóm tắt** (Gemini ~150 từ, giữ tên tác giả/tác
   phẩm). Luôn giữ tối thiểu 1 lượt gần nhất nguyên văn. Gemini lỗi khi tóm tắt → giữ bản cũ.
3. **Ngân sách token**: `CONTEXT_TOKEN_LIMIT = 20.000`, tự tóm tắt khi chạm
   `SUMMARY_TRIGGER_RATIO = 0.75` (75%). Prompt cuối =
   `system + tài liệu + [tóm tắt lượt cũ] + [lượt gần nguyên văn] + câu hỏi`.

### 26. Context Bar (thanh "Ngữ cảnh 0/20.000 tok") là gì?
**Trực quan hóa ngân sách token** đang dùng cho prompt:
- Sau mỗi lượt, dựng thử prompt và **ước lượng token** = số ký tự ÷ 3 (~3 ký tự = 1 token cho
  tiếng Việt).
- Hiển thị **token dùng / 20.000** + phần trăm; đổi màu **xanh → vàng → đỏ**.
- **Vạch đỏ = 75%** chính là ngưỡng kích hoạt tự tóm tắt (câu 25, cơ chế 3).
- Ý nghĩa: em **chủ động đặt trần 20.000 token** (dù Gemini hỗ trợ ~1 triệu) để kiểm soát **độ
  trễ và chi phí**, thay vì để prompt phình vô hạn.

**Nếu hỏi "sao không dùng hết 1 triệu token?"**: ngân sách lớn làm chậm + tốn tiền mỗi lượt;
20.000 đủ cho hội thoại tra cứu, và cơ chế tóm tắt giúp hội thoại dài vẫn không tràn.

---

**Mẹo trả lời:** nếu bị hỏi khái niệm không chắc, đừng đoán bừa — định nghĩa phần mình biết rồi
**liên hệ về cách đồ án dùng nó**. Hội đồng đánh giá cao việc hiểu *tại sao* chọn kỹ thuật đó.
