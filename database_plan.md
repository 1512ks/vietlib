# Tái tổ chức Database & Làm giàu Metadata Sách bằng AI + Excel

Tài liệu này trình bày kế hoạch chi tiết để chuẩn hóa, xuất khẩu, bổ sung thông tin thiếu bằng AI (Gemini API) và tái nhập dữ liệu cho toàn bộ sách trong database phục vụ hệ thống RAG Chatbot.

---

## Tổng quan & Bối cảnh

Hệ thống hiện tại lưu trữ sách từ 3 nguồn chính trong thư mục `data/processed/`:
1. `work/`: Dữ liệu tác phẩm văn học Việt Nam từ Wikipedia (rất mỏng, hầu hết thiếu tác giả, năm xuất bản, nhà xuất bản, ảnh bìa).
2. `gbooks/`: Dữ liệu sách từ Google Books API (thiếu nhiều trường như năm xuất bản, nhà xuất bản, thể loại chuẩn, tóm tắt sơ sài hoặc tiếng Anh).
3. `archive_compact/`: Kho lưu trữ nén (chứa tóm tắt AI và độ dài từ).

Hiện tại, việc thiếu các trường metadata cốt lõi ảnh hưởng lớn đến chất lượng của cấu trúc Metadata Injection trong RAG (`build_knowledge_base.py`), khiến câu trả lời của chatbot thiếu chính xác khi người dùng hỏi về tác giả, năm sáng tác hoặc nhà xuất bản.

---

## Ý tưởng cốt lõi của giải pháp

1. **Chuẩn hóa Metadata Schema**: Định nghĩa một tập hợp các trường thông tin tiêu chuẩn cho một cuốn sách.
2. **Xuất khẩu hợp nhất (Export to Excel)**: Gộp các bản ghi sách từ cả 3 nguồn trùng khớp theo bộ đôi `(tên sách, tác giả)` để tránh trùng lặp. Mỗi dòng trong file Excel đại diện cho một tác phẩm độc nhất và lưu giữ danh sách các đường dẫn file gốc (`Source Paths`) để phục vụ việc cập nhật ngược lại.
3. **Làm giàu dữ liệu tự động bằng Gemini API (AI-filling)**: Viết một kịch bản Python tự động gọi Gemini API để điền các trường bị thiếu dựa trên tên sách và tác giả hiện có. Sử dụng tính năng **Google Search Grounding** (kết nối tìm kiếm thời gian thực của Gemini) để lấy chính xác các dữ liệu thực tế (như năm xuất bản, nhà xuất bản, ảnh bìa, tóm tắt chính xác).
4. **Nhập khẩu dữ liệu (Re-import)**: Đọc file Excel đã điền đủ thông tin, cập nhật trực tiếp vào các file JSON gốc được liệt kê trong cột `Source Paths`.
5. **Re-build Database**: Chạy lại pipeline `build_knowledge_base.py` để cập nhật dữ liệu mới lên Qdrant vector DB và BM25 index.

---

## Mẫu Metadata Sách tiêu chuẩn (Metadata Schema)

Mỗi cuốn sách sẽ được quản lý bằng các trường thông tin sau trong file Excel:

| Tên cột Excel | Khóa JSON tương ứng | Kiểu dữ liệu | Mô tả | Trạng thái hiện tại |
| :--- | :--- | :--- | :--- | :--- |
| **Book ID** | `id` | String | Mã băm duy nhất tạo từ `(title.lower() + author.lower())` | Có sẵn |
| **Tiêu đề** | `title` | String | Tên tác phẩm / Sách | Có sẵn |
| **Tác giả** | `author` | String | Tác giả tác phẩm (hỗ trợ điền nếu thiếu) | Một số bài bị rỗng |
| **Năm xuất bản** | `publication_year`| String | Năm xuất bản hoặc năm sáng tác đầu tiên | Thiếu rất nhiều (>80%) |
| **Thể loại** | `genre` | String | Thể loại văn học chuẩn (Tiểu thuyết, Truyện ngắn, Thơ...) | Thiếu nhiều hoặc không đồng nhất |
| **Nhà xuất bản** | `publisher` | String | Nhà xuất bản chính thức | Hầu như trống |
| **Số trang** | `page_count` | Integer | Số trang sách | Trống nhiều |
| **Mã ISBN** | `isbn` | String | Mã số ISBN | Trống nhiều |
| **Ảnh bìa** | `cover_url` | String | URL hình ảnh bìa sách | Trống nhiều |
| **Tóm tắt ngắn** | `summary` | String | Tóm tắt cốt truyện/nội dung chính (200-500 từ) | Nhiều bài bị tóm tắt cụt |
| **Nguồn dữ liệu** | `source` | String | Liệt kê các nguồn: `wikipedia, gbooks, archive_compact` | Có sẵn |
| **Đường dẫn file**| `source_paths` | String | Danh sách đường dẫn các file JSON gốc (phân tách bằng dấu `;`) | **Cực kỳ quan trọng để Re-import** |

---

## Chi tiết kế hoạch triển khai

Kế hoạch được chia làm 4 pha cụ thể sau:

### Pha 1: Xuất dữ liệu ra Excel chuẩn hóa (`export_books_excel.py`)
*   **Mục tiêu**: Quét toàn bộ thư mục `work/`, `gbooks/` và `archive_compact/`, gộp các thực thể sách trùng lặp dựa trên tên sách và tác giả, sau đó xuất ra file `data/books_metadata_raw.xlsx`.
*   **Logic thực hiện**:
    *   Đọc tất cả file JSON trong các thư mục tương ứng.
    *   Tạo khóa gom nhóm: `key = f"{title.lower()} | {author.lower()}"`.
    *   Tổng hợp thông tin từ tất cả các file có chung khóa. Lưu tất cả đường dẫn file gốc vào cột `source_paths` dưới dạng chuỗi nối nhau bằng dấu `;` (Ví dụ: `data/processed/work/page_123.json;data/processed/gbooks/gbooks_abc.json`).
    *   Dùng `openpyxl` tô màu nền màu vàng (Yellow Fill) cho các ô bị trống để trực quan hóa dữ liệu thiếu.
    *   In thống kê chi tiết về tỷ lệ điền đầy đủ (fill rate) của từng cột.

### Pha 2: Làm giàu dữ liệu tự động bằng Gemini API (`enrich_metadata_ai.py`)
*   **Mục tiêu**: Đọc file `data/books_metadata_raw.xlsx`, dùng Gemini API để tự động bổ sung thông tin các ô trống và ghi ra file `data/books_metadata_enriched.xlsx`.
*   **Logic thực hiện**:
    *   Sử dụng thư viện `google-generativeai` tích hợp sẵn trong môi trường, đọc khóa `GEMINI_API_KEY` từ file `.env`.
    *   Sử dụng model `gemini-2.5-flash` với cấu hình **Google Search Grounding** nhằm tìm kiếm thông tin chính xác trên internet (năm xuất bản, nhà xuất bản, ISBN, ảnh bìa).
    *   Gửi prompt chứa Tên sách, Tác giả và tóm tắt sơ bộ (nếu có) yêu cầu AI trả về kết quả dưới dạng cấu trúc JSON chuẩn.
    *   Kịch bản sẽ chạy theo lô (Batch Processing) và có cơ chế lưu trữ đệm (Checkpointing) để tránh mất dữ liệu khi bị gián đoạn hoặc gặp lỗi giới hạn API (Rate Limit).
    *   Hỗ trợ chế độ chạy thử nghiệm (`--limit N`) trên N cuốn sách để người dùng đánh giá chất lượng trước khi chạy toàn bộ.

