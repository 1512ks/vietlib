# Sample Model — Mini-RAG benchmark chuẩn (chatbot Thư viện Văn học VN)

Hệ RAG **thu nhỏ, dữ liệu sạch, ground-truth ĐẦY ĐỦ** — tập đối chứng (controlled benchmark)
bên cạnh hệ thống lớn. Tự chứa hoàn toàn: **không đụng Qdrant production**.

> ⚠️ **Nguyên tắc trung thực**: kết quả ở đây là hiệu năng trên tập đối chứng có nhãn đầy đủ,
> KHÔNG phải hiệu năng hệ lớn (11.759 chunk). Golden set cố ý chứa ca khó và ca ngoài miền.

## Thành phần

| Đường dẫn | Nội dung |
|---|---|
| `corpus/chunks.json` | **163 chunk tri thức** × 51 tác phẩm (3–4 chunk/tác phẩm: tóm tắt · nhân vật · chủ đề · tác giả-bối cảnh · hình thức). Dữ kiện kinh điển kiểm chứng, không trích nguyên văn dài. |
| `corpus/metadata.csv` | 51 tác phẩm — metadata đã kiểm chứng + **lớp thương mại**: giá tham khảo, link Tiki, note tuyển tập (nguồn sự thật cho thẻ sách). |
| `golden/queries.json` | **32 truy vấn**: 8 FACTUAL · 6 AUTHOR · 6 SEMANTIC · 4 MULTI_TURN (kèm history) · 4 FALLBACK + 4 cặp paraphrase đo stability. Mỗi câu: graded relevance 0/1/2 + **full relevant set** (→ Recall THẬT) + 28 ground-truth answers. |
| `index/` | bge-m3 (`AITeamVN/Vietnamese_Embedding`, 1024d) + BM25, chunk-level. |
| `retrieval.py` | Hybrid RRF (vector + BM25) + ngưỡng tin cậy out-of-corpus. |
| `generate.py` | Gemini 2.5 Flash — giọng CSKH tự nhiên, marker nguồn `[n]` NGẦM (ẩn khỏi UI, dùng chấm điểm), rewriter multi-turn, gợi ý câu hỏi tiếp. |
| `app.py` | UI Streamlit style AI-Native (mockup v2, UI_SPEC.md): thẻ sách + giá + nút Mua Tiki + note tuyển tập, typing indicator, streaming, followup chips. |
| `eval/run_eval.py` | Đo retrieval (P/R/F1/MRR/nDCG graded/MAP/Hit × bm25/vector/hybrid), fallback, stability, multi-turn. |
| `eval/judge.py` | Generation kiểu RAGAS: Faithfulness + Answer Relevance (giám khảo Gemini t=0) + Context P/R@5 (từ nhãn vàng) + citation + fallback pass. |
| `results/` | JSON kết quả + `summary.md` (bảng cho báo cáo). |

## Kết quả chính (2026-07-20, chi tiết ở `results/summary.md`)

- Retrieval hybrid: **HitRate@3 = 100%**, MRR **0.964**, Recall@10 0.80 (recall THẬT).
- Fallback: **4/4** phát hiện ngoài miền + từ chối lịch sự (biên cosine 0.31 vs 0.48).
- Generation: Faithfulness **0.990**, Answer Relevance **1.00**, citation valid 100%.
- Stability (paraphrase): Jaccard tác phẩm 0.571 — hạn chế đã đo và nêu rõ.
- Đối chiếu phương pháp luận bảo vệ (3 khung A/B/C + RAG Triad): `results/danh_gia_3khung_ABC.md`.

## Reproduce (một chuỗi lệnh)

```powershell
# 1. Build index chunk-level (bge-m3, ~1 phút)
.venv/Scripts/python.exe sample_model/eval/build_index.py

# 2. Đo retrieval + fallback + stability (không cần API key)
.venv/Scripts/python.exe -m sample_model.eval.run_eval

# 3. Đo thêm generation với giám khảo Gemini (cần GEMINI_API_KEY trong env/.streamlit/secrets.toml)
.venv/Scripts/python.exe -m sample_model.eval.run_eval --judge

# 4. Chạy chatbot demo
.venv/Scripts/streamlit.exe run sample_model/app.py
```

## Các quyết định thiết kế cần nhớ khi bảo vệ

1. **Recall THẬT & nDCG graded** — sửa đúng 2 hạn chế bị flag ở hệ lớn (recall≈precision,
   nDCG nhị phân): golden set gán *toàn bộ* chunk relevant + nhãn 3 mức 0/1/2.
2. **Ngưỡng out-of-corpus 0.40** hiệu chỉnh thực nghiệm trên chính index: câu trong kho
   cosine ≥ 0.479, ngoài kho ≤ 0.310 → biên an toàn ~0.09 mỗi phía.
3. **Citation ngầm**: UI theo hướng CSKH tự nhiên (không hiện "Nguồn: [1]…"), nhưng model vẫn
   chèn `[n]` → hệ thống vẫn CHẤM ĐƯỢC citation accuracy và chọn đúng thẻ sách; minh bạch
   nguồn thể hiện qua thẻ sách (tên · tác giả · năm · giá · nút Tiki · note tuyển tập).
4. **Context Precision/Recall tính từ nhãn vàng** thay vì LLM-proxy như RAGAS gốc — chính xác
   hơn vì benchmark có full relevant set (điểm mạnh riêng của sample model).
5. **Giá bán là dữ liệu AI-searched tham khảo** (xem DATA_MAP.md mục 7) — cần verify tay
   trước khi công bố; note "giá tuyển tập" hiển thị rõ trên thẻ sách để không gây hiểu lầm.
