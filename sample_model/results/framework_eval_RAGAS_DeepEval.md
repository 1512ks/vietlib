# Đánh giá generation bằng framework THẬT: RAGAS + DeepEval (sample model)

> Chạy 2026-07-21. Judge chung: **Gemini 2.5-flash (temperature 0)**. Cùng **28 mẫu**, cùng dataset
> (`results/ragas_dataset.json`) → đối chứng công bằng với bản tự code trước đây.
> Thư viện: **ragas 0.2.15**, **deepeval 4.1.2** (GeminiModel gốc). Stack pin: langchain 0.3.x.

## Kết quả đối chứng 3 phương pháp (n=28)

| Metric | Tự code (kiểu RAGAS) | **RAGAS thật** (0.2.15) | **DeepEval thật** (4.1.2) |
|---|--:|--:|--:|
| Faithfulness | 0.968 | 0.933 | 0.996 |
| Answer Relevancy | 0.911 | 0.811 | 0.908 |
| Context Precision | 0.933 | 0.967 | 0.946 |
| Context Recall | 0.902 | 0.816 | 0.929 |

*(Context Precision "tự code" = bản rank-aware đã sửa; Context Recall/Precision của RAGAS/DeepEval là bản LLM-judge của thư viện, khác định nghĩa label-based của ta.)*

## Nhận xét

1. **Ba phương pháp độc lập HỘI TỤ** — mọi metric đều nằm quanh 0.81–1.00, không có metric nào "rơi". Điều này **xác nhận chất lượng sinh câu của sample là thật**, không phải tạo tác của một giám khảo đơn lẻ.

2. **Bản tự code khớp tốt với framework thật** — faithfulness 0.93–1.00, context precision 0.93–0.97 đồng thuận cả 3. → chứng minh cài đặt "kiểu RAGAS" của ta đúng hướng, không thổi phồng.

3. **Chênh lệch giải thích được bằng cách cài đặt metric:**
   - *Answer Relevancy:* RAGAS thấp nhất (0.811) vì RAGAS dùng **cosine embedding** giữa câu hỏi gốc và các câu hỏi "sinh ngược" — thước đo bảo thủ với tiếng Việt; tự code & DeepEval dùng **LLM chấm điểm** nên rộng lượng hơn (~0.91).
   - *Faithfulness:* DeepEval cao nhất (0.996), RAGAS thấp nhất (0.933) vì RAGAS **tách câu trả lời thành nhiều statement nguyên tử** rồi soi từng cái → khắt khe hơn.
   - *Context Recall:* RAGAS (0.816) dùng LLM suy luận từng claim của đáp án chuẩn có được context bao phủ không; DeepEval (0.929) & tự code (0.902) rộng hơn.

4. **Context Precision đồng thuận cao (0.93–0.97)** → khẳng định lần sửa công thức trước đây (naive 0.543 → rank-aware 0.933) là **đúng chuẩn**: cả RAGAS và DeepEval đều cho ~0.95.

## Ý nghĩa cho luận văn

- Giờ có thể viết **"đánh giá bằng RAGAS và DeepEval (framework chuẩn)"** một cách trung thực — đã chạy thư viện thật, không chỉ tự code.
- Trình bày **bảng 3 cột** như một hình thức **kiểm chứng chéo (cross-validation) giữa các framework** — điểm cộng về tính nghiêm ngặt phương pháp luận.
- Chênh lệch giữa framework là **bình thường và giải thích được** (khác định nghĩa/cài đặt metric) — nên nêu rõ, đừng chọn 1 con số "đẹp nhất".

## Tái lập
```
.venv/Scripts/python.exe -m sample_model.eval.build_ragas_dataset   # dựng dataset 28 mẫu
.venv/Scripts/python.exe -m sample_model.eval.run_ragas    --n 28   # RAGAS thật
.venv/Scripts/python.exe -m sample_model.eval.run_deepeval --n 28   # DeepEval thật
```
Kết quả JSON: `results/ragas_real_results.json`, `results/deepeval_real_results.json`.
Biểu đồ: `charts_datn/c18_framework_comparison.pdf`.
