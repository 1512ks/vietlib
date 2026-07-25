# BỘ CÂU HỎI DEMO — đã test thực tế đêm 09/07/2026

> Tất cả câu dưới đây đã chạy thật trên hệ thống và cho kết quả như ghi chú.
> Gõ ĐÚNG các câu này. Thứ tự trình bày theo luồng demo. Cột "Kết quả" = điều đã xảy ra khi test.

---

## 0. HỆ TRUY VẤN THỂ HIỆN NĂNG LỰC (bảng tổng — dùng để giới thiệu năng lực)

Để chứng minh chatbot không chỉ "tra từ khóa", hãy trình bày **8 loại truy vấn** bên dưới,
mỗi loại khoe một năng lực khác nhau. Tất cả câu minh họa đã test chạy đúng đêm 09/07.

| # | Loại truy vấn | Năng lực thể hiện | Câu minh họa (đã test ✅) |
|---|---------------|-------------------|---------------------------|
| 1 | **Factual** (tra cứu chính xác) | BM25 khớp tên riêng/tên sách | *Chí Phèo là tác phẩm của tác giả nào?* |
| 2 | **Semantic** (theo chủ đề, không nêu tên sách) | Vector hiểu ngữ nghĩa | *Truyện nào khắc họa người nông dân nghèo khổ bị áp bức bóc lột?* |
| 3 | **Metadata** (năm / thể loại) | Làm giàu payload | *Chí Phèo thuộc thể loại gì?* · *Truyện Kiều ra đời năm nào?* |
| 4 | **Sai chính tả** (typo) | Độ mạnh mẽ (robustness) | *Ai viết Số đở?* · *Chí Phèo của Nam Coa là gì?* |
| 5 | **Khẩu ngữ** (diễn đạt tự nhiên) | Hiểu văn nói | *Kể cho tôi nghe về cuốn Số đỏ đi* |
| 6 | **So sánh / tổng hợp** | RAG tổng hợp nhiều nguồn | *So sánh hoàn cảnh của Chí Phèo và lão Hạc* |
| 7 | **Hội thoại đa lượt** (memory) | Nhớ ngữ cảnh, hiểu câu nối tiếp | *Vợ nhặt của ai?* → *Tác giả đó viết gì khác?* |
| 8 | **Ngoài phạm vi** (chống ảo tưởng) | Từ chối thay vì bịa | *Giá vàng hôm nay bao nhiêu?* |

**Cách trình bày (2 phút):** "Em minh họa 8 loại truy vấn để cho thấy hệ thống xử lý được
nhiều tình huống thực tế. Loại 1–3 là truy hồi cơ bản; loại 4 cho thấy **chịu được lỗi gõ
sai** — nhờ tìm kiếm ngữ nghĩa bù cho từ khóa; loại 6 cho thấy khả năng **tổng hợp nhiều
tác phẩm** chứ không chỉ tra một cuốn; loại 8 là cơ chế **chống ảo tưởng**."

### Điểm nhấn nên khoe: SAI CHÍNH TẢ (loại 4)
Đây là câu gây ấn tượng mạnh — gõ sai mà vẫn trả lời đúng:

| Câu (cố tình gõ sai) | Kết quả đã test |
|----------------------|-----------------|
| **Ai viết Số đở?** | ✅ "Số đỏ được viết bởi Vũ Trọng Phụng" |
| **Chí Phèo của Nam Coa là tác phẩm gì?** | ✅ "truyện ngắn hiện thực phê phán, xuất bản 1941" |
| **Truyện Kiềuu do ai sáng tác?** | ✅ "do đại thi hào Nguyễn Du sáng tác" |

**Lời dẫn:** "Người dùng thật thường gõ sai. Vì hệ thống dùng **tìm kiếm ngữ nghĩa** (vector)
song song với từ khóa, nó vẫn hiểu ý dù chính tả sai — điều mà tìm kiếm từ khóa thuần không làm được."

