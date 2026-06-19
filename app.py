"""
app.py -- Streamlit Web UI cho RAG Chatbot Thư viện Điện tử Tiếng Việt.

Chạy:
    streamlit run app.py

Yêu cầu:
    pip install streamlit
    Đặt GEMINI_API_KEY, QDRANT_URL, QDRANT_API_KEY trong file .env
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Cầu nối Secrets của Streamlit Cloud → biến môi trường ──
# Khi deploy trên Streamlit Cloud không có file .env; các module dùng
# os.environ.get(...) cần được nạp giá trị từ st.secrets.
try:
    for _k in ("GEMINI_API_KEY", "QDRANT_URL", "QDRANT_API_KEY",
               "BM25_INDEX_URL", "VECTOR_DB_URL"):
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass


# ============================================================
#  Page Config
# ============================================================
st.set_page_config(
    page_title="📚 Thư viện Văn học Việt Nam",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
#  Custom CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Background ── */
.stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #0f0c29 40%, #1a0a2e 70%, #0d1b2a 100%);
    min-height: 100vh;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(15,12,41,0.95);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(139,92,246,0.2);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] label {
    color: #94a3b8 !important;
    font-size: 0.82rem;
    font-weight: 500;
}

/* ── Header ── */
.app-header {
    text-align: center;
    padding: 2rem 1rem 1.5rem;
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(168,85,247,0.12));
    border-radius: 20px;
    border: 1px solid rgba(139,92,246,0.3);
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.app-header::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 60%);
    animation: pulse 4s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:0.5} 50%{opacity:1} }
.app-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #c4b5fd, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.3rem;
    position: relative;
}
.app-header p {
    color: #94a3b8;
    margin: 0;
    font-size: 0.95rem;
    position: relative;
}

/* ── Mode badge trong header ── */
.mode-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 0.6rem;
    position: relative;
}
.mode-hybrid { background: rgba(99,102,241,0.2); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.4); }
.mode-bm25   { background: rgba(234,179,8,0.15); color: #fbbf24; border: 1px solid rgba(234,179,8,0.3); }
.mode-vector { background: rgba(168,85,247,0.15); color: #c084fc; border: 1px solid rgba(168,85,247,0.3); }

/* ── Chat bubbles ── */
.chat-user {
    display: flex;
    justify-content: flex-end;
    margin: 1rem 0;
    animation: slideLeft 0.3s ease;
}
@keyframes slideLeft { from{opacity:0;transform:translateX(20px)} to{opacity:1;transform:translateX(0)} }
.chat-user-bubble {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    padding: 0.8rem 1.2rem;
    border-radius: 20px 20px 4px 20px;
    max-width: 68%;
    font-size: 0.95rem;
    line-height: 1.6;
    box-shadow: 0 4px 20px rgba(99,102,241,0.35), 0 1px 3px rgba(0,0,0,0.3);
}
.chat-bot {
    display: flex;
    justify-content: flex-start;
    margin: 1rem 0;
    animation: slideRight 0.3s ease;
}
@keyframes slideRight { from{opacity:0;transform:translateX(-20px)} to{opacity:1;transform:translateX(0)} }
.chat-bot-inner {
    max-width: 82%;
}
.chat-bot-bubble {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    color: #e2e8f0;
    padding: 0.9rem 1.2rem;
    border-radius: 20px 20px 20px 4px;
    font-size: 0.95rem;
    line-height: 1.7;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.chat-bot-bubble strong { color: #c4b5fd; }
.chat-bot-bubble em { color: #93c5fd; }

/* ── Meta row (latency + mode) ── */
.meta-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 0.4rem;
    flex-wrap: wrap;
}
.latency-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.72rem;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 500;
}
.badge-green  { background: rgba(34,197,94,0.12);  color: #4ade80; border: 1px solid rgba(34,197,94,0.25); }
.badge-yellow { background: rgba(234,179,8,0.12);  color: #facc15; border: 1px solid rgba(234,179,8,0.25); }
.badge-red    { background: rgba(239,68,68,0.12);  color: #f87171; border: 1px solid rgba(239,68,68,0.25); }
.mode-tag {
    font-size: 0.72rem;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(139,92,246,0.12);
    color: #a78bfa;
    border: 1px solid rgba(139,92,246,0.25);
    font-weight: 500;
}

/* ── Citation cards ── */
.citation-section {
    margin-top: 0.75rem;
}
.citation-label {
    font-size: 0.78rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.4rem;
}
.citation-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 8px;
}
.citation-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 0.6rem 0.85rem;
    transition: border-color 0.2s, background 0.2s;
}
.citation-card:hover {
    border-color: rgba(139,92,246,0.4);
    background: rgba(139,92,246,0.06);
}
.citation-num {
    font-size: 0.72rem;
    color: #a78bfa;
    font-weight: 700;
    display: inline-block;
    background: rgba(139,92,246,0.15);
    padding: 1px 7px;
    border-radius: 10px;
    margin-bottom: 4px;
}
.citation-title {
    color: #93c5fd;
    font-style: italic;
    font-size: 0.88rem;
    font-weight: 500;
    display: block;
    line-height: 1.3;
}
.citation-author {
    color: #94a3b8;
    font-size: 0.8rem;
    margin-top: 2px;
}
.citation-score {
    color: #475569;
    font-size: 0.72rem;
    margin-top: 3px;
}
.citation-snippet {
    color: #64748b;
    font-size: 0.78rem;
    margin-top: 4px;
    line-height: 1.4;
    border-top: 1px solid rgba(255,255,255,0.05);
    padding-top: 4px;
}

/* ── Suggestion chips ── */
.suggest-label {
    color: #64748b;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin: 0.8rem 0 0.4rem;
}

/* ── Welcome card ── */
.welcome-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(168,85,247,0.08));
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    text-align: center;
}
.welcome-icon { font-size: 3.5rem; margin-bottom: 1rem; display: block; }
.welcome-card h3 {
    font-family: 'Playfair Display', serif;
    color: #e2e8f0;
    font-size: 1.4rem;
    margin: 0 0 0.5rem;
}
.welcome-card p { color: #94a3b8; font-size: 0.95rem; margin: 0; line-height: 1.6; }

/* ── Stats row ── */
.stats-row {
    display: flex;
    gap: 10px;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}
.stat-chip {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: #94a3b8;
}
.stat-chip span { color: #c4b5fd; font-weight: 600; }

/* ── Input ── */
[data-testid="stChatInput"] textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(139,92,246,0.35) !important;
    border-radius: 14px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.18) !important;
}

/* ── Buttons ── */
.stButton button {
    background: rgba(99,102,241,0.12) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    color: #a5b4fc !important;
    border-radius: 10px !important;
    font-size: 0.85rem !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    background: rgba(99,102,241,0.25) !important;
    border-color: rgba(99,102,241,0.5) !important;
    transform: translateY(-1px) !important;
}

hr { border-color: rgba(255,255,255,0.06) !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
#  Cache
# ============================================================
@st.cache_resource(show_spinner=False)
def load_engine(use_reranker: bool = True):
    try:
        from utils.download_utils import check_and_download_resources
        check_and_download_resources()
    except Exception as e:
        st.warning(f"Lỗi khi kiểm tra/tải tài nguyên tự động: {e}")
    from retrieval_qa import RetrievalQA
    return RetrievalQA.build(use_reranker=use_reranker)


@st.cache_resource(show_spinner=False)
def load_suggester(_gemini_client):
    from question_suggester import QuestionSuggester
    return QuestionSuggester(_gemini_client)


# ============================================================
#  Session State
# ============================================================
def init_session():
    defaults = {
        "messages": [],
        "pending_query": None,
        "engine_loaded": False,
        "search_mode": "hybrid",
        "use_reranker": True,
        "top_k": 5,
        "n_suggest": 3,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ============================================================
#  Sidebar
# ============================================================
with st.sidebar:
    st.markdown("## ⚙️ Cài đặt")
    st.divider()

    st.markdown("**🔍 Chế độ tìm kiếm**")
    mode_map = {
        "🔀 Hybrid (BM25 + Vector)": "hybrid",
        "📝 BM25 Only": "bm25",
        "🧠 Vector Only": "vector",
    }
    mode_label = st.selectbox(
        "Chiến lược retrieval",
        list(mode_map.keys()),
        index=0,
        label_visibility="collapsed",
    )
    search_mode = mode_map[mode_label]

    use_reranker = st.checkbox(
        "⚡ Cross-Encoder Rerank",
        value=True,
        disabled=(search_mode != "hybrid"),
        help="Chỉ áp dụng cho chế độ Hybrid",
    )
    if search_mode != "hybrid":
        use_reranker = False

    top_k = st.slider("📄 Số tài liệu tham khảo (Top-K)", 1, 10, 5)

    st.divider()
    st.markdown("**💡 Câu hỏi gợi ý**")
    n_suggest = st.slider("Số câu gợi ý", 1, 5, 3)

    st.divider()

    show_snippets = st.checkbox("📄 Hiện trích đoạn văn bản", value=False,
                                 help="Hiện đoạn text ngắn trong citation card")

    st.divider()

    # Export
    if st.session_state.messages:
        st.markdown("**💾 Xuất lịch sử chat**")

        def _build_json() -> str:
            export = []
            for msg in st.session_state.messages:
                entry = {"role": msg["role"], "content": msg["content"]}
                if msg["role"] == "assistant" and "meta" in msg:
                    m = msg["meta"]
                    entry["latency_ms"] = m.get("latency", {}).get("total_ms", 0)
                    entry["mode"] = m.get("mode", "")
                    entry["sources"] = [
                        {"title": c.get("title"), "author": c.get("author")}
                        for c in m.get("contexts", [])
                    ]
                export.append(entry)
            return json.dumps(export, ensure_ascii=False, indent=2)

        def _build_txt() -> str:
            lines = ["=== LỊCH SỬ CHAT — Thư viện Văn học Việt Nam ===\n"]
            for msg in st.session_state.messages:
                label = "👤 Người dùng" if msg["role"] == "user" else "🤖 Chatbot"
                lines.append(f"{label}:\n{msg['content']}")
                if msg["role"] == "assistant" and "meta" in msg:
                    srcs = msg["meta"].get("contexts", [])
                    if srcs:
                        lines.append("📚 Nguồn: " + " | ".join(
                            f"{c.get('title')} ({c.get('author')})" for c in srcs
                        ))
                lines.append("-" * 50)
            return "\n".join(lines)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📄 JSON", _build_json(), "chat_history.json",
                               "application/json", use_container_width=True)
        with c2:
            st.download_button("📝 TXT", _build_txt(), "chat_history.txt",
                               "text/plain", use_container_width=True)

    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.rerun()

    st.divider()
    st.markdown("""
    <div style="color:#475569; font-size:0.76rem; line-height:1.7;">
    📚 <strong style="color:#64748b;">Thư viện Văn học Việt Nam</strong><br>
    RAG · Gemini 2.5 Flash · Qdrant Cloud<br>
    BM25 + Hybrid + Cross-Encoder Rerank<br>
    <span style="color:#334155;">ĐATN 2025–2026</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
