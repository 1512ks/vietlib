# TỔNG HỢP LÝ THUYẾT ĐÁNH GIÁ — MỘT PHƯƠNG PHÁP LUẬN THỐNG NHẤT
*(Tài liệu học-hiểu để trình bày trước hội đồng. Bổ trợ cho `hoi_dap_ly_thuyet.md` (khái niệm nền)
và `chuan_bi_bao_ve.md` (đối chiếu chi tiết 3 khung). Số liệu: hệ lớn = eval 2026-07-20 · sample model = `sample_model/results/` lần chạy 08:24.)*

---

# PHẦN 1 — PHƯƠNG PHÁP LUẬN THỐNG NHẤT

## 1.1. Từ 3 khung tham chiếu về 1 phương pháp luận

Đồ án tham chiếu 3 khung đánh giá: **OMICall** (góc vận hành sản phẩm), **GeeksforGeeks** (góc kỹ thuật RAG), **Microsoft/Shimin Zhang** (góc sản phẩm LLM doanh nghiệp). Ba khung này không mâu thuẫn — chúng nhìn **cùng một hệ thống ở các tầng khác nhau**. Hợp nhất lại, ta được một phương pháp luận duy nhất:

> **Đánh giá chatbot RAG = đo chất lượng từng chặng trên ĐƯỜNG ĐI CỦA MỘT CÂU HỎI, cộng với độ an toàn và trải nghiệm bao quanh đường đi đó.**

Đường đi của một câu hỏi qua hệ thống và metric gác ở từng chặng:

```
Người dùng hỏi ──► [0] Viết lại câu hỏi (multi-turn) ──► [1] TRUY HỒI ──► [2] Cổng tin cậy ──► [3] SINH ──► [4] Hiển thị & trải nghiệm
                        │                                   │                 │                  │                │
                Knowledge Retention              P@K, R@K, F1, MRR,    Fallback đúng      Faithfulness,     Citation, latency,
                (nhớ hội thoại)                  nDCG, MAP, HitRate,   (từ chối khi       Answer Relevance,  streaming, thẻ nguồn,
                                                 + Stability            ngoài kho)         (RAG Triad)        conversion
```

**Bốn tầng của phương pháp luận thống nhất** (mỗi khung tham chiếu đóng góp một phần):

| Tầng | Câu hỏi cốt lõi | Metric | Nguồn khung |
|---|---|---|---|
| **T1. Truy hồi** | "Lấy đúng tài liệu chưa? Xếp đúng thứ tự chưa?" | P@K · R@K · F1 · MRR · nDCG · MAP · HitRate · Stability | B (retrieval-level), C (search) |
| **T2. Sinh** | "Trả lời có bịa không? Có đúng trọng tâm không?" | Faithfulness · Answer Relevance · Context P/R (= **RAG Triad**) · Citation | B (generation/e2e), C (LLM quality) |
| **T3. Hội thoại & an toàn** | "Nhớ được ngữ cảnh? Biết từ chối? Bền với cách hỏi khác?" | Multi-turn recall · Fallback rate · Stability · Red-team | C (retention, red teaming) |
| **T4. Trải nghiệm & vận hành** | "Người dùng có dùng được, thích, và mua không?" | Latency/streaming · tương tác · hài lòng · conversion | A (OMICall) |

**Vì sao hợp nhất kiểu này thuyết phục:** RAG là hệ **xích nối tiếp** — sinh giỏi mấy cũng vô nghĩa nếu truy hồi sai (garbage in, garbage out), truy hồi giỏi mấy cũng vô nghĩa nếu sinh bịa. Nên phải đo **từng mắt xích riêng** (T1, T2) trước khi đo **cả chuỗi** (T3, T4). Đây chính là tinh thần "component-wise trước, end-to-end sau" mà cả 3 khung cùng chia sẻ.

## 1.2. RAG Triad — hạt nhân của tầng T1–T2

RAG Triad là tam giác 3 cạnh kiểm tra chéo giữa 3 đối tượng: **Câu hỏi – Ngữ cảnh – Câu trả lời**:

1. **Context Relevance** (hỏi ↔ ngữ cảnh): ngữ cảnh lấy về có chứa thông tin trả lời được câu hỏi không? → đo bằng bộ metric T1.
2. **Groundedness / Faithfulness** (ngữ cảnh ↔ trả lời): câu trả lời có bám vào ngữ cảnh không, hay tự bịa? → đo bằng LLM-judge tách claim.
3. **Answer Relevance** (hỏi ↔ trả lời): câu trả lời có giải quyết đúng trọng tâm câu hỏi không? → đo bằng LLM-judge so với đáp án chuẩn.

**Ý nghĩa của việc đủ cả 3 cạnh:** thiếu cạnh nào là lọt đúng một loại lỗi đó. Chỉ đo 1+3 mà bỏ 2 → bot trả lời "đúng trọng tâm" nhưng bịa chi tiết vẫn được điểm cao. Chỉ đo 1+2 mà bỏ 3 → bot trung thực nhưng lạc đề vẫn qua. **Hệ lớn** đo được cạnh 1 định lượng + cạnh 2 thủ công; **sample model** là nơi đầu tiên đo trọn 3 cạnh bằng số: Context Recall@5 = 0.852 · Faithfulness = 0.990 · Answer Relevance = 1.000.

## 1.3. Hai tầng bằng chứng — vì sao có 2 bộ số liệu

| | Hệ lớn (production) | Sample model (đối chứng) |
|---|---|---|
| Corpus | 11.759 chunk, dữ liệu thật có nhiễu | 163 chunk, sạch 100%, tự soạn kiểm chứng |
| Nhãn | 30 câu, keyword nhị phân | 32 câu, **graded 0/1/2 + full relevant set** |
| Vai trò | Chứng minh hệ chạy được ở quy mô thật | Đo **chuẩn học thuật, tái lập được** mọi metric |
| Recall | Xấp xỉ (≈ Precision) — hạn chế đã khai | **Recall thật** (biết đủ tập tài liệu đúng) |
| Khâu sinh | Kiểm thủ công 15 ca | **LLM-judge tự động** kiểu RAGAS, 16 câu + 91 claim |

**Câu chốt cho hội đồng:** *"Một bộ số chứng minh tính THỰC TIỄN, một bộ số chứng minh tính KHOA HỌC. Chúng bổ trợ chứ không thay thế nhau — giống thử thuốc vừa trên bệnh nhân thật vừa trong phòng lab có đối chứng."*

---

# PHẦN 2 — Ý NGHĨA TỪNG METRIC (HỌC HIỂU, KHÔNG HỌC VẸT)

> Mẹo nhớ tổng: hình dung **người thủ thư lấy ra K cuốn sách** đặt lên bàn theo thứ tự. Mỗi metric trả lời một câu hỏi khác nhau về chồng sách đó.

## 2.1. Nhóm TRUY HỒI (đo "chồng sách" trả về)

### Precision@K — "Trong K cuốn lấy ra, mấy phần là đúng?"
- **Công thức:** số tài liệu đúng trong top-K ÷ K.
- **Ví dụ:** lấy 5 cuốn, 3 cuốn liên quan → P@5 = 0.6.
- **Nó thấy gì:** độ "sạch" của kết quả — lấy bừa nhiều rác thì P thấp.
- **Nó KHÔNG thấy gì:** có bỏ sót tài liệu đúng nằm ngoài top-K không (việc của Recall), và thứ tự xếp (việc của MRR/nDCG).
- **Số thật:** hệ lớn P@1 = 0.83 · sample hybrid P@1 = 0.929.

### Recall@K — "Trong TẤT CẢ tài liệu đúng đang có trong kho, vớt về được mấy phần?"
- **Công thức:** số tài liệu đúng trong top-K ÷ **tổng số tài liệu đúng của cả kho**.
- **Ví dụ:** kho có 4 chunk nói về Lão Hạc, top-5 vớt được 3 → R@5 = 0.75.
- **Điểm học hiểu quan trọng nhất:** mẫu số đòi hỏi phải BIẾT TRƯỚC toàn bộ tài liệu đúng. Hệ lớn 11.759 chunk không thể gán tay hết → đành xấp xỉ R = P (hạn chế tự khai). **Sample model sinh ra chính là để sửa điều này**: corpus nhỏ nên gán được *full relevant set* → Recall thật: R@5 = 0.682, R@10 = 0.799.
- **Cạm bẫy hội đồng hỏi xoáy:** "AUTHOR Recall@5 = 0.408 thấp thế?" → Trả lời: đó là **trần lý thuyết**, không phải lỗi: tác giả 4 tác phẩm có 13 chunk đúng mà chỉ lấy 5 → tối đa 5/13 ≈ 0.38. Bằng chứng: cùng câu đó Recall@10 tăng vọt.

