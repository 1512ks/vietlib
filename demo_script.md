# Kịch bản demo & mô tả chương trình — Buổi kiểm tra ĐATN

> Chatbot hỏi–đáp văn học Việt Nam bằng kiến trúc RAG (Retrieval-Augmented Generation).
> Đọc phần I để mở màn (~2 phút), phần II là các bước demo kèm lời giải thích cho từng bước.

---

## PHẦN I — BÀI MÔ TẢ CHƯƠNG TRÌNH (đọc mở màn, ~2 phút)

Em xin trình bày chương trình **Chatbot Thư viện Điện tử Tiếng Việt** — hệ thống hỏi–đáp
về văn học Việt Nam, xây dựng theo kiến trúc **RAG (Retrieval-Augmented Generation)**.

Vấn đề của các mô hình ngôn ngữ lớn khi hỏi về văn học Việt Nam là chúng thường
**bịa thông tin (ảo tưởng)** — sai tên tác giả, sai năm xuất bản, bịa nội dung tác phẩm.
Giải pháp của em là **không để mô hình trả lời từ trí nhớ**, mà bắt nó trả lời dựa trên
một **kho tri thức đã kiểm soát**: hệ thống truy hồi các đoạn văn bản liên quan từ kho,
đưa vào ngữ cảnh, rồi mô hình sinh câu trả lời **kèm trích dẫn nguồn**.

**Kho tri thức:** dữ liệu được thu thập tự động (crawler) từ nguồn văn học mở, làm sạch,
khử trùng lặp, và làm giàu siêu dữ liệu (năm xuất bản, thể loại, nhà xuất bản) bằng
Gemini có kiểm chứng chéo với Wikidata. Kết quả là **11.759 đoạn văn bản (chunk)**,
độ phủ khoảng **89% các tác phẩm kinh điển** trong danh mục đối chiếu.

**Luồng xử lý một câu hỏi gồm 4 bước:**

1. **Truy hồi lai hợp (Hybrid Retrieval):** câu hỏi được tìm song song bằng hai phương pháp —
   **BM25** (khớp từ khóa, mạnh với tên riêng, tên tác phẩm) và **tìm kiếm ngữ nghĩa**
   (embedding 384 chiều bằng `paraphrase-multilingual-MiniLM-L12-v2`, lưu trong
   **Qdrant** với chỉ mục HNSW, độ đo cosine).
2. **Hợp nhất RRF (Reciprocal Rank Fusion, k=60):** trộn hai danh sách kết quả theo thứ hạng,
   không cần chuẩn hóa điểm số giữa hai hệ khác nhau.
3. **Tái xếp hạng Cross-Encoder** (`ms-marco-MiniLM-L-6-v2`): đọc cặp (câu hỏi, đoạn văn)
   cùng lúc để chấm điểm chính xác hơn Bi-Encoder, sắp lại top kết quả.
4. **Sinh câu trả lời bằng Gemini 2.5 Flash:** các đoạn văn tốt nhất được đưa vào prompt,
   mô hình trả lời kèm **nguồn tham khảo**. Nếu điểm truy hồi dưới ngưỡng
   (RRF < 0.003) hệ thống **từ chối trả lời** thay vì bịa — đây là cơ chế chống ảo tưởng.

Hệ thống còn có **bộ nhớ hội thoại**: hiểu câu hỏi nối tiếp ("tác giả đó", "cuốn này"),
với ngân sách ngữ cảnh 12.000 token và tự động tóm tắt khi dùng quá 75%.

**Kết quả đánh giá** trên bộ 30 câu hỏi có nhãn: truy hồi lai hợp đạt
**Precision@1 = 83,3%**, **MRR = 0,887** — cao hơn dùng riêng BM25 (76,7%) và cao hơn
hẳn dùng riêng vector (33,3%). Em sẽ demo trực tiếp ngay sau đây.

---

## PHẦN II — CÁC BƯỚC DEMO (từng bước: THAO TÁC → LỜI GIẢI THÍCH)

