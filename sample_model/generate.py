"""
generate.py -- Sinh câu trả lời kiểu CHĂM SÓC KHÁCH HÀNG (Gemini) cho sample model.

Thiết kế:
  - Giọng nhân viên thư viện thân thiện, xưng "mình", trả lời ngắn tự nhiên.
  - KHÔNG in danh sách nguồn cho người đọc; LLM vẫn chèn marker [n] ngầm sau dữ kiện
    (để hệ thống chấm citation + chọn thẻ sách) — UI sẽ strip trước khi hiển thị.
  - Câu ngoài kho → từ chối lịch sự + gợi ý hướng khác (chống ảo tưởng).
  - Multi-turn: contextualize_query() viết lại câu hỏi nối tiếp thành câu độc lập.
  - suggest_followups(): sinh 2-3 chip câu hỏi tiếp theo.

Dùng:
    from sample_model.generate import Generator
    g = Generator()
    text = g.answer(query, hits, low_confidence=False)
"""
from __future__ import annotations

import json
import os
import re
from typing import Iterable, List, Optional

from .retrieval import Hit

GEMINI_MODEL = "gemini-2.5-flash"        # model chính: nhanh, chất lượng cao
LITE_MODEL = "gemini-2.5-flash-lite"     # model phụ rẻ/nhanh: rewriter + followups
MAX_CONTEXT_LEN = 700                     # cắt mỗi chunk tối đa N ký tự trong prompt

SYSTEM_PROMPT = """\
Bạn là nhân viên tư vấn của Thư viện Văn học Việt Nam — thân thiện, tận tình như một \
người bạn yêu sách. Xưng "mình", gọi người đọc là "bạn".

## Cách trả lời
1. **Tự nhiên như trò chuyện**: đi thẳng vào câu trả lời, ấm áp, KHÔNG rào đón kiểu \
"dựa trên ngữ cảnh được cung cấp". Ngắn gọn (dưới 180 từ), dùng gạch đầu dòng khi kể \
từ 3 tác phẩm trở lên.
2. **Chỉ nói điều có trong [TƯ LIỆU]**: mọi dữ kiện về nội dung, nhân vật, năm, thể loại \
phải lấy từ các nguồn được cung cấp. TUYỆT ĐỐI không bịa. Không chắc thì nói "mình chưa \
có thông tin phần này".
3. **Đánh dấu nguồn ngầm**: ngay sau mỗi dữ kiện lấy từ nguồn [n], chèn ký hiệu [n] \
(ví dụ: "Lão Hạc chọn cái chết để giữ trọn nhân cách [2]."). Ký hiệu này SẼ BỊ ẨN khỏi \
người đọc, đừng ngại chèn; nhưng KHÔNG tự viết mục "Nguồn:" hay "Tài liệu tham khảo".
4. **Câu hỏi ngoài kho** (sách nước ngoài, chủ đề phi văn học, tác phẩm không có trong \
[TƯ LIỆU]): xin lỗi nhẹ nhàng đúng kiểu: "Tiếc quá, thư viện mình hiện chỉ có các tác \
phẩm văn học Việt Nam nên chưa giúp bạn được phần này." — rồi mời bạn đọc khám phá một \
chủ đề gần nhất mà thư viện có. KHÔNG bịa nội dung.
5. **Câu hỏi khảo sát** (giai đoạn, phong trào, thể loại, "nên đọc gì"): tổng hợp từ các \
tác phẩm trong [TƯ LIỆU], giới thiệu 2-4 cuốn tiêu biểu kèm 1 câu vì sao nên đọc.
6. **Câu hỏi về giá / mua sách**: mỗi nguồn có dòng "Thông tin bán". Trả lời đúng giá tham \
khảo ở đó (nói rõ là *giá tham khảo, có thể thay đổi*); nếu ghi "giá tuyển tập" thì nói rõ \
tác phẩm nằm trong tuyển tập nào và giá là của cả tuyển tập; nếu chưa có giá thì nói thật. \
Luôn nhắc bạn đọc có thể bấm **nút "Mua trên Tiki" ngay dưới thẻ sách** để đặt mua.
7. Kết bằng MỘT câu mời gọi tự nhiên (hỏi tiếp / khuyến khích tìm đọc-sở hữu cuốn sách), \
trừ khi vừa từ chối.
"""

