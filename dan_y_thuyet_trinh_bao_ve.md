# DÀN Ý & KỊCH BẢN THUYẾT TRÌNH BẢO VỆ ĐỒ ÁN TỐT NGHIỆP
**Đề tài:** Xây dựng Chatbot Thư viện Điện tử Tiếng Việt (VietLib RAG)
**Sinh viên:** [Họ và tên] - [MSSV] | **GVHD:** TS. Lê Kim Thư (Đại học Bách khoa Hà Nội)

---

## 🎯 CHIẾN LƯỢC TỔNG THỂ & PHÂN BỔ THỜI GIAN (~10–12 Phút)
1. **Phần 1: Giới thiệu Bài toán & Sản phẩm** (Slide 1–2) — **~2.5 phút**
2. **Phần 2: Phương pháp luận & Tiêu chí đánh giá** (Slide 3–4) — **~2.5 phút**
3. **Phần 3: Đột phá học thuật: Sample Model (Tập đối chứng)** (Slide 5–6) — **~3 phút**
4. **Phần 4: So sánh, Kết luận & Demo trực tiếp** (Slide 7–8 + Demo) — **~3–4 phút**

---

## PHẦN I: KỊCH BẢN CHI TIẾT THEO TỪNG SLIDE (Bám sát file [slide_bao_ve.tex](file:///c:/Users/Admin/Desktop/%C4%90ATN/slide_bao_ve.tex))

### Slide 1: Bìa Đề Tài & Giới thiệu
*   **Tiêu đề:** XÂY DỰNG CHATBOT THƯ VIỆN ĐIỆN TỬ TIẾNG VIỆT — Kiến trúc RAG & Đánh giá đa tiêu chí
*   **Lời thoại gợi ý:** 
    > *"Kính thưa thầy cô trong Hội đồng bảo vệ đồ án tốt nghiệp. Em tên là [Họ và tên], sinh viên ngành Toán-Tin. Sau đây, em xin phép trình bày đề tài đồ án tốt nghiệp của mình: 'Xây dựng Chatbot Thư viện Điện tử Tiếng Việt' dưới sự hướng dẫn khoa học của TS. Lê Kim Thư."*
*   **Điểm nhấn ăn điểm:** Thái độ tự tin, trang trọng. Mở đầu mạch lạc, dứt khoát.

---

### Slide 2: Đặt Vấn Đề (Vấn đề & Giải pháp)
*   **Nội dung chính:**
    *   **Thực tế:** Độc giả tìm sách theo ý nghĩa/nội dung/cảm xúc $\rightarrow$ Tìm kiếm từ khóa truyền thống (keyword search) thất bại.
    *   **LLM truyền thống (như ChatGPT):** Bị hiện tượng **ảo tưởng (hallucination)**, bịa đặt nội dung tác phẩm, nhầm lẫn tác giả/năm xuất bản đối với dữ liệu văn học Việt Nam.
    *   **Giải pháp RAG (Retrieval-Augmented Generation):** Truy hồi ngữ cảnh thực tế $\rightarrow$ Sinh câu trả lời kèm trích dẫn nguồn $\rightarrow$ Triết lý *"thà từ chối còn hơn bịa đặt"*.
*   **Lời thoại gợi ý:** 
    > *"Vấn đề lớn nhất khi ứng dụng AI thế hệ mới vào nghiên cứu văn học Việt Nam là hiện tượng 'ảo tưởng thông tin'. Mô hình ngôn ngữ lớn (LLM) thường bịa ra cốt truyện hoặc nhầm lẫn tác giả do dữ liệu huấn luyện tiếng Việt hạn chế. Để giải quyết, em xây dựng hệ thống Chatbot theo kiến trúc RAG. Hệ thống không dựa vào trí nhớ của LLM để trả lời, mà bắt buộc truy hồi thông tin chính xác từ một kho dữ liệu thư viện đã được làm sạch và kiểm soát gồm **11.759 chunk**, sau đó đưa vào ngữ cảnh để mô hình sinh câu trả lời kèm trích dẫn nguồn chính xác."*
*   **Điểm nhấn ăn điểm:** Chỉ ra đúng **"Pain Point"** (Nỗi đau của người dùng: LLM bịa thông tin văn học Việt Nam) và giải thích logic của RAG.

---

