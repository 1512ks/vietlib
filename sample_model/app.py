"""
app.py -- Chatbot Thư viện Văn học (sample model, style AI-Native).

Triển khai đúng mockup v2 đã duyệt trong UI_SPEC.md:
  Header · message thread · thẻ sách (giá + Mua trên Tiki + note tuyển tập) ·
  trích dẫn nguồn · suggested chips · typing indicator · pill input.

Backend: hybrid retrieval bge-m3 (sample_model/index) + generation Gemini + citations.

Chạy:  .venv/Scripts/streamlit run sample_model/app.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from html import escape
from pathlib import Path

import streamlit as st

USAGE_LOG = Path(__file__).resolve().parent / "results" / "usage_log.jsonl"


def log_event(kind: str, **fields) -> None:
    """Ghi 1 dòng JSON vào usage_log.jsonl để đo các chỉ số vận hành Khung A
    (tương tác, phản hồi 👍/👎, click chip, click Mua Tiki). Best-effort — lỗi bỏ qua.
    Không dùng datetime.now() (bị chặn trong môi trường này) → dùng bộ đếm phiên."""
    try:
        st.session_state.evt_seq = st.session_state.get("evt_seq", 0) + 1
        rec = {"seq": st.session_state.evt_seq,
               "session": st.session_state.get("sid", "?"), "kind": kind, **fields}
        USAGE_LOG.parent.mkdir(exist_ok=True)
        with open(USAGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

# Cho phép chạy cả `streamlit run sample_model/app.py` lẫn `-m`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sample_model.retrieval import Retriever, Hit, CONFIDENCE_MIN       # noqa: E402
from sample_model.generate import (                                     # noqa: E402
    Generator, strip_citations, cited_indices)

# ── Nạp secret → env (Streamlit Cloud dùng st.secrets; local dùng env/.env) ──
# EMBED_DTYPE=bfloat16 trên Cloud để model bge-m3 lọt RAM free tier (xem retrieval._embed)
for _k in ("GEMINI_API_KEY", "EMBED_DTYPE"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = str(st.secrets[_k])
    except Exception:
        pass

st.set_page_config(page_title="Trợ lý Thư viện Văn học", page_icon="📚",
                   layout="centered", initial_sidebar_state="collapsed")

ACCENT = "#6366F1"

SUGGESTIONS = [
    "Gợi ý một cuốn sách hay để đọc cuối tuần",
    "Có sách nào về tình yêu và tuổi trẻ không?",
    "Tóm tắt truyện Chí Phèo giúp mình",
    "Giá cuốn Số đỏ bao nhiêu?",
]

# ══════════════════════════════════════════════════════════════════
#  CSS — design tokens AI-Native (UI_SPEC.md)
# ══════════════════════════════════════════════════════════════════
# ── Inline SVG icons (tự chứa — không phụ thuộc webfont, chạy ổn trên Streamlit Cloud) ──
SVG_BOOKS = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
             'stroke-linecap="round" stroke-linejoin="round"><path d="M3 19a2 2 0 0 1 2-2h6V5a2 '
             '2 0 0 0-2-2H5a2 2 0 0 0-2 2z"/><path d="M11 17h6a2 2 0 0 1 2 2M11 5a2 2 0 0 1 '
             '2-2h4a2 2 0 0 1 2 2v14"/><path d="M11 5v14"/></svg>')
SVG_BOOK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M4 4a2 2 0 0 1 2-2h13a1 1 0 '
            '0 1 1 1v17a1 1 0 0 1-1 1H6a2 2 0 0 1-2-2z"/><path d="M4 18a2 2 0 0 1 2-2h13"/></svg>')
SVG_CART = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="20" r="1"/>'
            '<circle cx="18" cy="20" r="1"/><path d="M2 3h2l2.4 12.3a1 1 0 0 0 1 .7h9.7a1 1 0 0 0 '
            '1-.8L21 6H5.1"/></svg>')
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root{
  --accent:#6366F1; --accent-d:#4F46E5; --online:#10B981;
  --u-bg:#E0E7FF; --u-fg:#3730A3;
  --ai-bg:#F9FAFB; --ai-bd:#EEECF6; --ai-fg:#1F2937;
  --card-bd:#ECEAF6; --collect:#8B5CF6;
  --chip-bg:#EEF0FF; --chip-fg:#4F46E5; --input-bd:#E5E3F0;
}
html, body, [class*="css"]{ font-family:'Inter',-apple-system,'Segoe UI',sans-serif; }
.hd-avatar svg{ width:22px; height:22px; } .ai-avatar svg{ width:16px; height:16px; }
.bc-cover svg{ width:22px; height:22px; } .bc-collect svg{ width:14px; height:14px; }
.tiki-btn svg{ width:14px; height:14px; }

/* Ẩn chrome mặc định Streamlit + nền dịu mắt */
#MainMenu, header[data-testid="stHeader"], footer{ visibility:hidden; }
.stApp{ background:linear-gradient(180deg,#F7F8FC 0%,#F2F3FA 100%); }
.block-container{ padding-top:1.1rem; padding-bottom:6rem; max-width:720px; }

/* ── Header ── */
.app-header{
  display:flex; align-items:center; gap:13px;
  background:linear-gradient(135deg,#6366F1 0%,#7C7CF5 55%,#8B5CF6 100%); color:#fff;
  padding:15px 20px; border-radius:16px; margin-bottom:18px;
  box-shadow:0 10px 28px rgba(99,102,241,.30);
}
.hd-avatar{
  width:42px; height:42px; border-radius:12px; flex:none;
  background:rgba(255,255,255,.20); display:flex; align-items:center;
  justify-content:center; font-size:22px;
}
.hd-title{ font-weight:700; font-size:16.5px; line-height:1.2; letter-spacing:.2px; }
.hd-sub{ font-size:12.5px; color:#DCE0FF; display:flex; align-items:center; gap:6px; margin-top:3px;}
.hd-dot{ width:8px; height:8px; border-radius:50%; background:var(--online);
  box-shadow:0 0 0 3px rgba(16,185,129,.25); display:inline-block; }

/* ── Bubbles ── */
.turn{ margin-bottom:16px; }
.msg-user{ display:flex; justify-content:flex-end; }
.bubble-user{
  background:var(--u-bg); color:var(--u-fg);
  padding:11px 15px; border-radius:16px 16px 4px 16px;
  max-width:78%; font-size:15px; line-height:1.55; }
.msg-ai{ display:flex; gap:10px; align-items:flex-start; }
.ai-avatar{
  width:30px; height:30px; border-radius:9px; flex:none; margin-top:2px;
  background:linear-gradient(135deg,#6366F1,#8B5CF6); color:#fff;
  display:flex; align-items:center; justify-content:center; font-size:15px; }
.bubble-ai{
  background:var(--ai-bg); border:1px solid var(--ai-bd); color:var(--ai-fg);
  padding:12px 16px; border-radius:4px 16px 16px 16px;
  max-width:88%; font-size:15px; line-height:1.6; }
.bubble-ai p{ margin:0 0 8px; } .bubble-ai p:last-child{ margin-bottom:0; }
.bubble-ai ul{ margin:6px 0; padding-left:20px; } .bubble-ai li{ margin:3px 0; }
.bubble-ai strong{ color:#111827; }

/* ── Thẻ sách ── */
.book-card{
  display:flex; gap:12px; background:#fff;
  border:1px solid var(--card-bd); border-left:3px solid var(--accent);
  border-radius:10px; padding:12px 14px; margin:10px 0;
  box-shadow:0 1px 3px rgba(79,70,229,.05); transition:box-shadow .18s, transform .18s; }
.book-card:hover{ box-shadow:0 8px 22px rgba(99,102,241,.14); transform:translateY(-1px); }
.bc-cover{
  width:42px; height:56px; flex:none; border-radius:6px;
  background:linear-gradient(135deg,#EEF0FF,#E0E7FF); color:var(--accent);
  display:flex; align-items:center; justify-content:center; font-size:22px; }
.bc-body{ flex:1; min-width:0; }
.bc-title{ font-weight:600; font-size:14.5px; color:#111827; }
.bc-meta{ font-size:12.5px; color:#6B7280; margin-top:1px; }
.bc-collect{ font-size:12.5px; color:var(--collect); margin-top:5px;
  display:flex; align-items:center; gap:5px; }
.bc-foot{ display:flex; align-items:center; gap:10px; margin-top:8px; flex-wrap:wrap; }
.bc-price{ color:var(--accent); font-size:15px; font-weight:500; }
.bc-price.na{ color:#9CA3AF; font-size:13px; font-weight:400; }
.tiki-btn{
  background:var(--accent); color:#fff !important; text-decoration:none;
  font-size:12.5px; font-weight:500; padding:6px 12px; border-radius:8px;
  display:inline-flex; align-items:center; gap:5px; transition:background .15s; }
.tiki-btn:hover{ background:var(--accent-d); }

/* ── Typing indicator ── */
.typing{ display:inline-flex; gap:5px; padding:14px 16px;
  background:var(--ai-bg); border:1px solid var(--ai-bd);
  border-radius:4px 16px 16px 16px; }
.typing span{ width:8px; height:8px; border-radius:50%; background:var(--accent);
  animation:pulse 1.2s infinite ease-in-out; }
.typing span:nth-child(2){ animation-delay:.2s; }
.typing span:nth-child(3){ animation-delay:.4s; }
@keyframes pulse{ 0%,80%,100%{ transform:scale(.5); opacity:.4; }
  40%{ transform:scale(1); opacity:1; } }
@media (prefers-reduced-motion:reduce){ .typing span{ animation:none; opacity:.7; } }

/* ── Suggested chips = Streamlit buttons ── */
div[data-testid="stButton"] > button{
  background:var(--chip-bg); color:var(--chip-fg); border:1px solid #E4E7FF;
  border-radius:14px; padding:9px 16px; font-size:13.5px; font-weight:500;
  min-height:44px; line-height:1.35; transition:background .15s, border-color .15s, transform .1s; }
div[data-testid="stButton"] > button:hover{ background:#E4E7FF; color:var(--accent-d);
  border-color:#C7CCFF; }
div[data-testid="stButton"] > button:active{ transform:scale(.98); }
.chips-label{ font-size:13px; color:#8B90A0; margin:4px 0 8px; font-weight:500; }

/* ── Nút phản hồi 👍/👎 (nhỏ, kín đáo, canh theo bubble AI) ── */
.fb-row div[data-testid="stButton"] > button{
  background:transparent; color:#9CA3AF; border:1px solid #ECEAF6; border-radius:8px;
  min-height:30px; padding:2px 10px; font-size:14px; }
.fb-row div[data-testid="stButton"] > button:hover{ background:#F5F3FF; color:var(--accent-d); }
.fb-thanks{ font-size:12px; color:#10B981; padding:4px 0 0 40px; }

/* ── Input pill ── */
div[data-testid="stChatInput"] textarea{ font-size:15px; }
div[data-testid="stChatInput"]{ border-color:var(--input-bd) !important; }
div[data-testid="stChatInput"] button{ background:var(--accent) !important; }

/* ── Khung viền "tấm thiệp" cho vùng chat + lá eucalyptus 4 góc ── */
.leafy{ position:fixed; z-index:0; pointer-events:none; opacity:.72;
  width:min(21vw,300px); }
.leafy svg{ width:100%; height:auto; display:block; }
.leafy-tl{ top:-8px; left:-8px; }
.leafy-tr{ top:-8px; right:-8px; transform:scaleX(-1); }
.leafy-bl{ bottom:-8px; left:-8px; transform:scaleY(-1); }
.leafy-br{ bottom:-8px; right:-8px; transform:scale(-1,-1); }
/* Màn hẹp không có chỗ trống → ẩn để không che nội dung */
@media (max-width:1150px){ .leafy{ display:none; } }

/* Vùng nội dung thành thẻ trắng bo tròn có viền (như tấm thiệp) */
.block-container{ position:relative; z-index:1;
  background:#FFFFFF; border:1px solid #E4EAE1; border-radius:22px;
  padding:24px 28px 84px !important; margin-top:1.3rem;
  box-shadow:0 14px 44px rgba(70,90,70,.09), 0 2px 8px rgba(70,90,70,.05); }
</style>
""", unsafe_allow_html=True)