### Pha 3: Cập nhật dữ liệu ngược lại DB (`import_books_excel.py`)
*   **Mục tiêu**: Đọc file `data/books_metadata_enriched.xlsx` đã được AI làm đầy thông tin, cập nhật ngược lại vào các file JSON gốc.
*   **Logic thực hiện**:
    *   Duyệt qua từng dòng trong file Excel.
    *   Đọc danh sách đường dẫn tại cột `source_paths`.
    *   Đối với mỗi đường dẫn file:
        *   Tải nội dung file JSON lên bộ nhớ.
        *   Cập nhật các trường thông tin tương ứng vừa được làm giàu từ Excel (chỉ ghi đè nếu dữ liệu mới có giá trị và tốt hơn).
        *   Lưu lại file JSON gốc dưới dạng UTF-8.

### Pha 4: Re-build Vector DB & BM25 Index
*   **Mục tiêu**: Cập nhật chỉ mục tìm kiếm để hệ thống RAG sử dụng dữ liệu mới ngay lập tức.
*   **Logic thực hiện**:
    *   Chạy lại script `build_knowledge_base.py`.
    *   Pipeline sẽ đọc các file JSON đã được làm giàu, sinh chuỗi metadata injection chi tiết hơn (ví dụ: `[Tiêu đề: Lũy Hoa] | [Tác giả: Nguyễn Huy Tưởng] | [Năm xuất bản: 1960] | [Thể loại: Kịch] | [Nhà xuất bản: NXB Văn học]`), sau đó tạo embedding và cập nhật lại lên Qdrant Cloud/Local và rebuild BM25 Index.

---

## Kế hoạch kiểm thử & Xác thực (Verification Plan)

### Thử nghiệm tự động
1.  **Kiểm tra tính toàn vẹn của File Excel**: Chạy thử script export để xác nhận file `processed_data_raw.xlsx` được tạo ra đúng cấu trúc, tô màu chuẩn xác và không bị lỗi Unicode.
2.  **Chạy thử nghiệm AI với quy mô nhỏ (Dry Run)**: Chạy thử `enrich_metadata_ai.py --limit 5` để kiểm tra kết quả trả về của Gemini API có khớp chính xác với sách thực tế không và định dạng JSON phản hồi của AI có ổn định không.
3.  **Kiểm thử Re-import**: Thực hiện import thử nghiệm một vài bản ghi, kiểm tra sự thay đổi của file JSON gốc (sử dụng `git diff` để kiểm tra trực tiếp các thay đổi).
4.  **Chạy script đánh giá**: Chạy lại `audit_coverage.py` để kiểm tra tỷ lệ phủ đầy dữ liệu mới sau khi import so với trước khi làm giàu.

### Xác thực thủ công
1.  Người dùng mở trực tiếp file `data/books_metadata_enriched.xlsx` để kiểm tra tính chính xác của thông tin do AI điền (như năm sáng tác, nhà xuất bản) trước khi thực hiện import.

---

## Ý kiến/Câu hỏi mở cần xác nhận từ người dùng

> [!IMPORTANT]
> Hãy xem xét các câu hỏi dưới đây trước khi phê duyệt kế hoạch triển khai:
> 1. **Phương pháp điền dữ liệu**: Bạn muốn dùng script Python tự động gọi Gemini API (như đề xuất ở Pha 2) hay muốn tự tải file Excel lên các giao diện Chatbot (ChatGPT/Claude) bên ngoài để làm thủ công từng phần? (Khuyến nghị dùng kịch bản Python tự động để xử lý nhanh và đồng bộ hơn).
> 2. **Phạm vi cập nhật ngược**: Khi import dữ liệu từ Excel về, có nên cập nhật đè tóm tắt sách (`summary`) mới từ AI lên toàn bộ sách hay chỉ cập nhật các trường metadata rỗng và giữ nguyên nội dung tóm tắt hiện tại đối với những cuốn đã có tóm tắt dài?