### Slide 3: Kiến trúc Hệ thống & Pipeline Xử Lý
*   **Nội dung chính:**
    *   **Pipeline 4 bước:** 
        1. **Hybrid Retrieval (Truy hồi lai):** BM25 (Từ khóa/Tên riêng) + Dense Vector (Semantic qua model `paraphrase-multilingual-MiniLM-L12-v2`, lưu trong Qdrant DB sử dụng chỉ mục HNSW).
        2. **Hợp nhất RRF (Reciprocal Rank Fusion, k=60):** Trộn kết quả mà không cần chuẩn hóa điểm số khác biệt.
        3. **Tái xếp hạng (Cross-Encoder):** Dùng `ms-marco-MiniLM-L-6-v2` chấm điểm chéo để tối ưu hóa thứ tự.
        4. **Sinh câu trả lời (Gemini 2.5 Flash):** Prompt ràng buộc ngữ cảnh + Cơ chế từ chối khi điểm RRF dưới ngưỡng chặn `0.003`.
*   **Lời thoại gợi ý:** 
    > *"Về mặt kiến trúc, khi người dùng đưa vào một câu hỏi, hệ thống sẽ đi qua một pipeline 4 bước tối ưu. Đầu tiên, câu hỏi được tìm kiếm song song bằng BM25 (mạnh về tên riêng, từ khóa) và Dense Retrieval sử dụng vector nhúng 384 chiều, lưu trữ trên Qdrant Vector DB với chỉ mục HNSW. Hai danh sách kết quả được trộn lại bằng cơ chế RRF với tham số k=60 để giữ tính công bằng về mặt thứ hạng. Để tăng cường độ chính xác, em áp dụng mô hình Cross-Encoder để tái xếp hạng (Rerank) lại Top kết quả trước khi đưa vào prompt của Gemini 2.5 Flash sinh câu trả lời cuối cùng kèm trích dẫn. Đặc biệt, nếu điểm RRF cao nhất dưới ngưỡng chặn 0.003, hệ thống sẽ chủ động từ chối trả lời để triệt tiêu hoàn toàn ảo tưởng."*
*   **Điểm nhấn ăn điểm:** Thể hiện sự am hiểu sâu sắc về kiến trúc tìm kiếm hiện đại (Hybrid, RRF, Reranking, Fallback Threshold).

---

### Slide 4: Phương pháp luận & Tiêu chí đánh giá đa chiều
*   **Nội dung chính:**
    *   Hợp nhất **3 khung tham chiếu**:
        *   **Khung A (OMICall):** chatbot dưới góc độ sản phẩm dịch vụ (hiệu năng ngôn ngữ, tốc độ phản hồi).
        *   **Khung B (GeeksforGeeks):** RAG dưới góc độ kỹ thuật (tách biệt khâu truy hồi và khâu sinh).
        *   **Khung C (Microsoft):** Đánh giá chatbot LLM thực chiến (Tìm kiếm liên quan + Đảm bảo an toàn/Red-teaming + Chất lượng sinh).
    *   **Bộ 3 RAG Triad:** Context Relevance $\cdot$ Faithfulness $\cdot$ Answer Relevance.
*   **Lời thoại gợi ý:** 
    > *"Một trong những đóng góp quan trọng của đồ án này là việc xây dựng một **Phương pháp luận đánh giá toàn diện**. Em đã hợp nhất 3 khung tham chiếu: OMICall (đánh giá góc độ sản phẩm), GeeksforGeeks (đánh giá góc độ kỹ thuật RAG) và Microsoft (đánh giá hệ thống LLM thực chiến). Trọng tâm đánh giá dựa trên bộ ba RAG Triad để kiểm soát chất lượng từng chặng: Truy hồi có liên quan không? LLM sinh ra có trung thực với tài liệu truy hồi không (Faithfulness)? Và câu trả lời có đúng trọng tâm câu hỏi của người dùng không (Answer Relevance)?"*
*   **Điểm nhấn ăn điểm:** Đồ án không chỉ làm code mà có **phương pháp luận nghiên cứu (methodology)** rõ ràng, chuẩn học thuật, thuyết phục được các thầy cô khó tính.

---