### Bước 0 — Chuẩn bị TRƯỚC khi hội đồng vào (30 phút trước)

```
.venv\Scripts\activate
streamlit run app.py
```
- Khởi động mất **~35 giây** (nạp model embedding + cross-encoder). Chạy 1 câu warm-up bất kỳ.
- Kiểm tra mạng (Gemini API + Qdrant Cloud đều cần mạng). Bật sẵn 4G dự phòng.
- Đóng mọi tab/editor đang mở `.env` hoặc file APIKEY.

### Bước 1 — Giới thiệu giao diện (30 giây)

**Thao tác:** chỉ vào sidebar, không bấm gì vội.

**Nói:** "Giao diện gồm khung chat chính và bảng điều khiển bên trái, nơi có thể
chọn **chế độ truy hồi** (Hybrid / BM25 / Vector — phục vụ so sánh thực nghiệm),
bật tắt **tái xếp hạng Cross-Encoder**, chỉnh **Top-K** số tài liệu tham khảo,
bật **bộ nhớ hội thoại**, và thanh **theo dõi ngân sách ngữ cảnh** — vạch đỏ là
ngưỡng 75% khi hệ thống tự tóm tắt lịch sử hội thoại."

### Bước 2 — Câu hỏi mở màn (chế độ Hybrid mặc định)

**Gõ:** `Tác phẩm Số đỏ của Vũ Trọng Phụng nói về điều gì?`

**Nói trong lúc chờ (~3–8 giây):** "Câu hỏi đang được tìm song song bằng BM25 và
tìm kiếm ngữ nghĩa trên 11.759 đoạn văn bản, hợp nhất bằng RRF, tái xếp hạng bằng
Cross-Encoder, và 5 đoạn tốt nhất được đưa cho Gemini sinh câu trả lời."

**Khi có kết quả:** mở expander **"📚 Nguồn tài liệu"** → "Đây là điểm khác biệt so
với hỏi ChatGPT trực tiếp: mọi câu trả lời đều kèm nguồn từ kho tri thức, kiểm chứng được."

### Bước 3 — Câu hỏi khai thác siêu dữ liệu (thành quả làm giàu metadata)

**Gõ:** `Ai là tác giả của Truyện Kiều và tác phẩm ra đời năm nào?`

**Nói:** "Thông tin năm xuất bản, thể loại, nhà xuất bản không có sẵn trong văn bản gốc —
em đã làm giàu siêu dữ liệu bằng pipeline tự động: Gemini trích xuất, kiểm chứng chéo
với Wikidata, rồi gắn vào payload của từng vector trong Qdrant. Nhờ đó chatbot trả lời
được cả các câu hỏi siêu dữ liệu chứ không chỉ nội dung."

### Bước 4 — So sánh các chế độ truy hồi (điểm nhấn thực nghiệm)

**Thao tác:** hỏi cùng một câu ở 2 chế độ:
1. Sidebar → chọn **"🧠 Vector Only"** → gõ: `Tắt đèn của Ngô Tất Tố viết về ai?`
2. Đổi lại **"🔀 Hybrid (BM25 + Vector)"** → gõ lại đúng câu đó.

**Kết quả đã test (09/07):** ở chế độ **Vector Only** câu trả lời **mơ hồ và thiếu** —
kiểu "*Tắt đèn là tác phẩm hiện thực phê phán tiêu biểu... tuy nhiên không tìm thấy
thông tin chi tiết cụ thể*"; chuyển sang **Hybrid** thì trả lời **đầy đủ, có chiều sâu**
kèm tiểu sử tác giả (Ngô Tất Tố 1893–1954) và nguồn trích dẫn. Tương phản rõ về **chất
lượng câu trả lời**.

> ⚠️ **LƯU Ý tính không tất định:** kết quả Vector Only thay đổi giữa các lần chạy (có
> lần từ chối hẳn, có lần trả lời mơ hồ) vì phụ thuộc độ tương đồng vector + Gemini.
> ĐỪNG hứa trước "vector sẽ từ chối". Cứ chạy và chỉ ra: câu trả lời Hybrid **giàu và
> chắc** hơn hẳn. **Bằng chứng cứng là bảng số liệu**, không phải một lần chạy đơn lẻ.

