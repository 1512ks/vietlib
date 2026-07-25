# CẨM NANG GIẢI TRÌNH PHẢN HỒI CỦA GIÁO VIÊN HƯỚNG DẪN
*(Tài liệu bỏ túi chuẩn bị cho buổi bảo vệ Đồ án tốt nghiệp)*

Tài liệu này được biên soạn dựa trên các câu hỏi chất vấn thực tế của Giáo viên hướng dẫn (GVHD). Hãy đọc kỹ, nắm vững các số liệu cốt lõi và lập luận dưới đây để tự tin trả lời trước Hội đồng bảo vệ.

---

## ❓ CÂU 1: Tại sao phải dùng mô hình ngôn ngữ lớn (LLM - Gemini 2.5 Flash) trong khi đề tài này có thể làm tốt với một mô hình ngôn ngữ bé (SLM)? Hãy chứng minh độ tốt của nó.

### Lập luận bảo vệ (Chọn 1 trong 3 ý chính để nói, hoặc trình bày cả 3):

1. **Khả năng tuân thủ ràng buộc nghiêm ngặt (System Prompt/Instruction Adherence):**
   - **Bản chất RAG:** Đầu ra của RAG bắt buộc phải neo giữ (grounded) trên ngữ cảnh được truy hồi. Nếu ngữ cảnh thiếu, mô hình phải từ chối trả lời thay vì tự suy diễn (ảo tưởng).
   - **So sánh LLM vs SLM:** Các mô hình ngôn ngữ nhỏ (SLM < 10B parameters như PhoGPT-4B, Llama-3-8B) thường rất kém trong việc tuân thủ các System Prompt dài và phức tạp. Chúng có xu hướng bỏ qua các ràng buộc "không được bịa đặt" và tự động sinh câu trả lời sai lệch dựa trên tri thức cũ trong trọng số của chúng. Gemini 2.5 Flash tuân thủ prompt cực kỳ nghiêm ngặt, giúp tỷ lệ trích dẫn chính xác đạt **100%** trong thực nghiệm.
2. **Xử lý ngữ cảnh hội thoại đa lượt phức tạp:**
   - Hệ thống có chức năng viết lại câu hỏi (`Query Rewriting`) để chuyển các câu hỏi nối tiếp có chứa đại từ (ví dụ: *"Tác giả đó còn viết gì khác?"*) thành câu truy vấn độc lập chứa thực thể cụ thể (ví dụ: *"Kim Lân còn viết gì khác?"*).
   - Tác vụ này đòi hỏi năng lực hiểu ngữ cảnh sâu sắc và liên kết đại từ ngữ pháp tiếng Việt rất phức tạp. Các SLM thường viết lại câu hỏi bị sai thực thể hoặc làm mất ngữ nghĩa gốc, dẫn đến khâu truy hồi phía sau bị hỏng hoàn toàn.
3. **Hiệu năng tóm tắt lịch sử (Context Budgeting):**
   - Khi hội thoại dài vượt quá ngân sách (20.000 token), hệ thống tự động tóm tắt các lượt cũ. LLM lớn có thể nén hội thoại cực kỳ súc tích mà vẫn giữ nguyên các thực thể quan trọng (tên sách, tác giả). SLM dễ bị lỗi "quên thảm họa" hoặc làm mất các danh từ riêng quan trọng khi tóm tắt tiếng Việt.
4. **Chi phí hạ tầng và tính khả thi triển khai thực tế:**
   - Để chạy một SLM cục bộ (như PhoGPT) với độ trễ thấp và phục vụ được nhiều người dùng đồng thời, hệ thống đòi hỏi GPU chuyên dụng đắt tiền (VRAM ≥ 16GB). Điều này không khả thi cho một đồ án tốt nghiệp của sinh viên khi triển khai công khai (deploy cloud) trên các nền tảng miễn phí như Streamlit Cloud.
   - Gemini API giải quyết được bài toán hiệu năng vượt trội của mô hình lớn, hỗ trợ tiếng Việt xuất sắc, hoàn toàn miễn phí (free tier) và tốc độ phản hồi nhanh (streaming token đầu chỉ mất 1-2s).