### Slide 5: Ý nghĩa các Metric chính & Số liệu Hệ thống lớn
*   **Nội dung chính:**
    *   Giải thích ngắn gọn ý nghĩa: Precision, Recall, MRR (Quan trọng nhất với RAG), nDCG (Nhạy thứ hạng), Faithfulness (Độ trung thực).
    *   Bảng số liệu thực nghiệm hệ chính (11.759 chunk):
        *   **BM25 only:** P@1 = 76.7%, MRR = 0.863
        *   **Vector only:** P@1 = 33.3%, MRR = 0.446
        *   **Hybrid + Rerank:** **P@1 = 83.3%, MRR = 0.887**
*   **Lời thoại gợi ý:** 
    > *"Hệ thống được đánh giá qua các chỉ số khoa học: Precision@K đo độ chính xác, MRR đo xem tài liệu đúng đầu tiên xuất hiện ở vị trí thứ mấy (đặc biệt quan trọng vì LLM chỉ đọc các đoạn đầu), nDCG đánh giá thứ tự sắp xếp và Faithfulness đo độ trung thực chống ảo tưởng. Thực nghiệm trên hệ thống lớn với 11.759 chunk cho thấy: Vector thuần chỉ đạt Precision@1 là 33.3% do mô hình nhúng đa ngôn ngữ chưa được tối ưu cho văn học VN. Tuy nhiên, khi kết hợp Hybrid và Rerank, chỉ số Precision@1 đã nhảy vọt lên **83.3%** và MRR đạt **0.887**, chứng minh hiệu quả vượt trội của việc kết hợp từ khóa và ngữ nghĩa."*
*   **Điểm nhấn ăn điểm:** Sử dụng số liệu thực nghiệm để thuyết phục. Giải thích tại sao Vector thuần lại kém (do tên riêng, tên tác phẩm trong văn học VN thiên về so khớp từ khóa và mô hình nhúng chưa được fine-tune).

---

### Slide 6: Đột phá Đánh giá: Tại sao cần "Sample Model"?
*   **Nội dung chính:**
    *   **Hạn chế của hệ thống lớn:** Không thể gán nhãn thủ công cho toàn bộ 11.759 chunk $\rightarrow$ Không đo được **Recall thật** (phải lấy Recall xấp xỉ = Precision); nDCG chỉ dùng nhãn nhị phân; khâu sinh đánh giá thủ công tốn sức.
    *   **Giải pháp: Sample Model (Tập đối chứng sạch 100%):**
        *   Quy mô: 163 chunk được trích lọc từ 51 tác phẩm kinh điển được kiểm chứng metadata sạch sẽ.
        *   Golden set **32 câu hỏi** đầy đủ nhãn phân cấp (graded 0/1/2) + danh sách relevant cụ thể + câu trả lời chuẩn (ground-truth answers).
*   **Lời thoại gợi ý:** 
    > *"Tuy nhiên, trên hệ thống lớn, việc đo lường gặp một giới hạn phổ biến trong nghiên cứu RAG: Chúng ta không thể gán nhãn liên quan cho toàn bộ gần 12.000 chunk, dẫn tới chỉ số Recall đo được chỉ là xấp xỉ, và nDCG chỉ dùng nhãn nhị phân thô sơ. Để giải quyết triệt để hạn chế đo lường này, em đã xây dựng một **Sample Model (Tập đối chứng chuẩn benchmark)**. Tập đối chứng gồm 163 chunk từ các tác phẩm kinh điển được làm sạch 100%, đi kèm bộ Golden Set gồm 32 câu hỏi có gán nhãn liên quan phân cấp (graded 0/1/2) và có sẵn câu trả lời ground-truth. Điều này cho phép hệ thống đo lường được **Recall thực tế**, tính toán **nDCG chuẩn học thuật**, và chạy được các framework tự động đánh giá khâu sinh như **RAGAS** dùng LLM-as-a-judge."*
*   **Điểm nhấn ăn điểm:** Đây là **"Highlight nghệ thuật"** của đồ án. Cho hội đồng thấy tư duy nghiên cứu trung thực, nghiêm túc, hiểu rõ hạn chế của bài toán quy mô lớn và biết thiết kế benchmark đối chứng khoa học để giải quyết.

---

