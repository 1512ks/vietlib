# UI SPEC — Chatbot Thư viện Văn học (mockup v2 ĐÃ DUYỆT)

Thiết kế theo style **AI-Native** (từ skill `ui-ux-pro-max`). Dùng file này làm nguồn khi code UI thật.

## Design tokens (AI-Native)
| Token | Giá trị |
|---|---|
| Accent AI (primary) | `#6366F1` |
| Success / online dot | `#10B981` |
| User bubble | nền `#E0E7FF`, chữ `#3730A3` |
| AI bubble | nền `#F9FAFB`, viền `#EEECF6`, chữ `#1F2937` |
| Header | nền `#6366F1`, chữ trắng, subtitle `#C7D2FE` |
| Book card | nền trắng, viền `#ECEAF6`, **border-left 3px `#6366F1`**, radius 8 |
| Giá | `#6366F1` (15px, 500) |
| Nút "Mua trên Tiki" | nền `#6366F1`, chữ trắng, radius 8 |
| Note tuyển tập | chữ `#8B5CF6` + icon `ti-books` |
| Suggested chip | nền `#EEF0FF`, chữ `#4F46E5`, radius 16 |
| Input | cao 44px, pill, viền `#E5E3F0`; nút gửi tròn `#6366F1` |
| Typing indicator | 3-dot pulse `#6366F1`, animation 1.2s |
| message-gap | 16px · font: sans |

## Cấu trúc component
1. **Header:** avatar (icon `ti-books`) + "Trợ lý Thư viện Văn học" + đèn online + nút minimize/close.
2. **Message thread:** bubble AI (trái) / user (phải).
3. **Book context card** (trong câu trả lời AI): cover icon · tên · `tác giả · năm · thể loại` · [note tuyển tập nếu có] · giá + nút Mua trên Tiki.
4. **Trích dẫn nguồn:** dòng `Nguồn: [1] ... [2] ...` (chống ảo tưởng).
5. **Suggested chips:** câu hỏi gợi ý.
6. **Typing indicator:** khi AI đang trả lời (streaming).
7. **Input bar:** ô nhập + nút gửi tròn.

## Nguồn dữ liệu cho thẻ sách
Đọc `sample_model/corpus/metadata.csv` — cột: `gia_tham_khao_vnd`, `tiki_link`, `ban_thuong_mai`, `ghi_chu_gia` (note "Bán rời" / "Trong tuyển tập '...'").

## Khi build (phiên mới, skill native)
Gọi skill `ui-ux-pro-max` để: audit accessibility (contrast, touch target 44px, aria), chốt palette/typography, và tuân 129 UX guidelines. Truy vấn tham khảo:
`python <skill>/scripts/search.py "AI chatbot messaging" --domain style` và `--domain ux`.