_EMPTY_FALLBACK = (
    "Xin lỗi bạn, mình chưa tạo được câu trả lời. Bạn thử hỏi lại rõ hơn "
    "(kèm tên tác phẩm hoặc tác giả) giúp mình nhé!"
)

# Marker [n] do LLM chèn — dùng để chấm citation + chọn thẻ sách, ẩn khỏi UI.
# Bắt cả dạng đơn [2] lẫn dạng gộp [1, 2, 3] mà model đôi khi sinh ra.
CITE_RE = re.compile(r"\s*\[(\d+(?:\s*,\s*\d+)*)\]")


def strip_citations(text: str) -> str:
    """Bỏ mọi marker [n] / [n, m, ...] khỏi văn bản hiển thị cho người đọc."""
    return CITE_RE.sub("", text)


def cited_indices(text: str) -> set:
    """Các source_idx được trích trong câu trả lời (gồm cả marker gộp)."""
    out = set()
    for grp in CITE_RE.findall(text):
        out.update(int(x) for x in re.findall(r"\d+", grp))
    return out


def build_prompt(query: str, hits: List[Hit], low_confidence: bool = False,
                 history: Optional[List[dict]] = None) -> str:
    """Ghép prompt RAG từ câu hỏi + các chunk truy hồi."""
    context_block = ""
    for h in hits:
        if h.price_int:
            gia = f"{h.price_int:,}đ".replace(",", ".")
            ban = f"giá tham khảo {gia}"
            if h.in_collection and h.edition:
                ban += f" (giá tuyển tập '{h.edition}' — tác phẩm nằm trong tuyển tập này)"
        else:
            ban = "chưa có giá bán rời"
        context_block += (
            f"\n--- Nguồn [{h.source_idx}] ---\n"
            f"Tác phẩm: {h.title} | Tác giả: {h.author} | Năm: {h.year} | "
            f"Thể loại: {h.genre} | Mục: {h.section}\n"
            f"Thông tin bán: {ban}\n"
            f"{h.text[:MAX_CONTEXT_LEN]}\n"
        )

    conf_note = ""
    if low_confidence:
        conf_note = (
            "\n[LƯU Ý HỆ THỐNG]: Các nguồn dưới đây LIÊN QUAN YẾU với câu hỏi — nhiều "
            "khả năng câu hỏi nằm ngoài kho thư viện. Nếu không nguồn nào trả lời được "
            "trực tiếp, hãy áp dụng quy tắc 4 (từ chối lịch sự), đừng gượng ép suy diễn.\n"
        )

    hist_block = ""
    if history:
        turns = []
        for m in history[-6:]:
            who = "Bạn đọc" if m.get("role") == "user" else "Bạn (nhân viên)"
            txt = (m.get("content") or "").replace("\n", " ").strip()[:500]
            if txt:
                turns.append(f"{who}: {txt}")
        if turns:
            hist_block = (
                "=== CUỘC TRÒ CHUYỆN TRƯỚC ĐÓ (để hiểu ngữ cảnh, KHÔNG phải nguồn dữ kiện) ===\n"
                + "\n".join(turns) + "\n\n"
            )

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"{hist_block}"
        f"=== [TƯ LIỆU] — CÁC ĐOẠN TRI THỨC LIÊN QUAN ==={conf_note}\n"
        f"{context_block}\n"
        f"=== CÂU HỎI CỦA BẠN ĐỌC ===\n{query}\n\n"
        f"=== CÂU TRẢ LỜI CỦA BẠN ==="
    )