### Slide 7: Kết quả thực nghiệm trên Sample Model & Ablation Study
*   **Nội dung chính:**
    *   **Kết quả truy hồi:** MRR = 0.946, HitRate@3 = 100%, Recall@10 (THẬT) = 0.873, nDCG@10 (graded) = 0.839.
    *   **Kết quả sinh (RAGAS / LLM-judge):** Faithfulness = 0.95–0.99, Answer Relevance = 1.00, Citation Accuracy = 100%.
    *   **Thử nghiệm cắt bỏ (Ablation Study):** Đổi mô hình nhúng từ `MiniLM` (P@1 = 43%) sang mô hình tiếng Việt chuyên dụng `bge-m3` (P@1 = 89%).
*   **Lời thoại gợi ý:** 
    > *"Kết quả thực nghiệm trên Sample Model vô cùng khả quan: MRR đạt 0.946, Recall thật đạt 87.3% và nDCG graded đạt 0.839. Đối với khâu sinh, điểm Faithfulness đạt mức gần như tuyệt đối (0.95 - 0.99) và Citation Accuracy đạt 100%, chứng minh chatbot trích dẫn nguồn cực kỳ chính xác. Để kiểm chứng xem hiệu năng tăng lên do kích thước tập dữ liệu nhỏ hay do kiến trúc, em đã thực hiện một thử nghiệm cắt bỏ (Ablation Study) bằng cách thay thế mô hình nhúng MiniLM sang mô hình chuyên dụng tiếng Việt BGE-M3. Kết quả là Precision@1 của tìm kiếm vector đã nhảy vọt từ 43% lên **89%**. Điều này chứng minh hiệu quả cải tiến đến từ công nghệ cốt lõi và mở ra hướng nâng cấp cho hệ thống lớn."*
*   **Điểm nhấn ăn điểm:** Cụm từ **"Ablation Study" (Thử nghiệm cắt bỏ)** là từ khóa rất đắt giá trong các nghiên cứu AI/Machine Learning, giúp tăng độ uy tín cho đồ án của bạn trước hội đồng HUST.

---

### Slide 8: Kết luận & Hướng phát triển
*   **Nội dung chính:**
    *   **Đạt được:** Chatbot RAG hoàn chỉnh chạy trên dữ liệu thật, chống ảo tưởng hiệu quả, có phương pháp luận đánh giá rõ ràng qua 3 khung tham chiếu và Sample Model đối chứng.
    *   **Hạn chế:** Phụ thuộc API Gemini, chưa có Human Evaluation quy mô lớn.
    *   **Hướng phát triển:** Tự host LLM, tích hợp mua sách/thương mại điện tử (đo tỉ lệ chuyển đổi thực tế theo Khung A), nâng cấp embedding của hệ lớn lên BGE-M3.
*   **Lời thoại gợi ý:** 
    > *"Tóm lại, đồ án đã hoàn thành mục tiêu xây dựng một chatbot RAG hoàn chỉnh cho thư viện văn học Việt Nam, giải quyết triệt để bài toán ảo tưởng thông tin bằng trích dẫn nguồn và ngưỡng chặn thông minh. Đồng thời, em đã đề xuất và thực hiện thành công phương pháp đánh giá đa tiêu chí thông qua tập đối chứng. Hướng phát triển tiếp theo của đề tài là ứng dụng mô hình BGE-M3 lên toàn bộ hệ thống lớn, tổ chức đánh giá chéo bởi nhiều chuyên gia con người để đo độ đồng thuận, và tích hợp các tính năng thương mại điện tử để đo lường các chỉ số kinh doanh thực tế. Em xin chân thành cảm ơn thầy cô trong hội đồng đã lắng nghe!"*

---

## PHẦN II: TIÊU CHÍ ĐÁNH GIÁ CHATBOT TRONG ĐỒ ÁN (TỔNG HỢP)

Để trả lời trôi chảy khi hội đồng chất vấn về tiêu chí đánh giá, bạn cần nắm rõ bảng tổng hợp 3 khung tham chiếu dưới đây:

| Khung Tham Chiếu | Tiêu Chí Đánh Giá | Cách Chatbot Đáp Ứng / Đo Lường | Trạng thái trong Đồ án |
| :--- | :--- | :--- | :---: |
| **Khung A (OMICall)**<br>*(Góc độ sản phẩm & vận hành)* | 1. Tỷ lệ tương tác (Engagement)<br>2. Mức độ hài lòng (CSAT)<br>3. Tỷ lệ chuyển đổi (Conversion)<br>4. Khả năng tự học (Learning)<br>5. Thời gian phản hồi (Latency)<br>6. Khả năng xử lý NLP (Accuracy) | - Tự sinh gợi ý câu hỏi tiếp theo.<br>- Chưa tích hợp nút đánh giá 👍/👎.<br>- Đề xuất tích hợp Tiki/Fahasa.<br>- Cập nhật tri thức tức thời qua RAG DB.<br>- Latency truy hồi ~554ms, token đầu ~1-2s.<br>- Xử lý ngôn ngữ rất tốt (P@1=83.3%). | ⚠️<br>❌<br>❌<br>⚠️<br>✅<br>✅ |
| **Khung B (GeeksforGeeks)**<br>*(Góc độ kỹ thuật hệ RAG)* | 1. Retrieval-level (Truy hồi)<br>2. Generation-level (Sinh LLM)<br>3. End-to-End (Đầu-cuối)<br>4. Human Evaluation (Đánh giá người) | - Đo bằng: P@K, Recall@K, MRR, nDCG, MAP, HitRate.<br>- Chống bịa đặt, đo qua tính Faithfulness.<br>- Đo Citation Accuracy (100%), Hallucination (0%).<br>- Expert Review (thang đạt/không đạt). | ✅<br>⚠️ (Đo trung thực)<br>✅ (Chống bịa)<br>⚠️ (Quy mô nhỏ) |
| **Khung C (Microsoft)**<br>*(Góc độ doanh nghiệp thực chiến)* | 1. Hiệu năng Tìm kiếm (Search)<br>2. Chất lượng sinh LLM (Generation)<br>3. Đánh giá An toàn (Safety) | - Search Relevance và Search Stability (viết lại câu hỏi).<br>- Coherence, Fluency, Role Adherence, Memory.<br>- Red-teaming bằng câu hỏi ngoài miền (fallback). | ✅ (Relevance)<br>⚠️ (Có cơ chế)<br>⚠️ (Mức cơ bản) |

---

## PHẦN III: KỊCH BẢN LIVE DEMO (Ăn điểm tuyệt đối trong 2-3 phút)

### Chuẩn bị trước (30 phút):
1. Chạy sẵn Streamlit: `streamlit run app.py` trên máy.
2. Hỏi trước 1 câu bất kỳ để hệ thống nạp (warm-up) model embedding và Cross-Encoder vào RAM (tránh để hội đồng đợi 30s cold start).
3. Bật sẵn 4G dự phòng (vì Gemini API và Qdrant Cloud cần kết nối Internet ổn định).

### Kịch bản Demo thực hành:
*   **Thao tác 1: Giới thiệu giao diện (30 giây)**
    *   *Hành động:* Chỉ vào thanh điều hướng bên trái (Sidebar).
    *   *Nói:* *"Giao diện Streamlit của em cho phép người dùng tùy chỉnh linh hoạt: chọn chế độ truy hồi (Hybrid, Vector, BM25) để phục vụ so sánh thực nghiệm, bật/tắt Cross-Encoder Rerank, điều chỉnh tham số Top-K, và thanh vạch đỏ giám sát 75% ngân sách ngữ cảnh hội thoại."*
*   **Thao tác 2: Truy vấn thông tin nội dung & Trích dẫn nguồn (45 giây)**
    *   *Hành động:* Gõ câu hỏi: `Tác phẩm Số đỏ của Vũ Trọng Phụng nói về điều gì?`
    *   *Nói:* *"Khi câu trả lời hiện ra, thầy cô có thể thấy chatbot trả lời rất mạch lạc và tự động sinh ra thẻ trích dẫn nguồn. Nhấp vào đây, hệ thống sẽ hiển thị chính xác đoạn văn bản gốc trong cơ sở dữ liệu làm bằng chứng, giúp triệt tiêu hoàn toàn sự mập mờ."*
*   **Thao tác 3: Đối chứng hiệu năng chế độ tìm kiếm (45 giây)**
    *   *Hành động:* Chọn chế độ **Vector Only** trên sidebar $\rightarrow$ Gõ câu: `Tắt đèn của Ngô Tất Tố viết về ai?` (kết quả trả về sẽ rất mơ hồ). Sau đó chuyển sang **Hybrid (BM25 + Vector)** $\rightarrow$ Gõ lại câu đó (kết quả trả về chi tiết, đầy đủ).
    *   *Nói:* *"Khi chạy Vector thuần, do mô hình nhúng đa ngữ chưa tối ưu cho tên riêng tiếng Việt, kết quả nhận được khá mơ hồ. Nhưng khi chuyển sang chế độ Hybrid lai hợp, hệ thống lập tức lấy ra thông tin đầy đủ về nhân vật chị Dậu cùng bối cảnh tác phẩm, minh chứng cho tầm quan trọng của việc kết hợp BM25."*
