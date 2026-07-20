"""
app_gradio.py -- Chatbot Thư viện Văn học bản GRADIO (để chạy trên Google Colab + share link).

Dùng lại backend: retrieval hybrid bge-m3 (group_works + adaptive-K) + generate Gemini CSKH.
Giao diện chatbot gr.ChatInterface, accent indigo (#6366F1), thẻ sách + giá + nút Mua Tiki
render bằng Markdown, hỗ trợ multi-turn + streaming + từ chối ngoài kho.

Chạy local:  .venv/Scripts/python.exe -m sample_model.app_gradio
Chạy Colab:  from sample_model.app_gradio import demo; demo.launch(share=True)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import gradio as gr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sample_model.retrieval import Retriever, Hit, CONFIDENCE_MIN   # noqa: E402
from sample_model.generate import Generator, strip_citations, cited_indices  # noqa: E402

STARTERS = [
    "Nam Cao có những tác phẩm nào?",
    "Gợi ý sách về thân phận người phụ nữ trong xã hội phong kiến",
    "Vì sao lão Hạc chọn cái chết?",
    "Giá cuốn Chí Phèo bao nhiêu?",
]

# ── Backend (nạp 1 lần) ──
_retriever: Retriever | None = None
_generator: Generator | None = None


def _backend():
    global _retriever, _generator
    if _retriever is None:
        _retriever = Retriever.load()
        _retriever.warm_up()
    if _generator is None:
        _generator = Generator()
    return _retriever, _generator


# ── Render thẻ sách bằng Markdown ──
def _fmt_price(h: Hit) -> str:
    if h.price_int:
        return f"{h.price_int:,}đ".replace(",", ".")
    return "Chưa có giá bán rời"


def _card_md(h: Hit) -> str:
    lines = [f"📖 **{h.title}** — {h.author} · {h.year} · {h.genre}"]
    if h.in_collection and h.edition:
        lines.append(f"📚 *Trong tuyển tập: “{h.edition}”*")
    buy = f"  ·  [🛒 **Mua trên Tiki**]({h.tiki})" if h.tiki else ""
    lines.append(f"💰 **{_fmt_price(h)}**{buy}")
    return "  \n".join(lines)


def _picked_cards(answer: str, hits: list[Hit], max_cards: int = 3) -> list[Hit]:
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


def _is_refusal(low_conf: bool, text: str) -> bool:
    t = text.lower()
    return low_conf and any(m in t for m in
                            ("tiếc quá", "xin lỗi", "chưa giúp", "không tìm thấy"))


# ── Hàm chat (streaming generator) ──
def chat_fn(message, history):
    """message: câu hỏi hiện tại. history: list[{role, content}] các lượt trước."""
    retriever, generator = _backend()
    history = history or []

    # Multi-turn: viết lại câu hỏi nối tiếp thành câu độc lập rồi truy hồi
    search_query = generator.contextualize_query(message, history)
    top_k = retriever.suggest_top_k(search_query)
    hits = retriever.search(search_query, top_k=top_k, group_works=True)
    conf = retriever.confidence(hits)
    low_conf = conf < CONFIDENCE_MIN

    acc = ""
    for chunk in generator.answer_stream(message, hits, low_confidence=low_conf,
                                         history=history):
        acc += chunk
        yield strip_citations(acc)

    if not _is_refusal(low_conf, acc):
        picked = _picked_cards(acc, hits)
        if picked:
            cards = "\n\n---\n\n" + "\n\n".join(_card_md(h) for h in picked)
            yield strip_citations(acc) + cards


# ── Giao diện (bọc ChatInterface trong Blocks để đặt theme indigo #6366F1) ──
theme = gr.themes.Soft(primary_hue="indigo", secondary_hue="violet",
                       neutral_hue="slate", font=["Inter", "system-ui", "sans-serif"])

CSS = """
.gradio-container {max-width: 880px !important; margin: auto !important;}
footer {visibility: hidden;}
"""

with gr.Blocks(title="Trợ lý Thư viện Văn học") as demo:
    gr.Markdown("## 📚 Trợ lý Thư viện Văn học\n"
                "Trợ lý AI tư vấn tác phẩm **văn học Việt Nam** · truy hồi **bge-m3** + "
                "**Gemini** · thẻ sách kèm giá & nút mua Tiki · chỉ trả lời trong phạm vi thư viện.")
    gr.ChatInterface(
        fn=chat_fn,
        examples=STARTERS,
        cache_examples=False,
    )


def launch(**kwargs):
    """Khởi chạy app kèm theme indigo + CSS (Gradio 6: theme/css truyền ở launch)."""
    return demo.launch(theme=theme, css=CSS, **kwargs)


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    launch()
