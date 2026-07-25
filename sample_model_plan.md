# KẾ HOẠCH: SAMPLE MODEL — Mini-RAG chuẩn benchmark cho bảo vệ

## Mục tiêu
Xây một hệ RAG **thu nhỏ, dữ liệu sạch 100%, có ground-truth ĐẦY ĐỦ**, để đo được **TẤT CẢ tiêu chí đánh giá một cách chuẩn xác và tái lập** — làm bản demo đối chứng "hoàn hảo" bên cạnh hệ thống lớn (11.759 chunk, dữ liệu nhiễu).

### ⚠️ Nguyên tắc trung thực (đọc trước khi làm)
Sample model được trình bày như **"tập đối chứng có nhãn đầy đủ" (controlled benchmark)**, KHÔNG nói đây là hiệu năng hệ thống thật trên toàn corpus. Giá trị của nó là **đo chuẩn + tái lập được + có cả ca khó/ca từ chối**, chứ không phải "làm đẹp số 100%". Golden set BẮT BUỘC có ca khó và ca ngoài miền để chứng minh hệ thống xử lý đúng — hội đồng tôn trọng benchmark trung thực hơn là điểm tuyệt đối đáng ngờ.

### Sample model này SỬA được 3 hạn chế đang bị flag ở hệ lớn
| Hạn chế hệ lớn | Sample model khắc phục |
|---|---|
| Recall chỉ xấp xỉ = Precision (thiếu tập relevant đầy đủ) | Corpus nhỏ → gán được **FULL relevant set** cho mỗi câu → **Recall THẬT** |
| nDCG dùng nhãn nhị phân (chưa chuẩn) | Gán **graded relevance (0/1/2)** → nDCG, MAP chuẩn học thuật |
| Khâu sinh chỉ đo thủ công | Có **ground-truth answers** → chạy được **RAGAS** (Faithfulness, Answer/Context) |

---

## Phạm vi dữ liệu (nhỏ + đầy đủ + sạch)
- **12–15 tác phẩm kinh điển Việt Nam**, metadata đã kiểm chứng (tên/tác giả/năm/thể loại ĐÚNG — dùng nguồn tin cậy, tránh lỗi năm/đảo tên đã biết từ Google Books).
  - Gợi ý: Chí Phèo, Lão Hạc, Tắt đèn, Số đỏ, Truyện Kiều, Dế Mèn phiêu lưu ký, Vợ nhặt, Nỗi buồn chiến tranh, Đất rừng phương Nam, Vang bóng một thời, Tôi thấy hoa vàng trên cỏ xanh, Cho tôi xin một vé đi tuổi thơ...
- Mỗi tác phẩm: **1 tóm tắt sạch + 3–6 đoạn trích chính** → tổng ~**100–150 chunk** (sentence-window chunking).
- Đủ nhỏ để kiểm soát toàn bộ, đủ đa dạng để cover mọi loại câu hỏi.

## Golden test set (điểm mấu chốt)
- **25–30 truy vấn**, cân bằng 5 nhóm: Factual · Author · Semantic/cảm xúc · Đa lượt (multi-turn) · **Ngoài miền (fallback)**.
- Mỗi truy vấn gắn: **graded relevance (0/1/2)** + **danh sách relevant đầy đủ** + (với ~15 câu) **câu trả lời chuẩn (ground-truth answer)**.

---

## Các giai đoạn thực hiện

### Phase 0 — Thiết kế & chốt danh mục *(~0.5 ngày)*
- Chốt 12–15 tác phẩm; lập bảng metadata đã kiểm chứng (title, author, year, genre).

### Phase 1 — Xây corpus sạch *(~1 ngày)*
- Soạn/chuẩn hóa nội dung → chunk (sentence-window) → gán metadata.
- Lưu `sample_model/corpus/` (JSON: id, text, title, author, year, genre).

### Phase 2 — Golden set có nhãn *(~1 ngày)*
- Viết 25–30 query + graded labels + full relevant set + 15 ground-truth answers.
- Lưu `sample_model/golden/queries.json`.

### Phase 3 — Index & pipeline *(~0.5 ngày)*
- Nhúng (corpus nhỏ nên **thử luôn Vietnamese_Embedding bge-m3** cũng chỉ ~1–2 phút — cơ hội chứng minh embedding tiếng Việt tốt hơn MiniLM ngay trên sample).
- Tạo collection Qdrant riêng `sample_lit` + BM25 index riêng → **không đụng hệ thống thật**.

### Phase 4 — Đo lường đầy đủ *(~0.5 ngày)*
- **Retrieval:** Precision@K, **Recall@K (thật)**, F1, MRR, **nDCG (graded)**, MAP, HitRate → tái dùng `search/evaluator.py` (mở rộng đọc graded label + full relevant set).
- **Generation:** Pass, Citation, Hallucination + **RAGAS** (Faithfulness, Answer Relevance, Context Precision/Recall).
- Xuất bảng + JSON vào `sample_model/results/`.

### Phase 5 — Human-centric demo *(~1 ngày, tùy chọn nhưng ăn điểm)*
- Trang Streamlit demo riêng: **Confidence meter** (từ điểm rerank), **highlight đoạn nguồn**, **từ chối lịch sự + gợi ý** cho câu ngoài miền.

### Phase 6 — Đóng gói bảo vệ *(~0.5 ngày)*
- `sample_model/README.md`: mô tả + bảng kết quả + **1 lệnh reproduce toàn bộ**.

**Tổng công sức:** ~4–5 ngày (không tính Phase 5); có thể rút còn ~2 ngày nếu bỏ RAGAS và giữ MiniLM.

---

## Bản đồ: tiêu chí đánh giá → sample model thỏa mãn thế nào
| Tiêu chí (3 khung A/B/C) | Cách sample model đáp ứng |
|---|---|
| Precision/Recall/F1/MRR/nDCG/MAP/HitRate | Golden set graded + full relevant → đo chuẩn 100% |
| Faithfulness / Hallucination / Citation | Ground-truth answer + corpus sạch → RAGAS + kiểm thủ công |
| Answer/Context Relevance (RAG Triad, RAGAS) | Có ground-truth → chạy RAGAS tự động |
| Fallback / Từ chối đúng (RGB, Khung C) | Golden set có ca ngoài miền cố ý |
| Human-centric (Shneiderman/PAIR/HAX) | Phase 5: minh bạch nguồn + confidence + control |
| Search Stability (Khung C) | Thêm 3–5 cặp câu "cùng ý, khác cách diễn đạt" để đo độ ổn định |

## Cấu trúc thư mục đề xuất
```
sample_model/
├── corpus/           # tác phẩm đã chunk + metadata sạch
├── golden/           # queries.json (graded label, full relevant, gt answers)
├── index/            # bm25 + vector (collection sample_lit)
├── eval/             # script đo retrieval + generation + RAGAS
├── results/          # bảng + JSON kết quả
├── app_demo.py       # (Phase 5) demo human-centric
└── README.md         # mô tả + 1 lệnh reproduce
```

## 2 quyết định cần bạn chốt trước khi bắt tay
1. **Embedding cho sample:** giữ MiniLM (nhanh, đồng nhất hệ lớn) hay dùng **Vietnamese_Embedding bge-m3** (chứng minh embedding VN tốt hơn — vì corpus nhỏ nên không tốn thời gian)?
2. **Có chạy RAGAS không?** RAGAS cần 1 API key LLM làm giám khảo (có thể dùng chính Gemini) — mạnh nhưng thêm phụ thuộc.