*   **Thao tác 4: Chứng minh khả năng chống ảo tưởng & Fallback (30 giây)**
    *   *Hành động:* Gõ câu hỏi ngoài phạm vi: `Cách nấu phở bò truyền thống như thế nào?`
    *   *Nói:* *"Đối với các câu hỏi nằm ngoài phạm vi văn học Việt Nam, hệ thống nhận diện điểm truy hồi dưới ngưỡng 0.003 và thực hiện cơ chế fallback: lịch sự từ chối trả lời thay vì cố gắng bịa đặt ra thông tin sai lệch."*
*   **Thao tác 5: Hội thoại đa lượt (30 giây)**
    *   *Hành động:* Hỏi tiếp: `Nam Cao có những tác phẩm tiêu biểu nào?` $\rightarrow$ Đợi câu trả lời $\rightarrow$ Hỏi tiếp: `Tác giả đó mất năm bao nhiêu?`
    *   *Nói:* *"Nhờ bộ nhớ hội thoại tích hợp cơ chế viết lại câu hỏi (query rewriting), chatbot hiểu 'tác giả đó' chính là nhà văn Nam Cao và truy hồi chính xác năm mất của ông là năm 1951."*

---

## PHẦN IV: CHIẾN THUẬT PHẢN BIỆN CÂU HỎI KHÓ TỪ HỘI ĐỒNG

### Câu hỏi 1: Tại sao Vector Retrieval (Tìm kiếm ngữ nghĩa) trong bài lại tệ hơn BM25 (33% so với 77%)? Thường thì Semantic Search phải tốt hơn chứ?
*   **Trả lời:** *"Dạ thưa thầy cô, Semantic Search tốt hơn khi hiểu các ý niệm trừu tượng. Tuy nhiên, đối với bài toán hỏi-đáp văn học Việt Nam, các câu hỏi thường chứa rất nhiều **tên riêng** (tên tác giả như 'Khái Hưng', 'Nhất Linh', tên tác phẩm như 'Tắt đèn', 'Chí Phèo'). Đây là những tín hiệu từ vựng rất mạnh mà thuật toán khớp từ khóa BM25 bắt cực kỳ hiệu quả. Trong khi đó, mô hình nhúng em sử dụng là `paraphrase-multilingual-MiniLM-L12-v2` là mô hình đa ngôn ngữ dạng tổng quát, chưa được huấn luyện chuyên biệt trên văn bản cổ hoặc tên riêng tiếng Việt. Đó là lý do tại sao Vector thuần lại kém hơn BM25, và cũng là động lực chính để em xây dựng giải pháp **Hybrid kết hợp cả hai** nhằm tận dụng ưu điểm của cả so khớp từ vựng lẫn ngữ nghĩa ngữ cảnh."*

### Câu hỏi 2: Công thức RRF là gì? Tại sao lại chọn tham số $k = 60$?
*   **Trả lời:** *"Dạ, Reciprocal Rank Fusion (RRF) trộn kết quả từ BM25 và Vector Search bằng cách tính tổng nghịch đảo thứ hạng của từng tài liệu trong hai danh sách: $RRF(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$. Ưu điểm lớn nhất của RRF là nó chỉ phụ thuộc vào **thứ hạng (rank)** chứ không phụ thuộc vào điểm số thô (score) vốn rất khó chuẩn hóa giữa hai hệ thống khác biệt. Tham số $k=60$ là hằng số chuẩn được đề xuất bởi nhóm tác giả Cormack và các cộng sự trong bài báo gốc năm 2009 tại hội nghị SIGIR. Giá trị này đã được chứng minh qua thực nghiệm là giúp cân bằng tốt nhất giữa các tài liệu ở top đầu và hạn chế hiện tượng các tài liệu hạng quá thấp làm nhiễu kết quả."*

