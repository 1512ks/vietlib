"""
preprocess_archive_compact.py
──────────────────────────────
Tạo "Book Card" compact từ data archive để dùng cho RAG.

Thay vì embed full-text (hàng chục ngàn từ/sách), ta tạo 1 document
tổng hợp có cấu trúc ~100-150 từ cho mỗi tác phẩm, gồm:
  - Tên tác phẩm, tác giả
  - Độ dài ước tính (số trang)
  - Trích đoạn mở đầu (200 chars đầu, đã làm sạch)

Output: data/processed/archive_compact/<uuid>.json
Mỗi file là 1 Book Card, dùng trực tiếp cho embedding (1 chunk/file).
"""

import json
import re
import logging
from pathlib import Path
from datetime import datetime

# ── Cấu hình ──────────────────────────────────────────────────────────────────
ARCHIVE_IN   = Path("data/processed/archive")
COMPACT_OUT  = Path("data/processed/archive_compact")
LOG_FILE     = Path("data/preprocess_archive_compact.log")
WORDS_PER_PAGE = 250  # ước tính số từ/trang sách

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_excerpt(text: str, max_chars: int = 300) -> str:
    """Lấy đoạn mở đầu sạch, loại bỏ ký tự đặc biệt và khoảng trắng thừa."""
    text = re.sub(r"\s+", " ", text).strip()
    # Cắt tại ranh giới từ, không cắt giữa chừng
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0]
    return cut + "..."


def estimate_pages(word_count: int) -> str:
    if word_count <= 0:
        return "không rõ"
    pages = word_count // WORDS_PER_PAGE
    if pages < 10:
        return f"~{pages} trang (truyện ngắn/thơ)"
    elif pages < 100:
        return f"~{pages} trang (truyện vừa)"
    else:
        return f"~{pages} trang (tiểu thuyết)"


def build_book_card(doc: dict) -> str:
    """
    Tạo chuỗi văn bản có cấu trúc đại diện cho tác phẩm.
    Đây là nội dung sẽ được embed và lưu vào vector DB.
    """
    title   = doc.get("title", "Không rõ").strip()
    author  = doc.get("author", "Khuyết danh").strip()
    wc      = doc.get("word_count", 0)
    content = doc.get("content", "") or ""
    excerpt = clean_excerpt(content, max_chars=300)
    pages   = estimate_pages(wc)

    parts = [
        f"Tác phẩm: {title}",
        f"Tác giả: {author}",
        f"Độ dài: {wc:,} từ ({pages})",
        f"Ngôn ngữ: Tiếng Việt",
        f"Nguồn: Kho lưu trữ văn học (archive)",
    ]
    if excerpt:
        parts.append(f"Trích đoạn mở đầu: {excerpt}")

    return "\n".join(parts)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not ARCHIVE_IN.exists():
        logger.error(f"Không tìm thấy thư mục: {ARCHIVE_IN}")
        return

    COMPACT_OUT.mkdir(parents=True, exist_ok=True)

    in_files  = list(ARCHIVE_IN.glob("*.json"))
    total     = len(in_files)
    done = skip = err = 0

    logger.info(f"Bắt đầu xử lý {total} archive files → {COMPACT_OUT}")

    for f in in_files:
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))

            title = doc.get("title", "").strip()
            if not title:
                skip += 1
                continue

            card_text = build_book_card(doc)

            compact = {
                "id":           doc["id"],
                "title":        title,
                "author":       doc.get("author", "Khuyết danh"),
                "type":         "work",
                "source":       "archive_compact",
                "content":      card_text,          # ← đây là thứ sẽ được embed
                "word_count":   doc.get("word_count", 0),
                "char_count":   len(card_text),
                "language":     "vi",
                "processed_at": datetime.now().isoformat(),
            }

            out = COMPACT_OUT / f.name
            out.write_text(json.dumps(compact, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            done += 1

            if done % 1000 == 0:
                logger.info(f"  ...{done}/{total} xử lý xong")

        except Exception as e:
            logger.warning(f"Lỗi {f.name}: {e}")
            err += 1

    logger.info("=" * 50)
    logger.info(f"HOÀN THÀNH: {done} book cards | skip={skip} | err={err}")
    logger.info(f"Output: {COMPACT_OUT}")

    # Thống kê nhanh
    samples = list(COMPACT_OUT.glob("*.json"))[:3]
    logger.info("--- Sample book cards ---")
    for s in samples:
        d = json.loads(s.read_text(encoding="utf-8"))
        logger.info(f"  [{d['title'][:50]}] by {d['author']} | card={d['char_count']} chars")


if __name__ == "__main__":
    main()
