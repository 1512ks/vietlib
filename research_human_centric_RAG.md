# Human-Centric cho Chatbot RAG Thư viện — Báo cáo tổng hợp & Giải thích metric

> **Mục đích file này:** giúp bạn *hiểu bản chất* từng khía cạnh nhân bản và từng chỉ số đo lường,
> để tự tin bảo vệ trước hội đồng. Các con số đã được **kiểm chứng và sửa lại** (xem dấu ✅ đã sửa /
> ⚠️ cần lưu ý). Không kèm danh mục tài liệu tham khảo theo yêu cầu — tập trung vào việc học.

---

## 0. Bức tranh lớn: "Human-Centric" nghĩa là gì và đo bằng cách nào?

Đánh giá một chatbot có **2 tầng tách biệt**, đừng trộn lẫn:

- **Tầng kỹ thuật** (bạn đã làm): retrieval metrics, faithfulness — trả lời câu hỏi *"máy chạy đúng không?"*
- **Tầng con người** (file này): usability, trust, accessibility — trả lời câu hỏi *"người dùng thật có
  dùng được, tin được, và thấy dễ chịu không?"*

Một hệ retrieval điểm cao vẫn có thể **thất bại về mặt con người** nếu người dùng không hiểu cách hỏi,
không tin câu trả lời, hoặc người khiếm thị không dùng được. Đó là lý do phải đo tầng thứ hai.

---

## 1. Khung Human-Centered AI (HCAI) — nền tảng tư duy

**Ý tưởng cốt lõi (Shneiderman):** hệ AI tốt phải đạt *đồng thời* hai điều — **máy tự động hoá cao** VÀ
**con người vẫn kiểm soát cao**. Nhiều người tưởng hai cái này đánh đổi nhau (máy càng tự động thì người
càng mất quyền), nhưng thiết kế tốt đạt được cả hai. Với chatbot của bạn: máy tự tìm sách (tự động hoá),
nhưng người dùng vẫn lái được hội thoại qua chip gợi ý (kiểm soát).

**18 nguyên tắc Microsoft (Amershi, CHI 2019)** chia theo 4 giai đoạn tương tác — nhớ theo giai đoạn dễ hơn nhớ 18 cái rời:

| Giai đoạn | Nguyên tắc chính | Chatbot sách nên làm gì |
|---|---|---|
| **Ban đầu** | G1: Làm rõ hệ thống *làm được gì* | Header + empty state nêu "mình tư vấn sách văn học VN", không dùng chữ "RAG/LLM" |
| **Ban đầu** | G2: Làm rõ hệ thống làm *tốt đến đâu* | Dòng nhỏ: "dựa trên kho dữ liệu thư viện, đôi khi có thể nhầm chi tiết phụ" → chỉnh kỳ vọng |
| **Trong khi dùng** | G11: Trao quyền kiểm soát | Chip gợi ý để người dùng thu hẹp ý định thay vì máy đoán mò |
| **Khi sai** | G10: Thu hẹp phạm vi khi nghi ngờ | Hỏi ngoài kho → từ chối lịch sự + gợi ý hướng khác (fallback) |
| **Theo thời gian** | G13–17: Học từ hành vi, nhớ ngữ cảnh | (nâng cao) ghi nhớ sở thích trong phiên |

**Khái niệm "ma sát hiệu quả" (productive friction — Google PAIR):** cố tình thêm một bước nhỏ để người
dùng *suy nghĩ* thay vì nuốt chửng câu trả lời. Ví dụ: user gõ "sách Nam Cao", thay vì đổ ra 10 kết quả
ngay, chatbot hỏi lại "bạn muốn truyện ngắn hiện thực hay tiểu thuyết tâm lý?". Ma sát này **chống thiên
lệch tự động hoá** (automation bias — xu hướng tin máy vô điều kiện).

---

## 2. Công cụ đo Usability/UX — HIỂU từng thang đo

Đây là phần "metric" quan trọng nhất của tầng con người. Giải thích từng cái:

### SUS (System Usability Scale) — ✅ ngưỡng đã sửa
- **Là gì:** 10 câu, thang Likert 1–5, đo *cảm nhận dễ dùng tổng thể*.
- **Đọc điểm thế nào:** quy về thang **0–100**. **68 là mốc chuẩn** (điểm trung vị của hàng trăm hệ thống
  đã khảo sát). **>68 = trên trung bình**, ~80+ = xuất sắc, <68 = có vấn đề khả dụng.
- **⚠️ Bẫy hay gặp:** điểm SUS **KHÔNG phải phần trăm**. 68 điểm ≠ "68% hài lòng". Đừng nói nhầm trước hội đồng.
- **Điểm yếu:** đo chung chung, không bắt được lỗi *đặc thù hội thoại* (hiểu sai ý, xử lý lỗi) → cần công cụ chuyên cho chatbot.

### UEQ / UEQ-S (User Experience Questionnaire) — ✅ thang đã điền
- **Là gì:** đo bằng các cặp từ trái nghĩa (vd "khó chịu ↔ dễ chịu"). UEQ đầy đủ 26 câu; **UEQ-S rút gọn 8 câu**.
- **Đọc điểm thế nào:** thang **−3 đến +3**.
  - **> +0.8** → trải nghiệm **tích cực**
  - **−0.8 đến +0.8** → trung tính (chưa đủ tốt)
  - **< −0.8** → tiêu cực
- **Đo 2 chiều — nhớ để phân tích sâu:**
  - *Pragmatic quality* (thực dụng): dễ dùng, hiệu quả, rõ ràng.
  - *Hedonic quality* (cảm xúc): thú vị, hấp dẫn, mới mẻ.
  - → Chatbot "thủ thư AI" của bạn muốn ăn điểm ở **hedonic** (cảm giác dễ chịu, muốn dùng lại).

### CUQ (Chatbot Usability Questionnaire) — ✅ công cụ CHÍNH khuyến nghị
- **Là gì:** thang **thiết kế riêng cho chatbot** (Holmes, ĐH Ulster). 16 câu: 8 tích cực (lẻ) + 8 tiêu
  cực (chẵn) xen kẽ, Likert 1–5. Cân bằng tích/tiêu cực để chống trả lời máy móc.
- **Cách tính (hiểu để tự tính được):**
  1. Câu **tích cực** (lẻ): điểm đóng góp = *(điểm chọn − 1)* → đồng ý càng nhiều, càng cao.
  2. Câu **tiêu cực** (chẵn): điểm đóng góp = *(5 − điểm chọn)* → phản đối càng nhiều, càng cao.
  3. Mỗi câu ra 0–4 điểm → 16 câu tối đa 64.
  4. Chuẩn hoá về 100: **CUQ = (tổng điểm) × 100/64 ≈ tổng × 1,5625**.
- **Đọc điểm:** so sánh trực tiếp được với SUS (cùng thang 100). Thực tế **>70 = tốt**.
- **Vì sao chọn làm chính:** nó hỏi thẳng những thứ RAG hay hỏng — "chatbot có hiểu đúng ý tôi không",
  "xử lý lỗi có tốt không", "dẫn dắt ban đầu có rõ không".

### BUS-11 / BUS-15 (Bot Usability Scale)
- Mạnh về **tâm lý học đo lường** (đa chiều: khả năng tiếp cận, chất lượng đối thoại, chất lượng thông
  tin, bảo mật, tốc độ). Nhưng **phân tích phức tạp hơn** → hơi quá cho đồ án 10 người. Biết để nhắc, không cần dùng.

### PARADISE Framework
- **Ý tưởng:** mô hình hoá *hài lòng người dùng = hàm của (task success − các loại chi phí)*, trong đó chi
  phí = số lượt thoại, thời gian, số lỗi. Đẹp về lý thuyết nhưng **cần hạ tầng ghi log đầy đủ + phân tích
  hồi quy** → không khả thi cho nghiên cứu nhỏ. Chỉ trích dẫn như khung tham khảo.

> **CHỐT bộ công cụ cho bạn:** **CUQ (chính) + UEQ-S (bổ trợ)**. CUQ bắt lỗi đặc thù chatbot; UEQ-S (chỉ
> 8 câu) đo nhanh cảm xúc mà không làm người thử mệt.