5. **Tính độc lập của kiến trúc (Modular Decoupling):**
   - Kiến trúc hệ thống được thiết kế hướng module phân lớp. Lớp Sinh (Generation Layer) giao tiếp qua API độc lập. Do đó, RAG của đồ án không bị khóa chặt vào Gemini. Trong tương lai, khi các SLM chạy local đủ mạnh và nhẹ, ta hoàn toàn có thể thay thế Gemini bằng SLM local mà không cần thay đổi cấu trúc Search Pipeline hay Vector DB. Đây là một hướng phát triển tương lai khả thi đã được nêu trong báo cáo.

---

## ❓ CÂU 2: Phương pháp luận đánh giá chatbot dạng RAG là gì? Sử dụng những Metric nào để đo đạc?

### 1. Phương pháp luận: Bộ ba đánh giá RAG (RAG Triad)
Chúng ta đánh giá hệ thống RAG dựa trên 3 mối quan hệ cốt lõi tạo thành một tam giác khép kín:
*   **Context Relevance (Sự liên quan của ngữ cảnh):** Đánh giá khâu **Truy hồi (Retrieval)**. Đo lường xem tài liệu lấy ra có thực sự liên quan và chứa câu trả lời cho câu hỏi không.
*   **Groundedness / Faithfulness (Tính trung thực):** Đánh giá khâu **Sinh (Generation)**. Đo lường xem câu trả lời của LLM có hoàn toàn căn cứ vào ngữ cảnh truy hồi được hay không (có bịa đặt thông tin nằm ngoài tài liệu không).
*   **Answer Relevance (Sự liên quan của câu trả lời):** Đánh giá khâu **Sinh (Generation)**. Đo lường xem câu trả lời cuối cùng có giải quyết trực tiếp và chính xác câu hỏi của người dùng hay không.

### 2. Các Metric đánh giá cụ thể trong đồ án:
*   **Đánh giá định lượng khâu Truy hồi:** Đo đạc trên bộ dữ liệu chuẩn (Golden Dataset) gồm 30 câu hỏi mẫu được gán nhãn thủ công (ground truth):
    *   **Precision@K (Độ chính xác tại K):** Đo tỷ lệ tài liệu liên quan trong top K kết quả trả về.
    *   **Recall@K (Độ phủ tại K):** Đo tỷ lệ tài liệu liên quan được truy hồi thành công so với toàn bộ tài liệu liên quan hiện có trong kho.
    *   **MRR (Mean Reciprocal Rank - Thứ hạng nghịch đảo trung bình):** Đo lường xem tài liệu đúng nhất được xếp ở vị trí thứ mấy. MRR càng gần 1 chứng tỏ tài liệu đúng nhất luôn được xếp lên đầu, giúp tối ưu hóa ngữ cảnh đưa vào LLM. **(Hybrid = 0.887)**
    *   **nDCG@K (Normalized Discounted Cumulative Gain):** Độ đo *nhạy thứ hạng*, thưởng cho việc đưa tài liệu liên quan lên sớm trong danh sách. **(Hybrid nDCG@10 = 0.90, cao nhất — BM25 0.89, Vector 0.52).**
    *   **MAP@K (Mean Average Precision):** Độ chính xác trung bình trên nhiều truy vấn, phản ánh chất lượng xếp hạng tổng thể. **(Hybrid MAP@10 = 0.84, cao nhất).**
    *   **Hit Rate@K (Tỷ lệ trúng):** Tỷ lệ truy vấn có ít nhất 1 tài liệu liên quan trong top-K. **(Hybrid & BM25 HitRate@5 = 100%, Vector chỉ 63%).**
    *   *Lưu ý nếu bị hỏi sâu:* Em **không dùng BLEU/ROUGE/METEOR** vì đó là metric so khớp đáp án tham chiếu (reference-based), không phù hợp bài toán sinh câu trả lời mở tiếng Việt không có "đáp án vàng"; thay vào đó em đo trực tiếp Groundedness/Hallucination/Citation. Hướng mở rộng: **RAGAS** và **LLM-as-a-judge** để tự động hóa đánh giá khâu sinh.