### F1@K — "Trung bình điều hòa của P và R"
- **Ý nghĩa:** phạt nặng nếu lệch một bên (P cao R thấp hoặc ngược lại). Trung bình điều hòa < trung bình cộng khi hai số lệch nhau — nên F1 chỉ cao khi CẢ HAI cùng cao.
- **Vì sao ở hệ lớn F1 = P:** vì R đã xấp xỉ = P. Ở sample thì F1 là số thật (0.533@5).

### MRR — "Cuốn đúng ĐẦU TIÊN nằm ở vị trí thứ mấy?"
- **Công thức:** trung bình của 1/vị trí tài liệu đúng đầu tiên. Vị trí 1 → 1.0; vị trí 2 → 0.5; vị trí 3 → 0.33.
- **Vì sao là metric QUAN TRỌNG NHẤT với RAG:** LLM đọc ngữ cảnh từ trên xuống và context có hạn — tài liệu đúng phải nằm càng cao càng tốt. MRR đo đúng điều đó.
- **Số thật:** hệ lớn 0.887 · sample hybrid **0.964** (tức tài liệu đúng gần như luôn đứng đầu).

### Hit Rate@K — "Có ÍT NHẤT một cuốn đúng trong K cuốn không?"
- **Ý nghĩa:** metric "sống còn" — miễn có 1 tài liệu đúng lọt vào là LLM còn nguyên liệu để trả lời đúng. Hit = 0 thì các khâu sau vô phương cứu.
- **Số thật:** hệ lớn Hit@5 = 1.00 · sample Hit@3 = **1.00** (đạt sớm hơn một bậc K).

### nDCG@K — "Xếp hạng có TỐI ƯU không, tính cả mức độ liên quan?"
- **Học hiểu qua 3 bước:**
  1. **Gain**: mỗi tài liệu có "độ quý" — nhãn graded: 2 = trả lời trực tiếp, 1 = liên quan một phần, 0 = không. Gain = 2^rel − 1 (nhãn 2 quý gấp 3 nhãn 1 — thưởng phi tuyến).
  2. **Discount**: tài liệu càng nằm sâu càng bị chiết khấu (chia log₂ của vị trí) — vì người đọc/LLM ít khi đọc tới.
  3. **Normalize**: chia cho điểm của cách xếp HOÀN HẢO → về thang [0,1]; 1.0 = không thể xếp tốt hơn.
- **Nó thấy cái mà P/R không thấy:** hai kết quả cùng P@5 = 0.6 nhưng một cái dồn tài liệu đúng lên đầu, một cái dồn xuống cuối — nDCG phân biệt được, P thì không.
- **Nâng cấp của đồ án:** hệ lớn dùng nhãn nhị phân (nDCG "thô") — sample dùng **nhãn 3 mức 0/1/2** → nDCG chuẩn học thuật: 0.742@5.

### MAP@K — "Chất lượng xếp hạng của TOÀN danh sách"
- **Học hiểu:** đi từ trên xuống, MỖI LẦN gặp tài liệu đúng thì chụp lại Precision tại điểm đó, xong lấy trung bình các "ảnh chụp". Xếp tài liệu đúng liền nhau trên đỉnh → các ảnh chụp đều đẹp → MAP cao.
- **Khác nDCG chỗ nào:** MAP chỉ quan tâm đúng/sai (nhị phân) nhưng nhìn *mọi* tài liệu đúng; nDCG quan tâm *mức độ* liên quan. Hai góc bổ nhau.
- **Số thật:** hệ lớn 0.84@10 · sample 0.69@10 (chuẩn hóa theo min(R,K) — cách tính chặt hơn, không so trực tiếp 2 con số).

### Search Stability — "Đổi cách diễn đạt, kết quả có đổi theo không?"
- **Cách đo:** 4 cặp câu *cùng ý khác lời* ("Vì sao lão Hạc chọn cái chết?" / "Lý do gì khiến lão Hạc tìm đến cái chết?") → so 2 top-5 bằng **Jaccard** = |giao| ÷ |hợp|.
- **Số thật (sample):** mức chunk 0.384 · mức tác phẩm 0.571. Con số khiêm tốn, công bố nguyên trạng — hệ lớn trước đây *chưa đo được* metric này.
- **Vì sao đo 2 mức:** người dùng thấy *cuốn sách* chứ không thấy *chunk* — hai câu paraphrase cùng trả về Truyện Kiều nhưng khác đoạn thì với người dùng vẫn là ổn định.