---

## 3. Phương pháp User Study nhỏ — và cái bẫy "5 người dùng"

### Quy tắc "Nielsen 5 users" — hiểu đúng giới hạn
- **Công thức gốc (Landauer–Nielsen):** tỉ lệ lỗi tìm được = **1 − (1 − L)ⁿ**, với *n* = số người test,
  *L* = xác suất một người phát hiện một lỗi. Với giao diện đồ hoạ truyền thống **L ≈ 0,31**, nên 5 người
  đã lộ ~**85%** lỗi.
- **⚠️ Vì sao KHÔNG áp thẳng cho chatbot:** giao diện đồ hoạ mang tính **xác định** (nút bấm ai cũng thấy
  giống nhau), còn hội thoại mang tính **ngẫu nhiên** — mỗi người hỏi một kiểu, dùng từ khác nhau. Nên *L*
  của chatbot **thấp hơn nhiều** và biến thiên lớn → 5 người sẽ **bỏ sót** nhiều lỗi hallucination / hiểu
  sai ngữ cảnh.
- **→ Khuyến nghị: 8–12 người** để đạt "bão hoà dữ liệu" (data saturation — thêm người mà không phát hiện
  lỗi mới nữa).

### 3 nhiệm vụ kiểm thử (độ khó tăng dần) + chỉ số đo

| Nhiệm vụ | Ví dụ | Đo cái gì |
|---|---|---|
| **1. Tìm xác định** | "Tìm 'Hồ Quý Ly' của Nguyễn Xuân Khánh, có trong kho không?" | **TSR** (task success rate), **ToT** (time-on-task), **số lượt thoại** |
| **2. Tìm mơ hồ** | "Tìm sách ấm áp tặng mẹ yêu Hà Nội xưa" | Khả năng hiểu ngữ cảnh phức tạp, tính hữu ích cảm nhận, hiệu quả chip gợi ý |
| **3. Ngoài phạm vi** | "Chỉ tôi công thức nấu phở" | **Chất lượng fallback**: có từ chối đúng không, có lịch sự/định hướng không |

**Giải thích 3 chỉ số định lượng:**
- **TSR (Task Success Rate):** % người *hoàn thành được* nhiệm vụ. Chỉ số end-to-end quan trọng nhất.
- **ToT (Time-on-Task):** thời gian hoàn thành. **Không có ngưỡng chuẩn tuyệt đối** — dùng để *so tương
  đối* giữa các phiên bản, hoặc giữa nhóm tuổi.
- **Số lượt thoại đến mục tiêu:** càng ít càng tốt (với cùng độ khó). Cũng là chỉ số *tương đối*.

**Think-aloud:** yêu cầu người dùng *nói ra suy nghĩ* khi thao tác ("giờ tôi không biết bấm đâu..."). Đây
là cách rẻ nhất để lộ *mô hình tâm trí* sai và rào cản nhận thức — dữ liệu định tính vàng cho luận văn.

---

## 4. Trust — phần lý thuyết dễ bị hội đồng hỏi nhất

### 4 yếu tố tạo/phá niềm tin
1. **Độ chính xác thông tin** — sai một chi tiết văn học là mất uy tín.
2. **Giọng điệu** — chuẩn mực, thân thiện như thủ thư.
3. **Thừa nhận giới hạn (epistemic humility)** — dám nói "mình không chắc" thay vì bịa.
4. **Tốc độ phản hồi** — đặc biệt **time-to-first-token** (bao lâu chữ đầu tiên xuất hiện). Chờ >2–3 giây
   mà không có tín hiệu (typing indicator) → người dùng mất kiên nhẫn.

### Tranh luận về Citation — ✅ ĐÃ SỬA số liệu (phần quan trọng cho "citation ngầm" của bạn)

Nghiên cứu **Ding et al. (2025)** về citation trong câu trả lời AI tìm ra 3 điều — nhớ kỹ vì liên quan
trực tiếp thiết kế của bạn:

1. **Có citation → tin tưởng tăng** — *kể cả khi citation là ngẫu nhiên/không liên quan*. Nghĩa là
   citation hoạt động như **"bằng chứng xã hội"** (social proof): người ta tin vì *thấy có nguồn*, không
   phải vì đã kiểm nguồn.
2. **Khi người dùng THỰC SỰ mở citation ra kiểm tra → tin tưởng lại GIẢM.** (Vì nhìn kỹ mới thấy nguồn
   không hoàn hảo.)
3. Citation ngẫu nhiên mà bị kiểm tra thì tin tưởng *ngang bằng không có citation*.

**⚠️ Đính chính so với bản báo cáo ngoài:**
- Con số **"<1% người dùng bấm vào nguồn"** là **có thật** nhưng đến từ **khảo sát Pew về AI Overviews**,
  **KHÔNG phải** từ Ding et al. (bản ngoài gộp nhầm 2 nghiên cứu).
- **"Thấp hơn 15 lần" là SAI.** Số Pew thật: có AI summary thì bấm link ~**8%**, không có thì ~**15%** →
  chênh khoảng **2 lần**. Bỏ hẳn con số "15 lần" khỏi luận văn.

**Bài học rút ra cho "citation ngầm":** citation ngầm giúp *cảm giác tin cậy* và giữ giọng tự nhiên — tốt.
**Nhưng** nó là con dao hai lưỡi: dễ tạo **niềm tin mù** (người dùng tin vì giọng chắc nịch, chẳng ai kiểm
chứng). → Chính vì thế **bắt buộc** phải có cơ chế "thừa nhận không chắc chắn" (mục dưới), và nên dùng
**thiết kế lai**: văn tự nhiên + citation ngầm trong chat, kèm **thẻ sách trực quan** có thư mục đầy đủ
phía dưới cho ai muốn kiểm chứng.

### Calibrated Trust — khái niệm phải hiểu để trả lời hội đồng
- **Mục tiêu KHÔNG phải là tối đa hoá niềm tin**, mà là **hiệu chuẩn** nó: niềm tin của người dùng khớp
  đúng với năng lực thật của hệ thống.
- **Over-reliance (tin quá):** tin cả khi máy sai → tiếp nhận kiến thức văn học bị bóp méo mà không nghi ngờ.
- **Under-reliance (tin thiếu):** máy từ chối máy móc/vụng về → người dùng bỏ đi dù máy làm được.
- **Cách đạt hiệu chuẩn:** khi *độ tin cậy truy xuất (retrieval confidence)* thấp, chatbot nên **chủ động
  báo sự không chắc chắn**: *"Mình tìm thấy thông tin liên quan nhưng dữ liệu chưa đủ để khẳng định chắc
  chắn..."* → giữ người dùng ở trạng thái cảnh giác lành mạnh.

---

## 5. Persona & xưng hô tiếng Việt

**Mức nhân cách hoá:** tiết chế. Đừng làm avatar người thật chuyển động (tốn tài nguyên + dễ rơi vào
**"thung lũng kỳ lạ" / uncanny valley** — cảm giác "gần giống người nhưng sai sai" gây khó chịu). Định vị
đúng: **"trợ lý thủ thư mẫn cán, khách quan"**, và nói rõ đây là AI để người dùng không lầm là người thật.

> ⚠️ **Đã sửa:** bản ngoài viết "uncanny valley đặc biệt với nữ giới" — claim này cơ sở yếu, **nên bỏ** vế
> giới tính, chỉ giữ ý chung.

**Bảng xưng hô — hiểu vì sao chọn "Mình – Bạn":**

| Cặp xưng hô | Cảm giác | Phù hợp? |
|---|---|---|
| Tôi – Quý khách | Trang trọng, xa cách, kiểu ngân hàng | ❌ Lạnh, không hợp không gian thư viện chia sẻ tri thức |
| **Mình – Bạn** | Thân thiện, gần gũi, ấm | ✅ **Mặc định** — nhưng giữ ngôn từ chuẩn mực, không teencode |
| Thư viện – Bạn | Rõ vai trò tổ chức, trung tính tuổi | ✅ Bổ trợ cho các thông báo chính thức |