*   **Đánh giá định lượng & định tính khâu Sinh:** Đo đạc trên bộ 15 kịch bản kiểm thử (Test Cases) đa dạng (Factual, Author, Semantic, Hard cases, Fallback cases):
    *   **Tỷ lệ vượt qua (Pass Rate):** Đánh giá **tự động** bằng heuristic (đối khớp từ khóa + phát hiện trích dẫn/từ chối) đạt **93.3% (14/15)**. Đánh giá **thủ công** theo tiêu chí trung thực & dẫn nguồn đạt **100% (15/15)**. Chênh lệch nằm ở 1 ca cảm xúc mơ hồ mà hệ thống *từ chối lịch sự* → auto-test tính trượt vì thiếu trích dẫn, nhưng con người coi đây là hành vi an toàn đúng chuẩn (không bịa đặt).
    *   **Citation Accuracy (Độ chính xác trích dẫn):** Tỷ lệ các trích dẫn nguồn `[n]` có đúng với tài liệu ngữ cảnh tương ứng không (Đạt **100%**, không có trích dẫn sai).
    *   **Tỷ lệ từ chối đúng (Fallback Rate):** Đánh giá khả năng từ chối đối với các câu hỏi ngoài miền (One Piece, giá vàng, cách nấu ăn...) để đảm bảo hệ thống không ảo tưởng.

---

## ❓ CÂU 3: Hãy tự đánh giá chatbot của mình (Ưu điểm & Hạn chế thực tế là gì)?

Hãy đưa ra các con số thực tế từ kết quả thực nghiệm của đồ án để tăng tính thuyết phục:

### 1. Ưu điểm (Thành quả đạt được):
*   **Thuật toán lai hợp (Hybrid) hoạt động cực tốt:** Kết quả thực nghiệm chứng minh Precision@1 của Vector thuần rất thấp (**33.3%**) vì mô hình nhúng MiniLM chưa tối ưu tiếng Việt. BM25 thuần đạt **76.7%** nhờ đối khớp từ khóa tốt. Khi lai hợp Hybrid kết hợp tái xếp hạng Cross-Encoder, độ chính xác đạt **83.3%** và MRR đạt **0.887**. Điều này chứng minh thuật toán kết hợp RRF và Reranker bù trừ khuyết điểm cho nhau rất tốt.
*   **Chống ảo tưởng 3 lớp mạnh mẽ:** Nhờ cơ chế lọc ngưỡng điểm RRF (`RELEVANCE_THRESHOLD = 0.003`), prompt hệ thống nghiêm ngặt và yêu cầu trích dẫn bắt buộc, chatbot đạt 100% tính an toàn (không bịa đặt thông tin) và trích dẫn chính xác nguồn gốc.
*   **Bộ nhớ hội thoại thông minh và kiểm soát token:** Hiểu các câu hỏi ngắn, câu hỏi nối tiếp đa lượt nhờ cơ chế viết lại câu (Query Rewriting). Cơ chế tóm tắt lịch sử giúp kiểm soát ngân sách token luôn nằm trong giới hạn 20.000 token, tránh phình to và tăng chi phí/độ trễ.
*   **Tối ưu hóa độ trễ cảm nhận:** Tích hợp streaming, nạp sẵn mô hình (warm-up) ở pha khởi tạo và bộ nhớ đệm nhiều tầng (LRU exact match + cache pool search) giúp giao diện Streamlit phản hồi cực kỳ nhanh nhạy.

### 2. Hạn chế (Điểm cần cải tiến):
*   **Mô hình nhúng ngữ nghĩa (Vector embedding) còn yếu:** MiniLM-L12-v2 hỗ trợ đa ngữ nhưng biểu diễn ngữ nghĩa tiếng Việt chưa sâu, dẫn đến tỷ lệ vector thuần chỉ đạt 33.3% Precision@1. Hệ thống hiện tại đang phụ thuộc nhiều vào BM25 để "gánh" các câu hỏi chứa tên riêng/tên sách.
*   **Quy mô bộ dữ liệu đánh giá còn nhỏ:** Bộ golden dataset mới chỉ có 30 câu hỏi truy hồi và 15 kịch bản chatbot, chưa phản ánh đầy đủ mọi tình huống sử dụng thực tế.
*   **Phụ thuộc vào API bên ngoài:** Hệ thống phụ thuộc hoàn toàn vào API Gemini của Google. Nếu mất mạng hoặc API quá tải, chatbot sẽ ngừng hoạt động.
*   **Một số trường siêu dữ liệu bị thiếu hoặc chưa chính xác:** Ví dụ năm xuất bản của các sách tái bản bị lẫn với năm sáng tác gốc, một số cuốn sách thiếu thông tin do Google Books không trả về và Gemini tra cứu web chưa ra.

---

## ❓ CÂU 4: Làm thế nào để chứng minh ứng dụng của bạn là "Human-centric" (Hướng con người)?

### Triết lý cốt lõi: 
*"Thiết kế ứng dụng xuất phát từ việc thấu hiểu và giải quyết triệt để những nỗi đau (pain points) thực tế của độc giả trong cuộc sống, chứ không chỉ là phô diễn công nghệ AI."*