## 2.2. Cổng tin cậy (giữa truy hồi và sinh)

### Ngưỡng out-of-corpus (confidence threshold)
- **Học hiểu:** trước khi cho LLM trả lời, hệ nhìn cosine cao nhất của kết quả truy hồi. Dưới ngưỡng → nhiều khả năng câu hỏi NGOÀI kho → kích hoạt chế độ từ chối.
- **Cách chọn ngưỡng 0.40 (sample):** đo thực nghiệm — câu trong kho thấp nhất 0.479, câu ngoài kho cao nhất 0.310 → đặt 0.40 giữa khe hở, biên an toàn ~0.09 mỗi phía. (Hệ lớn: cơ chế tương đương với RRF score, ngưỡng 0.003.)
- **Fallback Rate:** 4/4 câu bẫy (Harry Potter, self-help, vật lý, *tác giả không tồn tại*) đều bị chặn và từ chối lịch sự. Triết lý: **"thà từ chối còn hơn trả lời sai"**.

## 2.3. Nhóm SINH (đo câu trả lời)

### Faithfulness — "Mỗi câu khẳng định trong câu trả lời có nguồn đỡ không?"
- **Cách đo (kiểu RAGAS):** giám khảo Gemini (temperature 0) **tách câu trả lời thành từng claim** (đơn vị khẳng định dữ kiện), rồi kiểm từng claim: ngữ cảnh có thông tin đỡ cho nó không? Faithfulness = số claim được đỡ ÷ tổng claim.
- **Ví dụ:** trả lời có 4 claim, 3 claim tìm thấy trong nguồn, 1 claim model tự thêm → 0.75.
- **Vì sao tách claim thay vì chấm cả câu:** một câu trả lời dài có thể đúng 90% nhưng lẫn 1 chi tiết bịa — chấm nguyên câu sẽ bỏ lọt, tách claim thì bắt được đúng chi tiết đó.
- **Số thật:** 0.990 trên 91 claim/16 câu; 1 ca chưa tròn (q20 = 0.83) giữ nguyên làm bằng chứng trung thực.

### Answer Relevance — "Có trả lời ĐÚNG CÂU được hỏi không?"
- **Cách đo:** giám khảo so câu trả lời với **đáp án chuẩn** (ground-truth do người soạn): 1.0 đúng trọng tâm · 0.5 đúng một phần · 0.0 lạc đề.
- **Khác Faithfulness thế nào (hay bị hỏi):** Faithfulness = *trung thực với nguồn*; Answer Relevance = *trúng câu hỏi*. Bot có thể trung thực mà lạc đề (đọc nguồn A trả lời chuyện B) — cần cả hai.
- **Số thật:** 1.000 (16/16).

### Context Precision / Recall @5 — "Ngữ cảnh đưa cho LLM sạch và đủ chưa?"
- Context Precision@5 = phần ngữ cảnh đưa vào prompt thực sự liên quan (0.475 — vì luôn đưa 5 mà nhiều câu chỉ cần 1–3 nguồn). Context Recall@5 = phần tài liệu đúng của kho đã có mặt trong prompt (0.852).
- **Điểm mạnh riêng của đồ án:** RAGAS gốc phải nhờ LLM đoán 2 chỉ số này; đồ án tính **trực tiếp từ nhãn vàng** — chính xác hơn, không phụ thuộc judge.

### Citation Accuracy — "Trích nguồn có trỏ đúng tài liệu không?"
- Sample model: model chèn marker `[n]` **ngầm** (người dùng không thấy — UX chăm sóc khách hàng), hệ thống vẫn kiểm được: 100% marker trỏ vào nguồn có thật trong prompt. → Minh bạch nguồn thể hiện qua **thẻ sách** thay vì chú thích học thuật.