class _GeminiClient:
    """Wrapper Gemini gọn: chống response rỗng, hỗ trợ stream."""

    def __init__(self, model: str, api_key: Optional[str] = None):
        import google.generativeai as genai
        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            raise ValueError(
                "Thiếu GEMINI_API_KEY (đặt biến môi trường hoặc .streamlit/secrets.toml).")
        genai.configure(api_key=key)
        self._model = genai.GenerativeModel(model)
        self.model_name = model

    @staticmethod
    def _safe_text(response) -> str:
        try:
            if response.text:
                return response.text
        except Exception:
            pass
        out = []
        for cand in (getattr(response, "candidates", None) or []):
            content = getattr(cand, "content", None)
            for part in (getattr(content, "parts", None) or []):
                if getattr(part, "text", ""):
                    out.append(part.text)
        return "".join(out)

    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        for _ in range(2):
            resp = self._model.generate_content(
                prompt, generation_config={"temperature": temperature})
            text = self._safe_text(resp).strip()
            if text:
                return text
        return ""

    def generate_stream(self, prompt: str, temperature: float = 0.3) -> Iterable[str]:
        emitted = False
        try:
            resp = self._model.generate_content(
                prompt, generation_config={"temperature": temperature}, stream=True)
            for chunk in resp:
                try:
                    text = chunk.text
                except Exception:
                    text = self._safe_text(chunk)
                if text:
                    emitted = True
                    yield text
        except Exception:
            pass
        if not emitted:
            yield self.generate(prompt, temperature) or _EMPTY_FALLBACK