**Rủi ro persona quá thân mật:** giọng quá ngọt → người dùng **kỳ vọng sai** rằng máy cũng thông minh
vượt trội → khi máy hallucination, niềm tin **sụp đổ mạnh hơn** so với hệ thống ngay từ đầu khiêm tốn nhận mình là công cụ.

---

## 6. Accessibility (WCAG) — ✅ các thông số đã điền

**Touch target (kích thước vùng chạm):**
- **24×24 px** = chuẩn tối thiểu WCAG 2.2 mức **AA** (tiêu chí 2.5.8).
- **44×44 px** = mức nâng cao **AAA** + best-practice cho mobile/người lớn tuổi. → Bạn để 44px là **đúng và vượt chuẩn**.

**Tương phản màu (contrast ratio):**
- Chữ thường phải đạt **≥ 4,5:1** so với nền (WCAG AA, tiêu chí 1.4.3); chữ lớn ≥ 3:1.
- **Quy tắc vàng:** màu **không được là phương tiện duy nhất** truyền thông tin. Đừng chỉ dùng xanh=còn
  sách / đỏ=hết — phải kèm **nhãn chữ** (người mù màu vẫn đọc được).

**Streaming text + screen reader — cái bẫy kỹ thuật quan trọng:**
- Hiệu ứng chữ hiện dần rất đẹp với người sáng mắt, nhưng với trình đọc màn hình (NVDA/JAWS) mà cấu hình
  sai, nó sẽ **đọc lại cả câu mỗi khi có 1 chữ mới** → tra tấn người khiếm thị.
- **Cách sửa** — đặt ARIA cho khung chat:
  - `role="log"` → báo đây là luồng lịch sử hội thoại.
  - `aria-live="polite"` → chỉ đọc khi người dùng rảnh, không cắt ngang.
  - `aria-atomic="false"` → **chỉ đọc phần mới thêm**, không đọc lại từ đầu. (Đây là dòng quan trọng nhất.)
  - Thêm tuỳ chọn **tắt streaming** khi bật chế độ hỗ trợ tiếp cận.

**Người lớn tuổi / ít kinh nghiệm số:**
- Font sans-serif, mặc định **≥16px**, cho phóng to tới **200%** không vỡ layout.
- **"Blank page problem" (hội chứng trang trắng):** ô nhập trống buộc người dùng phải *tự nghĩ ra* câu hỏi
  (recall) — gánh nặng lớn. **Empty state + suggestion chips** biến việc đó thành *nhận biết* (recognition
  — chỉ cần bấm chip có sẵn). Đây là "giàn giáo" (scaffolding) đỡ tư duy người mới → bạn đã làm đúng.

---

## 7. Đạo đức & tác hại

- **Filter bubble:** nếu cứ gợi ý sách giống cái đã đọc → độc giả bị nhốt trong vùng an toàn, nghèo trải
  nghiệm. Thư viện nên có cơ chế **serendipity** (thỉnh thoảng giới thiệu tác phẩm ngoài vùng quen).
- **Hallucination hại tri thức:** RAG giảm bịa nhưng không loại hết — có thể nhầm cốt truyện, gán nhầm
  nhân vật. Với học sinh/sinh viên tra cứu học tập → sai kiến thức nền. Đây là lý do faithfulness + fallback
  của bạn có giá trị.
- **Privacy:** chat log chứa thông tin nhạy cảm (tâm trạng, hoàn cảnh). Phải **lọc PII** trước khi gửi API
  bên thứ ba, và có chính sách xoá log.
- **Informed consent (cho user study):** trước khi test phải cho người tham gia biết *ghi lại dữ liệu gì*,
  *dùng cho mục đích gì*, cam kết *ẩn danh* và *được rút lui bất cứ lúc nào* không bị ảnh hưởng. Nên có
  **checkbox xác nhận ngay trên giao diện Streamlit**.

---

## 8. Bảng tổng hợp: khía cạnh → đo bằng gì → đọc thế nào → tốn bao nhiêu