### Knowledge Retention (nhớ hội thoại) — "Hỏi bằng đại từ có hiểu không?"
- **Cách đo:** 4 câu chứa đại từ ("ông ấy", "tác phẩm này") kèm lịch sử giả lập → rewriter viết lại thành câu độc lập → đo retrieval như thường.
- **Số thật:** Recall@5 = 1.000, MRR = 1.000 — cơ chế viết lại câu hỏi hoạt động đúng vai trò "bộ nhớ".

## 2.4. Nhóm TRẢI NGHIỆM (tầng T4)
- **Độ trễ cảm nhận:** typing indicator hiện tức thì + streaming → token đầu 1–2s (đạt mục tiêu <2s); full 6–8s do API. Đây là ứng dụng nguyên lý **perceived performance**: người dùng chấp nhận chờ nếu thấy hệ thống đang "sống".
- **Human-centric / Conversational Commerce:** thẻ sách (giá + nút Mua Tiki + note tuyển tập) khép kín hành trình *tìm hiểu → mua*; chip gợi ý neo vào tác phẩm trong kho (luôn trả lời được) và có câu hướng mua. Chưa đo được số conversion vì chưa có người dùng thật — nói thẳng là ranh giới nghiên cứu/sản phẩm.

---

# PHẦN 3 — TỰ ĐÁNH GIÁ: BOT CÒN CẢI THIỆN ĐƯỢC GÌ

## 3.1. Điểm mạnh đã có bằng chứng số
1. Truy hồi mạnh và **đo chuẩn học thuật**: MRR 0.964, Hit@3 100%, Recall thật, nDCG graded.
2. **Chống ảo tưởng nhiều lớp có số kiểm chứng**: ngưỡng tin cậy (biên 0.09) + prompt ràng buộc + citation ngầm → Faithfulness 0.990, fallback 4/4, kể cả bẫy tác giả không tồn tại.
3. **Đo trọn RAG Triad tự động** — điều hệ lớn chưa làm được (LLM-judge kiểu RAGAS, t=0, tách claim).
4. Multi-turn có metric riêng (R@5 = 1.0) chứ không chỉ "có cơ chế".
5. Bằng chứng thực nghiệm cho lựa chọn kiến trúc: bge-m3 đưa vector từ P@1 0.33 (MiniLM, hệ lớn) lên 0.964 → định hướng nâng cấp hệ lớn có số chống lưng.

## 3.2. Hạn chế & lộ trình cải thiện (xếp theo tác động ÷ công sức)

> **Cập nhật 2026-07-20:** 6/10 mục thuần code đã XỬ LÝ và đo lại (đánh dấu ✅ — chi tiết ở
> `sample_model/results/cai_tien_v2.md`). 4 mục còn lại cần nguồn lực ngoài, giữ trong hướng phát triển.

| # | Hạn chế (số hiện tại) | Cách cải thiện cụ thể | Trạng thái | Kết quả / kỳ vọng |
|---|---|---|---|---|
| 2 | **AUTHOR Recall@5 bị trần K** (0.408 vì 13 relevant/K=5) | K thích ứng: phát hiện câu AUTHOR (tên tác giả + ý định liệt kê) → K=13 | ✅ ĐÃ LÀM | **Recall 0.408 → 0.872** |
| 1 | **Stability chunk thấp (0.384)** — paraphrase xáo thứ hạng section | Gộp điểm theo tác phẩm (max score per work) trước khi cắt top-K | ✅ ĐÃ LÀM (một phần) | **Relevance tăng mạnh** (R@10 0.80→0.87, MAP 0.69→0.82); **stability KHÔNG cải thiện** (card J@3 0.55→0.50) → vẫn là hạn chế mở, cần mở rộng truy vấn đồng nghĩa |
| 4 | **Fluency/Coherence chưa định lượng** | Judge chấm mạch lạc/trôi chảy thang 1–5 | ✅ ĐÃ LÀM | **Fluency 5.0 · Coherence 4.9–5.0** |
| 6 | **Red teaming mới ở mức câu ngoài miền** | Bộ 10 prompt tấn công (injection, moi prompt, bịa giá, giả admin, cướp vai…) | ✅ ĐÃ LÀM | **9/10 → phát hiện lỗ hổng lộ prompt → vá → 10/10** |
| 8 | **Latency chưa đo hệ thống** | Log p50/p95 truy hồi + sinh | ✅ ĐÃ LÀM | truy hồi p50 ~145ms · sinh full p50 ~4.1s p95 ~6.6s |
| 5 | **Khung A không có số vận hành** | Nút 👍/👎 + log click chip/impression sách | ✅ ĐÃ LÀM | log JSONL `usage_log.jsonl` — có số tương tác/hài lòng để demo |
| 3 | **Nhãn & chunk do 1 người soạn** | 1–2 người chấm lại mẫu 20% nhãn + nghiệm thu 163 chunk; tính Cohen's κ | ⏳ CẦN NGƯỜI | Tăng độ tin cậy học thuật |
| 7 | **Giá bán AI-searched chưa verify tay** | Đối chiếu tay 51 dòng giá với Tiki; sửa outlier (Truyền kỳ mạn lục 360k) | ⏳ CẦN BẠN | Số liệu thương mại sạch |
| 9 | Hệ lớn: nâng embedding MiniLM → bge-m3 | Re-embed 11.759 chunk, đo lại evaluate_search | ⏳ ĐỤNG PROD | Kỳ vọng vector P@1 0.33 → 0.7+ (bằng chứng từ sample) |
| 10 | Judge cùng họ model với generator | Chấm chéo mẫu bằng model khác họ (GPT/Claude) hoặc người | ⏳ CẦN KEY | Phản biện "vừa đá bóng vừa thổi còi" |