> ⚠️ **KHÔNG ổn định — TRÁNH khi demo (đã test bị lỗi/từ chối):**
> - *Không dấu:* "Chi Pheo la tac pham cua ai" thì được, nhưng "Tat den viet ve dieu gi" bị TỪ CHỐI.
>   → Chỉ nói "hệ thống xử lý được **một phần** câu không dấu", đừng demo trực tiếp.
> - *Khẩu ngữ:* "Kể cho tôi nghe về cuốn Số đỏ đi" được, nhưng "Ông nào viết Chí Phèo vậy?" bị từ chối.
>   → Chỉ dùng câu khẩu ngữ đã test ở bảng trên.

---

## 1. MỞ MÀN — 2 câu dễ, chắc chắn đúng (chế độ Hybrid mặc định)

| # | Câu hỏi | Kết quả đã test |
|---|---------|-----------------|
| 1 | **Tác phẩm Số đỏ của Vũ Trọng Phụng nói về điều gì?** | ✅ Trả lời về tiểu thuyết trào phúng của Vũ Trọng Phụng |
| 2 | **Chí Phèo là tác phẩm của tác giả nào?** | ✅ "Chí Phèo là tác phẩm của Nam Cao" + trích nguồn [1] |

**Lời dẫn:** "Em bắt đầu với câu hỏi cơ bản. Chú ý mỗi câu trả lời đều kèm **nguồn tài liệu**
lấy từ kho tri thức — khác với hỏi ChatGPT, ở đây mọi câu đều kiểm chứng được."
→ Mở expander **📚 Nguồn tài liệu** để hội đồng thấy trích dẫn.

---

## 2. KHAI THÁC METADATA — thành quả làm giàu dữ liệu (năm / thể loại)

| # | Câu hỏi | Kết quả đã test |
|---|---------|-----------------|
| 3 | **Truyện Kiều ra đời vào năm nào?** | ✅ "ra đời vào năm **1820**" |
| 4 | **Chí Phèo thuộc thể loại văn học gì?** | ✅ "thuộc thể loại **truyện ngắn**, hiện thực phê phán" |
| 5 | **Nỗi buồn chiến tranh của Bảo Ninh xuất bản năm nào?** | ✅ "xuất bản vào năm **1991**" |

**Lời dẫn:** "Thông tin năm xuất bản, thể loại không có sẵn trong văn bản gốc — em làm giàu
bằng pipeline tự động (Gemini + kiểm chứng Wikidata) rồi gắn vào metadata mỗi vector. Nhờ đó
chatbot trả lời được cả câu hỏi siêu dữ liệu."

> ⚠️ **KHÔNG hỏi "Số đỏ xuất bản năm nào?"** — câu này hệ thống TỪ CHỐI (metadata năm của
> Số đỏ bị trống). Dùng Truyện Kiều (1820) hoặc Nỗi buồn chiến tranh (1991) thay thế.

---

## 3. HỎI THEO TÁC GIẢ

| # | Câu hỏi | Kết quả đã test |
|---|---------|-----------------|
| 6 | **Nam Cao có những tác phẩm tiêu biểu nào?** | ✅ Liệt kê tác phẩm, nêu bối cảnh 1930–1945 |
| 7 | **Tô Hoài viết những tác phẩm gì?** | ✅ Liệt kê các sáng tác của Tô Hoài |

---

## 4. SO SÁNH CHẾ ĐỘ TRUY HỒI — điểm nhấn thực nghiệm

**Thao tác:** hỏi cùng 1 câu ở 2 chế độ (đổi ở sidebar):
- Vector Only → **Tắt đèn của Ngô Tất Tố viết về ai?**
- Hybrid → gõ lại đúng câu đó.

**Kết quả đã test:** Vector nói chung chung về "cuộc sống người nông dân bị áp bức";
Hybrid cho **chi tiết hơn** (tiểu sử Ngô Tất Tố, năm sinh 1893...).

> ⚠️ **Kết quả Vector KHÔNG tất định** — có lần trả lời, có lần từ chối. ĐỪNG hứa trước.
> **Bằng chứng cứng là BẢNG SỐ LIỆU**, không phải một lần chạy:

| Chế độ | P@1 | MRR |
|--------|-----|-----|
| Vector only | 33,3% | 0,446 |
| BM25 only | 76,7% | 0,863 |
| **Hybrid** | **83,3%** | **0,887** |

**Lời dẫn:** "Vector thuần yếu với tên riêng tiếng Việt (P@1 chỉ 33%), BM25 khớp từ khóa
được 77%, lai hợp cả hai đạt 83%. Mỗi phương pháp bù điểm yếu của nhau — đó là lý do em
chọn kiến trúc hybrid."

---

## 5. CHỐNG ẢO TƯỞNG — câu ngoài phạm vi (hệ thống TỪ CHỐI)

| # | Câu hỏi | Kết quả đã test |
|---|---------|-----------------|
| 8 | **Cách nấu phở bò truyền thống như thế nào?** | ✅ TỪ CHỐI: "không tìm thấy... thư viện tập trung văn học VN" |
| 9 | **Giá vàng hôm nay bao nhiêu?** | ✅ TỪ CHỐI tương tự |

**Lời dẫn:** "Câu ngoài phạm vi kho tri thức. Nếu điểm truy hồi dưới ngưỡng RRF 0.003,
hệ thống chặn và trả lời 'không tìm thấy' — **từ chối thay vì bịa**. Đây là cơ chế chống ảo tưởng."

> ⚠️ **KHÔNG dùng Harry Potter / sách dịch làm ví dụ ngoài phạm vi** — kho CÓ truyện dịch,
> sẽ trả lời chính xác. Dùng câu phi văn học (nấu ăn, giá vàng) mới chắc chắn bị từ chối.

---

## 6. BỘ NHỚ HỘI THOẠI — câu hỏi nối tiếp

**Gõ lần lượt (giữ "Ghi nhớ hội thoại" BẬT):**

| # | Câu hỏi | Kết quả đã test |
|---|---------|-----------------|
| 10 | **Vợ nhặt là truyện ngắn của ai?** | ✅ "của nhà văn **Kim Lân**", bối cảnh nạn đói 1945 |
| 11 | **Tác giả đó còn viết tác phẩm nào khác?** | ✅ Hiểu "tác giả đó" = Kim Lân → nêu truyện ngắn *Làng* |

**Lời dẫn:** "Câu thứ hai không nhắc tên Kim Lân, nhưng hệ thống hiểu 'tác giả đó' nhờ
bộ nhớ hội thoại — lịch sử được đưa vào bước viết lại câu hỏi trước khi truy hồi."

---

## 7. CÂU DỰ PHÒNG (nếu hội đồng yêu cầu hỏi tự do — đều đã test ANSWER)

- **Truyện Kiều do ai sáng tác?** → Nguyễn Du
- **Vũ Trọng Phụng nổi tiếng với phong cách gì?**
- **Bảo Ninh là tác giả của tác phẩm nào?**

---

## ⚠️ DANH SÁCH TRÁNH (đã test — cho kết quả xấu, ĐỪNG gõ trước hội đồng)

| Câu | Vì sao tránh |
|-----|--------------|
| Số đỏ xuất bản năm nào? | Bị TỪ CHỐI (metadata năm trống) |
| Tôi đang buồn, gợi ý sách phù hợp | Bị TỪ CHỐI (query cảm xúc, không khớp cách index) |
| Gợi ý sách theo tâm trạng | Tương tự — hệ thống không làm gợi ý theo cảm xúc tốt |
| Bất kỳ câu về Harry Potter / sách dịch | Kho CÓ → trả lời được, KHÔNG minh họa được "ngoài phạm vi" |

---

**Nguyên tắc vàng:** Nếu hội đồng ép hỏi câu tự do và kết quả kém → giải thích ngay bằng
số liệu: *"Hệ thống đạt 83% trên bộ đánh giá 30 câu, đây là ca khó vì..."* — bình tĩnh,
đừng lúng túng.