### 5 bằng chứng chứng minh tính Human-centric của ứng dụng:

1.  **Giải quyết nỗi đau "Quên tên sách/tác giả" bằng Tìm kiếm ngữ nghĩa (Semantic Search):**
    *   *Nỗi đau:* Trong thực tế, độc giả thường chỉ nhớ mang máng cốt truyện, chủ đề hoặc trạng thái cảm xúc của mình lúc đó (ví dụ: *"tôi đang buồn và muốn đọc một cuốn sách cô đơn"*, *"tìm truyện ngắn về người nông dân nghèo trước cách mạng"*). Các hệ thống tìm kiếm từ khóa truyền thống của thư viện sẽ trả về "Không tìm thấy", gây ức chế.
    *   *Giải pháp:* Chatbot hỗ trợ tìm kiếm ngữ nghĩa, hiểu được câu hỏi cảm xúc và mô tả nội dung tự nhiên để gợi ý chính xác tác phẩm phù hợp (Lão Hạc, Tắt đèn, Buồn...).
2.  **Giải quyết nỗi đau "Quá tải thông tin" bằng RAG tổng hợp kèm trích dẫn trực quan:**
    *   *Nỗi đau:* Khi tìm kiếm tài liệu trên Google, người dùng nhận được hàng chục đường link rời rạc. Họ phải tự mở từng tab, tự đọc lướt và chắt lọc thông tin để tự tổng hợp câu trả lời.
    *   *Giải pháp:* Chatbot đọc hiểu toàn bộ ngữ cảnh tài liệu, tự động so sánh, đối chiếu và tổng hợp thành một câu trả lời cô đọng, mạch lạc, đồng thời hiển thị nguồn rõ ràng để người dùng chỉ cần click là xem ngay được trích đoạn gốc, giúp tiết kiệm tối đa thời gian.
3.  **Bảo vệ lòng tin độc giả bằng cơ chế Chống ảo tưởng nghiêm ngặt:**
    *   *Nỗi đau:* Người dùng rất sợ các chatbot AI thông thường (như ChatGPT) "bịa đặt" nội dung tác phẩm hoặc trích dẫn sai sách, gây ảnh hưởng đến chất lượng nghiên cứu học thuật.
    *   *Giải pháp:* Ứng dụng đặt tính trung thực lên hàng đầu. Với cơ chế lọc ngưỡng RRF, chatbot chọn giải pháp *"thà từ chối trả lời còn hơn trả lời sai"*. Người dùng hoàn toàn tin tưởng vào câu trả lời vì mọi thông tin đều được kiểm chứng và có nút hiển thị trích đoạn văn bản gốc tương ứng.
4.  **Tối ưu hóa Trải nghiệm tương tác (UX) mượt mà:**
    *   *Nút câu hỏi gợi ý (Suggested Questions):* Hệ thống tự động sinh ra các câu hỏi tiếp theo dựa trên nội dung vừa trả lời. Điều này giúp định hướng người dùng khám phá tiếp chủ đề một cách tự nhiên mà không cần suy nghĩ xem nên gõ gì tiếp theo.
    *   *Streaming & Warm-up:* Người dùng không phải chờ đợi 6-8 giây trong vô vọng. Chữ được gõ ra màn hình thời gian thực giúp giảm độ trễ cảm nhận.
    *   *Context Bar minh bạch:* Hiển thị rõ ràng tài nguyên token đang sử dụng, giúp người dùng hiểu cơ chế hoạt động của chatbot.
5.  **Khép kín hành trình trải nghiệm bằng Định hướng Thương mại điện tử (Conversational Commerce):**
    *   *Nỗi đau:* Sau khi tìm được sách hay từ AI, người dùng phải tự copy tên sách, mở tab mới lên các sàn thương mại điện tử để tìm mua hoặc tìm ebook đọc. Mạch trải nghiệm bị chia cắt.
    *   *Giải pháp:* Chatbot định hướng tương lai tích hợp trực tiếp lớp siêu dữ liệu thương mại. Ngay sau khi giới thiệu sách, chatbot hiển thị luôn các thẻ mua sách, so sánh giá đa sàn (Tiki, Fahasa, Shopee), nút mua hoặc đọc thử ebook online trực tiếp, khép kín hoàn toàn hành trình khám phá và mua sắm trong một giao diện duy nhất.