# ── Lá trang trí 4 góc (SVG tự chứa, tái dùng bằng CSS lật/xoay) ──
try:
    _GREENERY = (Path(__file__).resolve().parent / "assets" / "greenery.svg").read_text(encoding="utf-8")
    st.markdown("".join(f'<div class="leafy leafy-{c}">{_GREENERY}</div>'
                        for c in ("tl", "tr", "bl", "br")), unsafe_allow_html=True)
except Exception:
    pass


# ══════════════════════════════════════════════════════════════════
#  Backend (cache resource — nạp 1 lần / phiên)
# ══════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner="⏳ Đang nạp mô hình tìm kiếm (bge-m3)…")
def load_retriever() -> Retriever:
    r = Retriever.load()
    r.warm_up()
    return r


@st.cache_resource(show_spinner=False)
def load_generator() -> Generator:
    return Generator()


# ══════════════════════════════════════════════════════════════════
#  Render helpers
# ══════════════════════════════════════════════════════════════════
def fmt_price(h: Hit) -> str:
    n = h.price_int
    if n is None:
        return '<span class="bc-price na">Chưa có giá bán rời</span>'
    s = f"{n:,}".replace(",", ".")
    return f'<span class="bc-price">{s}đ</span>'


def book_card_html(h: Hit) -> str:
    collect = ""
    if h.in_collection and h.edition:
        collect = (f'<div class="bc-collect">{SVG_BOOKS}'
                   f'Trong tuyển tập: “{escape(h.edition)}”</div>')
    tiki = ""
    if h.tiki:
        tiki = (f'<a class="tiki-btn" href="{escape(h.tiki)}" target="_blank" '
                f'rel="noopener">{SVG_CART}Mua trên Tiki</a>')
    return (
        f'<div class="book-card">'
        f'<div class="bc-cover">{SVG_BOOK}</div>'
        f'<div class="bc-body">'
        f'<div class="bc-title">{escape(h.title)}</div>'
        f'<div class="bc-meta">{escape(h.author)} · {escape(h.year)} · {escape(h.genre)}</div>'
        f'{collect}'
        f'<div class="bc-foot">{fmt_price(h)}{tiki}</div>'
        f'</div></div>'
    )