| Khía cạnh | Công cụ/phương pháp | Ngưỡng đọc hiểu | Chi phí |
|---|---|---|---|
| Usability chatbot | **CUQ** (16 câu) | >70/100 = tốt | 1 tuần, 8–12 người |
| Trải nghiệm cảm xúc | **UEQ-S** (8 câu) | >+0.8 = tích cực (thang −3..+3) | Ghép cùng CUQ |
| Dễ dùng tổng thể (tuỳ chọn) | SUS (10 câu) | >68 = trên trung bình | Ghép cùng |
| Hiệu suất tương tác | Log: TSR, ToT, số lượt thoại | So *tương đối*, không có mốc tuyệt đối | Tự động ghi |
| Hiệu chuẩn niềm tin | Cài "bẫy" thông tin sai trong task | % người phát hiện & nghi ngờ | Thiết kế kịch bản |
| Accessibility | NVDA/VoiceOver + Lighthouse | 100% tiêu chí WCAG 2.2 AA | 2 ngày, tự kiểm |
| Touch target | Đo px | ≥24 (AA), ≥44 (tốt) | Kiểm CSS |
| Tương phản | Đo ratio | ≥4.5:1 (chữ thường) | Kiểm CSS |

---

## 9. Kế hoạch User Study mẫu (10 ngày, 10 người)

**Người tham gia:** 10 độc giả — 4 sinh viên trẻ, 3 trung niên, 3 cao tuổi ít kinh nghiệm số (để lộ khác biệt theo tuổi).

**Quy trình mỗi người (~30 phút):**
1. **Ký consent + giới thiệu ngắn** (5 phút)
2. **Làm 3 nhiệm vụ, vừa làm vừa nói to (think-aloud)** (15 phút): tìm xác định → tìm mơ hồ → hỏi ngoài phạm vi
3. **Điền CUQ + UEQ-S** trên Google Forms (5 phút)
4. **Phỏng vấn bán cấu trúc** về trải nghiệm (5 phút)

**Phân tích:**
- *Định lượng:* tính điểm CUQ (công thức mục 2) + UEQ-S; báo trung bình (Mean) + độ lệch chuẩn (SD) từng
  item để lộ điểm nghẽn.
- *Định tính:* **Affinity mapping** — gom các câu than phiền/gợi ý thành cụm chủ đề ("lỗi giao diện", "lỗi
  nội dung RAG", "giọng điệu chưa hợp"); trích **≥5 câu nói đắt giá** đưa vào phần thảo luận.

---

## 10. Chốt: 5 việc cần làm + 3 hạn chế phải chủ động thừa nhận

### 5 việc ưu tiên trước bảo vệ
1. **Sửa streaming cho screen reader** (ARIA `aria-atomic="false"`) — quay video NVDA đọc mượt để trình chiếu.
2. **Thêm "ma sát hiệu quả"**: chip gợi ý làm rõ ý định khi câu hỏi mơ hồ, đừng đổ kết quả ngay.
3. **Hiện trạng thái chờ**: typing indicator / skeleton khi RAG chạy >2 giây.
4. **Trang onboarding tối giản**: empty state + câu hỏi mẫu dạng chip cho người dùng lần đầu.
5. **Consent + privacy**: checkbox xác nhận + cam kết ẩn danh log ngay trên Streamlit.

### 3 hạn chế nên tự nêu trước khi hội đồng hỏi (điểm cộng trung thực)
1. **Cỡ mẫu nhỏ (10 người):** đủ lộ lỗi thiết kế cốt lõi, nhưng chưa đại diện toàn bộ độc giả.
2. **Không có nhóm đối chứng:** chưa so định lượng chatbot với tìm kiếm dạng bộ lọc truyền thống → chưa
   *chứng minh* chatbot vượt trội, chỉ đánh giá được trải nghiệm nội tại.
3. **Lệch phân bố người dùng:** nhóm test nghiêng về người trẻ rành công nghệ → kết quả "dễ dùng" có thể
   lạc quan hơn thực tế với người cao tuổi.

> **Vì sao chủ động nêu hạn chế là điểm mạnh:** nó cho hội đồng thấy bạn *hiểu giới hạn phương pháp của
> mình* — dấu hiệu của tư duy khoa học chín, quan trọng hơn việc giả vờ mọi thứ hoàn hảo.