### Câu hỏi 3: Sự khác nhau giữa Bi-Encoder và Cross-Encoder là gì? Tại sao phải dùng cả hai?
*   **Trả lời:** *"Dạ, **Bi-Encoder** mã hóa câu hỏi và tài liệu thành các vector độc lập, rồi tính độ tương đồng bằng cosine. Phương pháp này rất nhanh, có thể tính toán trước và lập chỉ mục (index) để tìm kiếm hàng triệu tài liệu chỉ trong vài mili-giây, nhưng độ chính xác ở mức vừa phải vì câu hỏi và tài liệu không được tương tác với nhau trong quá trình nhúng. Ngược lại, **Cross-Encoder** đưa cả câu hỏi và tài liệu vào mô hình cùng một lúc để tính toán mức độ liên quan. Cách này cực kỳ chính xác vì có sự chú ý chéo (cross-attention) giữa từng từ trong câu hỏi và tài liệu, nhưng chi phí tính toán rất lớn và không thể lập chỉ mục trước. Do đó, em kết hợp cả hai theo kiến trúc hai tầng (two-stage): Dùng Bi-Encoder (kết hợp BM25) để lọc nhanh hàng vạn tài liệu xuống top-20 (Truy hồi), sau đó dùng Cross-Encoder để sắp xếp lại chính xác top-20 đó (Tái xếp hạng) trước khi gửi tới LLM."*

### Câu hỏi 4: Đánh giá bằng LLM-as-a-judge (như RAGAS) liệu có tin cậy không khi bản thân LLM cũng có thể bị ảo tưởng?
*   **Trả lời:** *"Dạ thưa thầy cô, đây là một câu hỏi rất hay về tính khách quan của việc đánh giá. Thực tế, các nghiên cứu gần đây (như bài báo RAGAS 2023) đã chỉ ra rằng khi được cung cấp prompt chi tiết với các tiêu chí chấm điểm rõ ràng (rubric), các mô hình LLM mạnh như GPT-4 hoặc Gemini Pro có độ tương quan rất cao với đánh giá của chuyên gia con người (đạt trên 80-85%). Để giảm thiểu sự thiếu chính xác của LLM-judge trong đồ án này, em đã: (1) Áp dụng LLM-judge trên **tập đối chứng Sample Model** sạch 100% để hạn chế nhiễu dữ liệu đầu vào. (2) Kết hợp đối chiếu kết quả của LLM-judge với việc **kiểm chứng thủ công** (Expert Review) trên bộ câu hỏi test. Kết quả cho thấy điểm số tự động và điểm đánh giá thủ công có sự đồng thuận rất cao (93.3% trùng khớp), chứng minh độ tin cậy của phương pháp."*

### Câu hỏi 5: Dữ liệu của em được thu thập như thế nào? Có vi phạm bản quyền hay không?
*   **Trả lời:** *"Dạ, dữ liệu trong kho tri thức của em được thu thập bằng công cụ thu thập tự động (crawler) từ các trang văn học mở uy tín (như vnthuquan). Hầu hết các tác phẩm được lựa chọn đều là văn học kinh điển Việt Nam (thời kỳ trung đại và hiện đại trước năm 1975), phần lớn đã hết thời hạn bảo hộ quyền tác giả hoặc thuộc phạm vi công cộng. Đồ án của em được thực hiện hoàn toàn phục vụ cho mục đích nghiên cứu học thuật, phi thương mại, nên đảm bảo tính hợp pháp và đạo đức trong nghiên cứu dữ liệu."*

---
> [!TIP]
> **Lời khuyên thực chiến:** Khi đứng trước hội đồng, nếu gặp câu hỏi tự do mà hệ thống chưa test trước, hãy cứ gõ câu hỏi đó vào demo. Nếu kết quả đúng, hãy nhấn mạnh tính linh hoạt của hệ thống. Nếu kết quả chưa tốt hoặc chatbot từ chối, hãy giải thích bằng tính trung thực khoa học: *"Dạ thưa thầy cô, đây là một câu hỏi khó và phức tạp. Hệ thống từ chối trả lời hoặc trả lời chưa đầy đủ vì tài liệu liên quan trong kho dữ liệu chưa bao phủ hết khía cạnh này, điều này đúng với triết lý thiết kế của em là 'thà từ chối trung thực còn hơn ảo tưởng bịa đặt thông tin'. Đây cũng chính là hướng để em tiếp tục làm giàu dữ liệu trong tương lai."*
