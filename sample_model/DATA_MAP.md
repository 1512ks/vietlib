# DATA MAP — Sample Model Corpus (Văn học Việt Nam)

> Bản đồ tổng quan bộ dữ liệu benchmark. Nguồn: [corpus/catalog.json](corpus/catalog.json).
> **51 tác phẩm · 39 tác giả · trải 725 năm (1285–2010) · 5 thời kỳ văn học.**

---

## 1. Phân bố theo THỜI KỲ (xương sống data map)
| Mã | Thời kỳ | Số tác phẩm |
|:--:|---|:--:|
| P1 | Văn học trung đại (trước TK20) | 7 |
| P2 | 1930–1945: Hiện thực · Lãng mạn · Thơ Mới | 19 |
| P3 | 1945–1954: Kháng chiến chống Pháp | 7 |
| P4 | 1954–1975: Kháng chiến chống Mỹ | 8 |
| P5 | Sau 1975: Đổi mới & đương đại | 10 |

## 2. Phân bố theo THỂ LOẠI
| Thể loại | Số lượng |
|---|:--:|
| Truyện ngắn | 17 |
| Thơ | 12 |
| Tiểu thuyết | 9 |
| Truyện thơ Nôm | 2 |
| Truyện dài | 2 |
| Nghị luận trung đại | 2 |
| Truyền kỳ / Ngâm khúc / Chương hồi / Tập truyện / Đồng thoại / Bút ký / Truyện vừa | mỗi loại 1 |

## 3. Tác giả có NHIỀU tác phẩm (dùng cho câu hỏi dạng AUTHOR)
| Tác giả | Số tác phẩm | Các tác phẩm |
|---|:--:|---|
| Nam Cao | 4 | Chí Phèo, Lão Hạc, Đời thừa, Đôi mắt |
| Nguyễn Minh Châu | 3 | Mảnh trăng cuối rừng, Bến quê, Chiếc thuyền ngoài xa |
| Vũ Trọng Phụng | 2 | Số đỏ, Giông tố |
| Thạch Lam | 2 | Gió lạnh đầu mùa, Hai đứa trẻ |
| Nguyễn Tuân | 2 | Vang bóng một thời, Chữ người tử tù |
| Tô Hoài | 2 | Dế Mèn phiêu lưu ký, Vợ chồng A Phủ |
| Kim Lân | 2 | Làng, Vợ nhặt |
| Huy Cận | 2 | Tràng giang, Đoàn thuyền đánh cá |
| Nguyễn Nhật Ánh | 2 | Mắt biếc, Tôi thấy hoa vàng trên cỏ xanh |

→ 9 tác giả × ≥2 tác phẩm ⇒ đủ dữ liệu kiểm thử truy vấn "tác giả X có những tác phẩm nào".

## 4. Trục THỜI GIAN
```
1285 ── 1428 ──── 1547 ─ 1741 ─ 1820 ─┤ trung đại (P1)
                          1925 ──────── 1943 ─┤ 1930-45 (P2, đông nhất)
                          1948 ── 1955 ─┤ chống Pháp (P3)
                          1957 ──── 1970 ─┤ chống Mỹ (P4)
                          1981 ──────── 2010 ┤ Đổi mới & đương đại (P5)
```

---

## 5. Tiến độ xây corpus (chunk tri thức)
| Trạng thái | Tác phẩm |
|---|---|
| ✅ Đã có chunk (batch 1) | Chí Phèo, Lão Hạc, Truyện Kiều, Vợ nhặt (15 chunk) |
| ⏳ Chờ viết chunk | 47 tác phẩm còn lại |

**Kế hoạch chunk:** mỗi tác phẩm 3–5 chunk (tóm tắt · nhân vật · chủ đề · tác giả/bối cảnh) → dự kiến **~180–230 chunk** cho toàn bộ 51 tác phẩm.

## 6. Kế hoạch phủ GOLDEN SET lên data map
Mục tiêu 25–30 truy vấn, phủ đều 5 thời kỳ và 5 loại câu hỏi:
| Loại truy vấn | Số câu dự kiến | Bám vào data map |
|---|:--:|---|
| FACTUAL (sự kiện, năm, nhân vật) | 8 | rải đều P1–P5 |
| AUTHOR (tác phẩm theo tác giả) | 6 | 9 tác giả nhiều tác phẩm ở mục 3 |
| SEMANTIC (chủ đề, cảm xúc) | 6 | theo chủ đề (chiến tranh, nông dân, tình yêu…) |
| MULTI_TURN (hỏi nối tiếp) | 4 | dùng đại từ "tác giả đó", "tác phẩm này" |
| FALLBACK (ngoài miền) | 4 | sách nước ngoài / chủ đề ngoài văn học |

## 7. Lớp siêu dữ liệu THƯƠNG MẠI (Human-centric / Conversational Commerce)
Bổ sung bằng Gemini grounded search (Google Search) — nguồn lưu ở cột `nguon_gia`.
| Chỉ số | Giá trị |
|---|---|
| Tác phẩm có giá tham khảo | **43/51 (84%)** |
| Giá trung vị | **60.000 đ** |
| Khoảng giá | 16.900 – 360.000 đ |
| Phân bố | <40k: 11 · 40–70k: 14 · 70–100k: 9 · ≥100k: 9 |
| Còn thiếu | 8 (bài trong SGK/tuyển tập, chưa có giá bán rời rõ ràng) |

Cột dữ liệu thương mại: `gia_tham_khao_vnd`, `tiki_link` (URL **tìm kiếm Tiki** — luôn hợp lệ), `nguon_gia` (link grounding), `ban_thuong_mai` (bản lẻ hay tên tuyển tập chứa tác phẩm — ví dụ *Nhớ rừng → Thơ Thế Lữ*, *Vợ chồng A Phủ → Truyện Tây Bắc*, *Chữ người tử tù → Vang bóng một thời*), và `ghi_chu_gia` — **note rõ**: "Bán rời" / "Nằm trong tuyển tập '...' — giá hiển thị là giá tuyển tập" / "Chưa có giá bán rời". (13 quyển trong tuyển tập · 30 bán rời · 8 chưa có giá).

**⚠️ Nhãn trung thực:** giá là *AI-searched, tham khảo* — có thể lệch thời điểm. Đã xử lý: null outlier sai (Chuyện người con gái Nam Xương 400k → dùng giá Truyền kỳ mạn lục), null liên kết nhầm (Chinh phụ ngâm gắn nhầm tập bình luận Bùi Giáng), kế thừa giá đúng (Chữ người tử tù ← Vang bóng một thời 76k). Cần verify tay trước khi công bố. Riêng giá cao nhất 360k (Truyền kỳ mạn lục) nên kiểm lại.

## 8. Vì sao data map này "ăn điểm" khi bảo vệ
- Chứng minh **độ phủ có kiểm soát**: đủ thời kỳ, thể loại, tác giả — không phải gom sách ngẫu nhiên.
- Metadata **đã kiểm chứng**, phân biệt *năm sáng tác* vs *năm in tập* → đúng tinh thần toàn vẹn dữ liệu.
- Golden set **ánh xạ minh bạch** lên từng ô của data map → đo được mọi metric mà không có vùng mù.