**Nói:** "Đây chính là điểm yếu của tìm kiếm ngữ nghĩa thuần: embedding đa ngôn ngữ
tổng quát yếu với tên riêng, tên tác phẩm tiếng Việt — trên bộ đánh giá 30 câu vector
thuần chỉ đạt Precision@1 = 33%. BM25 khớp từ khóa đạt 77%, còn **lai hợp cả hai đạt
83%, MRR 0,887** — mỗi phương pháp bù điểm yếu của phương pháp kia. Đó là lý do em
chọn kiến trúc hybrid."

### Bước 5 — Chống ảo tưởng (câu ngoài phạm vi kho tri thức)

**Gõ:** `Cách nấu phở bò truyền thống như thế nào?`
*(câu thay thế đã test: `Nội dung tiểu thuyết Fifty Shades of Grey là gì?` — chứng minh
cả sách không có trong kho cũng bị từ chối, không phải chỉ lọc theo chủ đề)*

> ⚠️ **TUYỆT ĐỐI KHÔNG dùng Harry Potter làm ví dụ ngoài phạm vi** — kho tri thức CÓ
> truyện dịch, hệ thống sẽ trả lời nội dung Harry Potter một cách chính xác (đã test).
> Nếu hội đồng hỏi về truyện dịch, đó lại là điểm cộng: "kho bao gồm cả tác phẩm dịch
> phổ biến tại Việt Nam".

**Kết quả đã test trước (08/07):** hệ thống từ chối: *"Tôi không tìm thấy thông tin...
Thư viện hiện tập trung vào văn học Việt Nam và các tác phẩm dịch phổ biến tại Việt Nam."*

**Nói:** "Đây là câu ngoài phạm vi kho tri thức. Nếu điểm truy hồi cao nhất dưới ngưỡng
RRF 0.003, hệ thống chặn ngay và trả lời 'không tìm thấy trong thư viện' — **từ chối
thay vì bịa**. Ngoài ra còn ngưỡng cảnh báo thứ hai (0.006): khi điểm thấp, prompt sẽ
yêu cầu Gemini dè dặt và từ chối các chi tiết không có trong tài liệu."

### Bước 6 — Bộ nhớ hội thoại (câu hỏi nối tiếp)

**Gõ lần lượt 2 câu** *(đã test 08/07 — câu 2 trả lời đúng "30/11/1951" kèm nguồn)*:
1. `Nam Cao có những tác phẩm tiêu biểu nào?`
2. `Tác giả đó mất năm bao nhiêu?`

**Nói:** "Câu thứ hai không nhắc tên Nam Cao, nhưng hệ thống hiểu 'tác giả đó' nhờ
bộ nhớ hội thoại: lịch sử được đưa vào bước viết lại câu hỏi (query rewriting) trước
khi truy hồi. Thanh 'Ngữ cảnh' bên sidebar cho thấy mức dùng token; chạm vạch đỏ 75%
của 12.000 token thì hệ thống tự tóm tắt các lượt cũ để tiết kiệm."

### Bước 7 — Kết thúc demo (tùy thời gian)

- Chỉ nhanh: **câu hỏi gợi ý** tự sinh, nút **xuất lịch sử chat** (JSON), tùy chọn
  hiện **trích đoạn văn bản** trong thẻ nguồn.
- Chốt: "Toàn bộ hệ thống cũng đã được triển khai trên Streamlit Cloud + Qdrant Cloud,
  chạy được từ trình duyệt bất kỳ" *(chỉ nói nếu đã kiểm tra link còn sống sáng nay)*.

---

## PHẦN III — BẢNG SỐ LIỆU CẦN THUỘC (eval 30 câu, DB cuối 25/06/2026)