_MD_BOLD = re.compile(r"\*\*(.+?)\*\*")


def answer_to_html(text: str) -> str:
    """Chuyển câu trả lời (markdown nhẹ, ĐÃ strip marker [n]) → HTML an toàn cho bubble."""
    text = escape(strip_citations(text))
    text = _MD_BOLD.sub(r"<strong>\1</strong>", text)
    html, in_ul = [], False
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("* ", "- ", "• ")):
            if not in_ul:
                html.append("<ul>"); in_ul = True
            html.append(f"<li>{line[2:].strip()}</li>")
        else:
            if in_ul:
                html.append("</ul>"); in_ul = False
            html.append(f"<p>{line}</p>")
    if in_ul:
        html.append("</ul>")
    return "".join(html)


def picked_cards(answer: str, hits: list[Hit], max_cards: int = 3) -> list[Hit]:
    """Chọn thẻ sách: ưu tiên tác phẩm được trích ngầm [n], dedupe theo work_id
    (nhiều chunk cùng tác phẩm → 1 thẻ), tối đa max_cards thẻ."""
    used = cited_indices(answer)
    picked = [h for h in hits if h.source_idx in used] or hits
    seen, out = set(), []
    for h in picked:
        if h.work_id not in seen:
            seen.add(h.work_id)
            out.append(h)
        if len(out) >= max_cards:
            break
    return out