class Generator:
    """API cấp cao: trả lời CSKH + rewriter multi-turn + gợi ý câu hỏi tiếp."""

    def __init__(self, api_key: Optional[str] = None, model: str = GEMINI_MODEL):
        self.main = _GeminiClient(model, api_key)
        # Model nhẹ cho việc phụ; lỗi (vd hết quota) thì dùng chung model chính
        try:
            self.lite = _GeminiClient(LITE_MODEL, api_key)
        except Exception:
            self.lite = self.main
        self.model_name = self.main.model_name

    # ---------------- trả lời chính ----------------
    def answer(self, query: str, hits: List[Hit], low_confidence: bool = False,
               history: Optional[List[dict]] = None) -> str:
        return (self.main.generate(build_prompt(query, hits, low_confidence, history))
                or _EMPTY_FALLBACK)

    def answer_stream(self, query: str, hits: List[Hit], low_confidence: bool = False,
                      history: Optional[List[dict]] = None) -> Iterable[str]:
        return self.main.generate_stream(build_prompt(query, hits, low_confidence, history))

    # ---------------- bộ nhớ hội thoại ----------------
    def contextualize_query(self, query: str, history: Optional[List[dict]]) -> str:
        """Viết lại câu hỏi nối tiếp thành câu ĐỘC LẬP (phục vụ truy hồi).

        Nếu không có lịch sử hoặc lỗi → trả nguyên câu gốc (an toàn).
        """
        if not history:
            return query
        turns = []
        for m in history[-6:]:
            who = "Người dùng" if m.get("role") == "user" else "Trợ lý"
            txt = (m.get("content") or "").replace("\n", " ").strip()[:400]
            if txt:
                turns.append(f"{who}: {txt}")
        if not turns:
            return query
        prompt = (
            "Cho LỊCH SỬ HỘI THOẠI và một CÂU HỎI NỐI TIẾP, hãy viết lại câu hỏi nối tiếp "
            "thành MỘT câu hỏi độc lập, đầy đủ ngữ cảnh, bằng tiếng Việt — thay các đại từ/"
            "tham chiếu (\"tác giả đó\", \"cuốn này\", \"ông ấy\"…) bằng tên cụ thể lấy từ "
            "lịch sử. Nếu câu hỏi đã độc lập thì giữ nguyên. CHỈ trả về câu hỏi.\n\n"
            f"LỊCH SỬ HỘI THOẠI:\n" + "\n".join(turns) + "\n\n"
            f"CÂU HỎI NỐI TIẾP: {query}\nCÂU HỎI ĐỘC LẬP:"
        )
        try:
            out = (self.lite.generate(prompt, temperature=0.0) or "").strip()
            out = out.splitlines()[0].strip() if out else ""
            if not out or len(out) > 300:
                return query
            return out
        except Exception:
            return query

    # ---------------- chip gợi ý tiếp theo ----------------
    def suggest_followups(self, query: str, answer: str,
                          hits: Optional[List[Hit]] = None, n: int = 3) -> List[str]:
        """Sinh n câu hỏi gợi ý tiếp theo (chip), NEO vào các tác phẩm vừa truy hồi
        (chắc chắn có trong kho → luôn trả lời được) và định hướng bạn đọc đến việc
        tìm hiểu sâu rồi MUA tác phẩm. Lỗi → trả [] (UI bỏ qua)."""
        # Danh sách tác phẩm cho phép nhắc tới (dedupe, giữ thứ tự xếp hạng)
        works, seen = [], set()
        for h in (hits or []):
            if h.work_id not in seen:
                seen.add(h.work_id)
                works.append(f"'{h.title}' ({h.author})")
        works_line = "; ".join(works[:4]) if works else "(các tác phẩm trong câu trả lời)"

        prompt = (
            "Bạn đọc vừa trò chuyện với trợ lý thư viện văn học Việt Nam.\n"
            f"Hãy đề xuất {n} câu hỏi NGẮN (dưới 12 từ) cho lượt hỏi tiếp theo, theo quy tắc:\n"
            f"1. CHỈ được hỏi về đúng các tác phẩm sau (có sẵn trong kho): {works_line}. "
            "KHÔNG nhắc tác phẩm/tác giả nào khác, không hỏi kiến thức tổng quát ngoài các cuốn này.\n"
            "2. Mỗi câu bám một trong các dạng kho trả lời được: tóm tắt nội dung, nhân vật, "
            "chủ đề - ý nghĩa, hoàn cảnh sáng tác, hoặc GIÁ BÁN của tác phẩm.\n"
            f"3. Ít nhất 1 trong {n} câu định hướng MUA sách, kiểu: \"Giá cuốn X bao nhiêu?\", "
            "\"Cuốn X có đáng mua không?\", \"Mua X phải mua theo tuyển tập nào?\".\n"
            "4. Không hỏi lại điều câu trả lời vừa nói.\n"
            "Trả về JSON array các chuỗi, không giải thích.\n\n"
            f"CÂU HỎI VỪA RỒI: {query}\nCÂU TRẢ LỜI VỪA RỒI: {strip_citations(answer)[:800]}\n"
        )
        try:
            raw = (self.lite.generate(prompt, temperature=0.4) or "").strip()
            m = re.search(r"\[.*\]", raw, re.S)
            items = json.loads(m.group(0)) if m else []
            return [str(s).strip() for s in items if str(s).strip()][:n]
        except Exception:
            return []


if __name__ == "__main__":
    import sys
    from .retrieval import Retriever, CONFIDENCE_MIN
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    r = Retriever.load()
    g = Generator()
    q = sys.argv[1] if len(sys.argv) > 1 else "Vì sao lão Hạc chọn cái chết?"
    hits = r.search(q, top_k=5)
    conf = r.confidence(hits)
    ans = g.answer(q, hits, low_confidence=conf < CONFIDENCE_MIN)
    print(f"Q: {q}  (conf={conf:.3f})\n")
    print("— RAW (marker ngầm):", ans[:400], "\n")
    print("— HIỂN THỊ:", strip_citations(ans))
    print("\n— Trích nguồn ngầm:", sorted(cited_indices(ans)))
    print("— Followups:", g.suggest_followups(q, ans, hits=hits))