| Chế độ | P@1 | P@5 | MRR | Độ trễ TB |
|---|---|---|---|---|
| BM25 only | 76,7% | 71,3% | 0,863 | ~55 ms |
| Vector only | 33,3% | 35,3% | 0,446 | ~820 ms |
| **Hybrid (RRF)** | **83,3%** | 70,7% | **0,887** | ~870 ms |
| Hybrid + Rerank | 83,3% | 70,7% | 0,887 | ~580 ms |

Số liệu hệ thống: **11.759 chunk** · độ phủ canon **~89%** · embedding **384 chiều** ·
RRF **k=60** · ngưỡng chặn **0.003** / cảnh báo **0.006** · ngữ cảnh **12.000 token**,
tự tóm tắt ở **75%** · cold start **~35 s**, câu đầu ~8 s, các câu sau **~2–3 s**.

---

## PHẦN IV — CÂU HỎI HỘI ĐỒNG DỰ KIẾN & Ý TRẢ LỜI

**1. Vì sao không dùng thẳng ChatGPT/Gemini mà phải RAG?**
LLM bịa thông tin về văn học VN (dữ liệu huấn luyện ít tiếng Việt chuyên sâu); RAG buộc
mô hình trả lời từ kho đã kiểm soát, có trích dẫn, kiểm chứng được, và cập nhật kho
không cần huấn luyện lại.

**2. RRF là gì, vì sao k=60?**
Điểm RRF của tài liệu = Σ 1/(k + hạng) qua các danh sách kết quả. Ưu điểm: chỉ dùng
thứ hạng nên không phải chuẩn hóa điểm giữa BM25 và cosine (hai thang khác nhau).
k=60 là giá trị chuẩn từ bài báo gốc (Cormack et al. 2009), làm giảm chênh lệch quá
lớn giữa các hạng đầu.

**3. Cross-Encoder khác Bi-Encoder chỗ nào? Trong bảng kết quả rerank không tăng P@1?**
Bi-Encoder mã hóa câu hỏi và tài liệu riêng rẽ (nhanh, dùng để truy hồi hàng nghìn);
Cross-Encoder đọc cặp (câu hỏi, tài liệu) cùng lúc (chính xác hơn, chỉ dùng rerank
top nhỏ). Trên bộ 30 câu, P@1 đã 83% nên rerank không cải thiện thêm ở tập này, nhưng
nó sắp lại thứ tự trong top-5 giúp đoạn đưa vào prompt Gemini tốt hơn — ảnh hưởng đến
chất lượng câu trả lời cuối, không chỉ chỉ số truy hồi.

**4. Vì sao vector thuần kém vậy (33%)?**
Model embedding đa ngôn ngữ tổng quát, chưa fine-tune cho văn học VN; câu hỏi thường
chứa tên riêng/tên tác phẩm — dạng tín hiệu từ vựng mà BM25 bắt tốt hơn ngữ nghĩa.
Đây chính là luận cứ cho kiến trúc hybrid.

**5. Dữ liệu lấy từ đâu, có bản quyền không?**
Crawler từ nguồn văn học mở (vnthuquan), phần lớn tác phẩm kinh điển đã hết hạn bảo hộ;
dùng cho mục đích nghiên cứu/học thuật.

**6. Làm sao biết chatbot không bịa?**
Ba lớp: (1) ngưỡng chặn out-of-corpus, (2) prompt yêu cầu chỉ dùng ngữ cảnh + từ chối
khi thiếu thông tin, (3) mọi câu trả lời kèm nguồn để đối chiếu.

**7. Hạn chế và hướng phát triển?**
Embedding chưa fine-tune cho tiếng Việt chuyên ngành; đánh giá mới 30 câu; phụ thuộc
API Gemini. Hướng: fine-tune embedder, mở rộng bộ đánh giá, thêm đánh giá chất lượng
sinh (faithfulness), self-host LLM.

---

**Nguyên tắc vàng:** chỉ gõ câu ĐÃ test trước. Hội đồng yêu cầu câu tự do → cứ chạy;
nếu kết quả kém, giải thích bằng số liệu ("hệ thống đúng 83% trên bộ đánh giá, đây là
ca khó vì...") thay vì lúng túng.