def render_user(content: str):
    st.markdown(
        f'<div class="turn msg-user"><div class="bubble-user">{escape(content)}</div></div>',
        unsafe_allow_html=True)


def render_assistant(content: str, cards_html: str = ""):
    st.markdown(
        f'<div class="turn msg-ai"><div class="ai-avatar">{SVG_BOOKS}</div>'
        f'<div class="bubble-ai">{answer_to_html(content)}{cards_html}</div></div>',
        unsafe_allow_html=True)


def render_followup_chips(followups: list, key_prefix: str):
    """Chip câu hỏi gợi ý tiếp theo — bấm là hỏi luôn (có log)."""
    if not followups:
        return
    cols = st.columns(len(followups))
    for i, s in enumerate(followups):
        if cols[i].button(s, key=f"{key_prefix}_{i}", use_container_width=True):
            log_event("chip_click", text=s)
            st.session_state.pending = s
            st.rerun()


def render_feedback(mi: int, msg: dict):
    """Nút 👍/👎 dưới câu trả lời — thu tín hiệu hài lòng (Khung A tiêu chí 2)."""
    fb = st.session_state.get("feedback", {})
    if mi in fb:
        st.markdown(f'<div class="fb-thanks">Cảm ơn phản hồi của bạn'
                    f'{" 👍" if fb[mi]=="up" else " 👎"}</div>', unsafe_allow_html=True)
        return
    st.markdown('<div class="fb-row">', unsafe_allow_html=True)
    c = st.columns([1, 1, 10])
    if c[0].button("👍", key=f"up_{mi}", help="Hữu ích"):
        st.session_state.setdefault("feedback", {})[mi] = "up"
        log_event("feedback", value="up", query=_prev_user(mi))
        st.rerun()
    if c[1].button("👎", key=f"down_{mi}", help="Chưa hữu ích"):
        st.session_state.setdefault("feedback", {})[mi] = "down"
        log_event("feedback", value="down", query=_prev_user(mi))
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def _prev_user(mi: int) -> str:
    """Câu hỏi của người dùng ngay trước tin nhắn trợ lý thứ mi (để gắn vào log)."""
    for j in range(mi - 1, -1, -1):
        if st.session_state.messages[j]["role"] == "user":
            return st.session_state.messages[j]["content"]
    return ""


