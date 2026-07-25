# Kế hoạch chuẩn bị buổi bảo vệ chương trình (ĐATN)

Hệ thống: Chatbot RAG văn học Việt Nam — Streamlit UI + Hybrid Search (BM25 + Vector, RRF)
+ Cross-Encoder rerank + Qdrant + Gemini. Demo trực tiếp trên máy cá nhân.

---

## Giai đoạn 1 — Hạ tầng (đã kiểm tra, xác nhận lại sáng demo)

- [ ] **Qdrant Cloud còn sống**: free tier có thể suspend khi idle — chạy `.\warmup_demo.ps1`
      (tự ping Qdrant + Gemini). Xác nhận collection `vn_literature` đủ **11.759 điểm**.
- [ ] **Gemini API key**: còn quota, không hết hạn. Có key dự phòng trong `.env`.
- [ ] **DB local dự phòng**: `data/vector_db` đủ 11.759 điểm + `data/bm25_index.pkl`. Nếu mạng
      chết, chạy `.\toggle_db.ps1` → truy hồi offline (chỉ Gemini còn cần mạng).

## Giai đoạn 2 — Khởi động & warm-up (30 phút trước giờ G)

- [ ] Chạy `.\warmup_demo.ps1`: kiểm hạ tầng → bật app → mở trình duyệt.
- [ ] Cold start ~35s (nạp embedder + cross-encoder). **Bật app TRƯỚC khi hội đồng vào.**
- [ ] Gõ 1 câu warm-up (vd "Số đỏ nói về gì?") để nạp model vào RAM.
- [ ] Câu đầu ~8s, các câu sau ~2–3s.

## Giai đoạn 3 — Kịch bản & câu hỏi (xem bo_cau_hoi_demo.md)

- [ ] Chỉ gõ câu **đã test** trong `bo_cau_hoi_demo.md` (11 câu chính + hệ 8 loại truy vấn).
- [ ] Nhớ **danh sách TRÁNH**: "Số đỏ xuất bản năm nào" (bị từ chối), câu cảm xúc, Harry Potter.
- [ ] Câu khoe: **sai chính tả** ("Ai viết Số đở?") vẫn trả lời đúng.
- [ ] **Video demo dự phòng** 2–3 phút phòng mạng chết hoàn toàn.

## Giai đoạn 4 — Số liệu & tài liệu (thuộc lòng)

- [ ] **11.759 chunk** · độ phủ **89%** · embedding **384 chiều** · RRF **k=60** · ngân sách
      **20.000 token** (tự tóm tắt ở 75%) · ngưỡng chặn **0.003**.
- [ ] Eval 30 câu: **Hybrid P@1 = 83,3%, MRR = 0,887** (BM25 76,7%, Vector 33,3%).
- [ ] Mở sẵn: `demo_script.md`, `bo_cau_hoi_demo.md`, `hoi_dap_ly_thuyet.md`,
      `giai_thich_code.md`, `DATN_so_lieu_that.pdf` (báo cáo), sơ đồ kiến trúc.

## Giai đoạn 5 — An toàn khi chiếu màn hình

- [ ] **ĐÓNG các file chứa key** trước khi chiếu: `.env`, `.streamlit/secrets.toml`,
      `APIKEYS (for testing).tex`. (Git đã sạch — key không lên GitHub, chỉ cần không lộ màn hình.)
- [ ] Tắt thông báo, sạc pin, **bật 4G dự phòng** (Gemini luôn cần mạng).
- [ ] Font tiếng Việt + layout hiển thị đúng trên máy chiếu (test 1280×720).

## Xử lý sự cố khi demo

| Tình huống | Cách xử lý |
|---|---|
| Lỗi `getaddrinfo failed` | **KHÔNG bấm retry** (vô ích) → tắt hẳn app, `streamlit run app.py` lại |
| Mạng chập chờn | Bấm gửi lại 1 lần (thường là blip); nếu chết hẳn → `.\toggle_db.ps1` |
| Câu trả lời kém | Giải thích bằng số liệu: "đúng 83% trên bộ đánh giá, đây là ca khó vì..." |
| Câu gõ sai/vô nghĩa | Đã vá — trả về từ chối lịch sự, không crash |

---

**Nguyên tắc vàng:** luôn gõ câu ĐÃ test trước; hội đồng yêu cầu câu tự do thì cứ chạy, nếu
kết quả kém thì giải thích ngay bằng số liệu eval thay vì lúng túng.