## 3.3. Đoạn nói 60 giây trước hội đồng (gợi ý)

> "Em đánh giá hệ thống theo một phương pháp luận thống nhất: đi theo đường đi của một câu hỏi qua bốn tầng — truy hồi, sinh, hội thoại-an toàn, và trải nghiệm — hợp nhất từ ba khung tham chiếu OMICall, GeeksforGeeks và Microsoft, với hạt nhân là RAG Triad. Em dùng hai tập bằng chứng: hệ production 11.759 chunk chứng minh tính thực tiễn, và một benchmark đối chứng 163 chunk có nhãn đầy đủ để đo chuẩn học thuật — nơi em tính được Recall thật, nDCG phân cấp, và tự động hóa khâu chấm sinh bằng LLM-judge theo chuẩn RAGAS: Faithfulness 0.99, Answer Relevance 1.0, từ chối đúng 4/4 câu bẫy. Em công bố cả những con số chưa đẹp — độ ổn định paraphrase 0.57, Recall nhóm tác giả bị trần K — kèm nguyên nhân và lộ trình khắc phục, vì em tin giá trị của một benchmark nằm ở tính trung thực và tái lập được."

## 3.4. Năm câu hỏi xoáy dễ gặp — trả lời ngắn

1. **"Sao số sample đẹp thế, có phải làm màu không?"** — Vì corpus sạch và có nhãn đầy đủ, ĐÚNG NHƯ THIẾT KẾ của một tập đối chứng; em không thay số hệ lớn bằng số này, và chính benchmark cũng chứa số xấu (stability 0.57, ca faithfulness 0.83) được công bố nguyên trạng.
2. **"Recall thật khác gì Recall các bạn khác hay báo?"** — Đa số báo Recall xấp xỉ bằng Precision vì không biết đủ tập tài liệu đúng; em xây corpus nhỏ đủ để gán *toàn bộ* tài liệu đúng cho từng câu → mẫu số thật.
3. **"LLM chấm LLM có đáng tin không?"** — Judge chạy temperature 0, tách claim đối chiếu nguồn (ít chủ quan hơn chấm cảm tính), 2 chỉ số context em tính từ nhãn vàng không qua judge; hạn chế cùng-họ-model em đã ghi nhận và có kế hoạch chấm chéo (mục 3.2.10).
4. **"Vì sao không dùng BLEU/ROUGE?"** — Đó là metric so khớp bề mặt chuỗi với đáp án mẫu, hợp với dịch máy/tóm tắt; câu trả lời chatbot mở có nhiều cách diễn đạt đúng — so bề mặt sẽ phạt oan. Em thay bằng Faithfulness + Answer Relevance đo ngữ nghĩa.
5. **"Ngưỡng từ chối 0.40 lấy đâu ra?"** — Không chọn cảm tính: đo phân bố cosine câu trong kho (thấp nhất 0.479) và ngoài kho (cao nhất 0.310) rồi đặt giữa khe hở, biên ~0.09 mỗi phía; quy trình hiệu chỉnh ghi trong README để tái lập.