# ══════════════════════════════════════════════════════════════════
#  Header
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="app-header">
  <div class="hd-avatar">{SVG_BOOKS}</div>
  <div>
    <div class="hd-title">Thư viện Văn học Việt Nam</div>
    <div class="hd-sub"><span class="hd-dot"></span> Tìm sách · hiểu tác phẩm · gợi ý theo sở thích</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  State + lịch sử
# ══════════════════════════════════════════════════════════════════
if "messages" not in st.session_state:
    st.session_state.messages = []          # {role, content, cards, followups}
if "pending" not in st.session_state:
    st.session_state.pending = None
if "sid" not in st.session_state:
    # id phiên ẩn danh (không dùng thời gian/random bị chặn) — theo số widget nội bộ
    st.session_state.sid = f"s{id(st.session_state) % 100000}"

# Lời chào khi phòng chat trống — ấm áp, mời gọi hành động
if not st.session_state.messages:
    render_assistant(
        "Chào bạn 👋 Mình ở đây để giúp bạn **tìm và hiểu sách văn học Việt Nam**.\n\n"
        "Bạn có thể hỏi mình kiểu như: *tóm tắt một tác phẩm*, *một tác giả có sách gì*, "
        "*gợi ý sách theo tâm trạng hay chủ đề*, hay *giá một cuốn sách*. Cứ hỏi tự nhiên nhé!")