#  Header
# ============================================================
mode_icons = {"hybrid": "🔀", "bm25": "📝", "vector": "🧠"}
mode_names = {"hybrid": "Hybrid+Rerank", "bm25": "BM25 Only", "vector": "Vector Only"}
rerank_tag = " + Rerank" if (search_mode == "hybrid" and use_reranker) else ""

st.markdown(f"""
<div class="app-header">
    <h1>📚 Thư viện Văn học Việt Nam</h1>
    <p>Chatbot thông minh hỗ trợ tìm kiếm &amp; khám phá văn học Việt Nam</p>
    <div>
        <span class="mode-badge mode-{search_mode}">
            {mode_icons[search_mode]} {mode_names[search_mode]}{rerank_tag}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
#  Engine loader
# ============================================================
def get_engine():
    with st.spinner("⏳ Đang khởi tạo hệ thống... (chỉ cần chờ lần đầu)"):
        return load_engine(use_reranker=use_reranker)


# ============================================================
#  Helpers
# ============================================================
def latency_badge_html(lat: dict) -> str:
    total_ms = lat.get("total_ms", 0)
    ret_ms   = lat.get("retrieve_ms", 0)
    llm_ms   = lat.get("llm_ms", 0)
    is_cached = lat.get("cached", False)

    if is_cached:
        return (
            '<span class="latency-badge badge-green">'
            '⚡ Cache hit · <1ms'
            '</span>'
        )

    total_s  = total_ms / 1000
    if total_s < 5:
        cls, icon = "badge-green", "🟢"
    elif total_s < 15:
        cls, icon = "badge-yellow", "🟡"
    else:
        cls, icon = "badge-red", "🔴"
    return (
        f'<span class="latency-badge {cls}">'
        f'{icon} {ret_ms}ms retrieve · {llm_ms}ms LLM · {total_ms}ms tổng'
        f'</span>'
    )


def mode_tag_html(mode: str, rerank: bool) -> str:
    label = mode_names.get(mode, mode)
    if mode == "hybrid" and rerank:
        label += "+Rerank"
    return f'<span class="mode-tag">{mode_icons.get(mode,"")} {label}</span>'


def render_citations(contexts: list, show_snip: bool):
    """Hiển thị citation cards bằng Streamlit native components."""
    if not contexts:
        return
    with st.expander(f"📚 Nguồn tài liệu ({len(contexts)})", expanded=True):
        cols_per_row = 2
        for i in range(0, len(contexts), cols_per_row):
            row = contexts[i:i + cols_per_row]
            cols = st.columns(len(row))
            for col, ctx in zip(cols, row):
                with col:
                    idx    = ctx.get("source_idx", "?")
                    title  = ctx.get("title", "Không rõ")
                    author = ctx.get("author", "Không rõ")
                    score  = ctx.get("score", 0)
                    snippet = ctx.get("text", "")[:150] + "…" if ctx.get("text") else ""
                    st.markdown(
                        f"""
                        <div class="citation-card">
                            <span class="citation-num">[{idx}]</span>
                            <span class="citation-title">{title}</span>
                            <div class="citation-author">✍️ {author}</div>
                            <div class="citation-score">Score: {score:.4f}</div>
                            {'<div class="citation-snippet">' + snippet + '</div>' if show_snip and snippet else ''}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# ============================================================
#  Render message
# ============================================================
def render_message(msg: dict, show_snip: bool = False):
    role    = msg["role"]
    content = msg["content"]

    if role == "user":
        st.markdown(
            f'<div class="chat-user"><div class="chat-user-bubble">{content}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        meta        = msg.get("meta", {})
        contexts    = meta.get("contexts", [])
        latency     = meta.get("latency", {})
        suggestions = meta.get("suggestions", [])
        mode        = meta.get("mode", "hybrid")
        rerank      = meta.get("use_reranker", True)

        # Bubble
        st.markdown(
            f'<div class="chat-bot"><div class="chat-bot-inner">'
            f'<div class="chat-bot-bubble">{content}</div>',
            unsafe_allow_html=True,
        )

        # Meta row
        meta_html = '<div class="meta-row">'
        if latency:
            meta_html += latency_badge_html(latency)
        meta_html += mode_tag_html(mode, rerank)
        meta_html += '</div>'
        st.markdown(meta_html + '</div></div>', unsafe_allow_html=True)

        # Citation cards
        if contexts:
            render_citations(contexts, show_snip)

        # Suggestion chips — chỉ cho message mới nhất
        if suggestions and msg.get("is_latest", False):
            st.markdown('<div class="suggest-label">💡 Bạn có thể hỏi tiếp:</div>',
                        unsafe_allow_html=True)
            cols = st.columns(len(suggestions))
            for i, (col, s) in enumerate(zip(cols, suggestions)):
                with col:
                    if st.button(s, key=f"sug_{id(msg)}_{i}", use_container_width=True):
                        st.session_state.pending_query = s
                        st.rerun()


# ============================================================
#  Main chat area
# ============================================================
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div class="welcome-card">
            <span class="welcome-icon">📖</span>
            <h3>Chào mừng đến Thư viện Văn học Việt Nam!</h3>
            <p>Hãy đặt câu hỏi về tác phẩm, tác giả, thể loại hoặc giai đoạn văn học.<br>
            Chatbot sử dụng RAG + Hybrid Search để tìm kiếm chính xác nhất.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="suggest-label" style="margin-top:1.5rem;">🚀 Bắt đầu với:</div>',
                    unsafe_allow_html=True)
        starters = [
            "Truyện Kiều của Nguyễn Du nói về điều gì?",
            "Gợi ý sách của Nguyễn Nhật Ánh",
            "Tôi đang buồn, hãy gợi ý sách phù hợp",
            "Văn học Việt Nam giai đoạn 1930–1945",
        ]
        cols = st.columns(2)
        for i, starter in enumerate(starters):
            with cols[i % 2]:
                if st.button(starter, use_container_width=True, key=f"start_{i}"):
                    st.session_state.pending_query = starter
                    st.rerun()
    else:
        # Đánh dấu message mới nhất
        for i, msg in enumerate(st.session_state.messages):
            msg["is_latest"] = (
                i == len(st.session_state.messages) - 1
                and msg["role"] == "assistant"
            )
        for msg in st.session_state.messages:
            render_message(msg, show_snip=show_snippets)


# ============================================================
#  Chat Input
# ============================================================
user_input = st.chat_input("Nhập câu hỏi về văn học Việt Nam...")

query = None
if st.session_state.pending_query:
    query = st.session_state.pending_query
    st.session_state.pending_query = None
elif user_input:
    query = user_input.strip()


# ============================================================
#  Xử lý câu hỏi mới
# ============================================================
if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("🔍 Đang tìm kiếm và tổng hợp câu trả lời..."):
        try:
            engine = get_engine()
            engine.top_k = top_k  # Apply top_k TRƯỚC khi search

            result = engine.ask(
                query,
                mode=search_mode,
                use_reranker=use_reranker if search_mode == "hybrid" else None,
            )
            answer   = result["answer"]
            contexts = result["contexts"]
            latency  = result["latency"]
        except Exception as e:
            answer   = f"❌ Có lỗi xảy ra: {str(e)}"
            contexts = []
            latency  = {}

    # Sinh câu hỏi gợi ý
    suggestions = []
    if contexts:
        try:
            suggester = load_suggester(engine.gemini)
            suggestions = suggester.suggest(
                query=query,
                contexts=contexts,
                answer=answer,
                n=n_suggest,
            )
        except Exception:
            suggestions = []

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "meta": {
            "contexts":     contexts,
            "latency":      latency,
            "suggestions":  suggestions,
            "mode":         search_mode,
            "use_reranker": use_reranker,
        },
    })

    st.rerun()