for mi, m in enumerate(st.session_state.messages):
    if m["role"] == "user":
        render_user(m["content"])
    else:
        render_assistant(m["content"], m.get("cards", ""))
        render_feedback(mi, m)
        # Chip gợi ý tiếp theo — chỉ ở tin nhắn cuối cùng, khi không có câu đang chờ
        if (mi == len(st.session_state.messages) - 1
                and st.session_state.pending is None):
            render_followup_chips(m.get("followups") or [], key_prefix=f"fu{mi}")


# ── Suggested chips (hiện khi mới bắt đầu) ──
if len(st.session_state.messages) < 2 and st.session_state.pending is None:
    st.markdown('<div class="chips-label">Thử bắt đầu với:</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, s in enumerate(SUGGESTIONS):
        if cols[i % 2].button(s, key=f"sug_{i}", use_container_width=True):
            log_event("starter_click", text=s)
            st.session_state.pending = s
            st.rerun()


# ── Input ──
typed = st.chat_input("Nhắn cho mình một câu hỏi về sách…")
if typed:
    st.session_state.pending = typed
    st.rerun()


# ══════════════════════════════════════════════════════════════════
#  Xử lý câu hỏi đang chờ
# ══════════════════════════════════════════════════════════════════
if st.session_state.pending:
    query = st.session_state.pending
    st.session_state.pending = None
    st.session_state.messages.append({"role": "user", "content": query})
    render_user(query)

    # Typing indicator hiện NGAY (kể cả trong lúc nạp model) để không có khoảng chờ câm
    placeholder = st.empty()
    placeholder.markdown(
        f'<div class="turn msg-ai"><div class="ai-avatar">{SVG_BOOKS}</div>'
        '<div class="typing"><span></span><span></span><span></span></div></div>',
        unsafe_allow_html=True)

    retriever = load_retriever()
    generator = load_generator()
    history = st.session_state.messages[:-1]

    # Multi-turn: viết lại câu hỏi nối tiếp thành câu độc lập rồi mới truy hồi
    search_query = generator.contextualize_query(query, history)

    # K thích ứng (câu AUTHOR cần vớt nhiều chunk hơn) + gộp hạng theo tác phẩm (ổn định)
    top_k = retriever.suggest_top_k(search_query)
    hits = retriever.search(search_query, top_k=top_k, group_works=True)
    conf = retriever.confidence(hits)
    low_conf = conf < CONFIDENCE_MIN

    # Stream câu trả lời vào bubble (marker [n] được strip khi hiển thị)
    acc = ""
    for chunk in generator.answer_stream(query, hits, low_confidence=low_conf, history=history):
        acc += chunk
        placeholder.markdown(
            f'<div class="turn msg-ai"><div class="ai-avatar">{SVG_BOOKS}</div>'
            f'<div class="bubble-ai">{answer_to_html(acc)}</div></div>',
            unsafe_allow_html=True)

    # Câu từ chối (ngoài kho) → không thẻ sách, không chip gợi ý theo tác phẩm
    refused = low_conf and ("tiếc quá" in acc.lower() or "xin lỗi" in acc.lower()
                            or "chưa giúp" in acc.lower() or "không tìm thấy" in acc.lower())
    if refused:
        cards_html, followups = "", []
    else:
        picked = picked_cards(acc, hits)
        cards_html = "".join(book_card_html(h) for h in picked)
        followups = generator.suggest_followups(query, acc, hits=picked or hits)

    log_event("turn", query=query, refused=bool(refused),
              confidence=round(conf, 3), n_cards=0 if refused else len(picked),
              books=[h.title for h in ([] if refused else picked)])
    placeholder.empty()
    render_assistant(acc, cards_html)
    st.session_state.messages.append(
        {"role": "assistant", "content": acc, "cards": cards_html, "followups": followups})
    st.rerun()
