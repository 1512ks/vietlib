"""
preprocess_gbooks.py -- Tiền xử lý dữ liệu Google Books raw → data/processed/gbooks/

Pipeline:
    1. Load tất cả gbooks_*.json từ data/raw_v2/books/
    2. Lọc ngôn ngữ: chỉ giữ language == 'vi'
    3. Lọc content: char_count >= MIN_CHARS
    4. Lọc chủ đề: bỏ sách không liên quan văn học VN
    5. Deduplicate theo title + author
    6. Clean text: normalize whitespace, bỏ ký tự lạ
    7. Lưu vào data/processed/gbooks/gbooks_<id>.json

Chạy:
    python preprocess_gbooks.py              # toàn bộ pipeline
    python preprocess_gbooks.py --stats      # xem thống kê
    python preprocess_gbooks.py --dry-run    # chạy thử, không lưu file
"""

import re
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Optional

# ============================================================
#  CAU HINH
# ============================================================
BASE_DIR   = Path(__file__).parent
RAW_DIR    = BASE_DIR / "data" / "raw_v2" / "books"
OUT_DIR    = BASE_DIR / "data" / "processed" / "gbooks"
LOG_FILE   = BASE_DIR / "data" / "preprocess_gbooks.log"
META_FILE  = BASE_DIR / "data" / "processed" / "gbooks_meta.json"

# Nguong loc
MIN_CHARS       = 20    # Giam xuong de giu lai nhieu sach hon
KEEP_LANGS      = {"vi"} # Chỉ giữ tiếng Việt

# Tu khoa xac dinh sach KHONG lien quan van hoc VN
# (kiem tra trong title + categories + genre, case-insensitive)
IRRELEVANT_KEYWORDS = [
    "học tiếng anh", "luyện thi", "foreign language study",
    "nông nghiệp", "thú y", "canh tác", "trồng trọt",
    "y học", "y tế", "dược", "bệnh viện",
    "kỹ thuật", "công nghệ", "điện tử", "tin học",
    "toán học", "vật lý", "hóa học",
    "kinh tế", "kế toán", "tài chính", "ngân hàng",
    "luật", "pháp luật",
    "nấu ăn", "ẩm thực", "cookbook",
    "du lịch", "travel guide",
    "microsoft", "excel", "word", "powerpoint", "photoshop",
    "java", "python programming", "lập trình",
]

# Từ khóa bảo vệ (WHITELIST): NẾU sách có chữ này, CHẮC CHẮN GIỮ LẠI dù có chứa keyword irrelevant
LITERATURE_KEYWORDS = [
    "tiểu thuyết", "truyện ngắn", "truyện dài", "truyện thơ",
    "thơ", "tản văn", "bút ký", "hồi ký", "ký sự",
    "văn học", "tác phẩm", "nhà văn", "nhà thơ",
    "kịch", "tuyển tập", "truyện cổ tích", "chí phèo", "vợ nhặt",
    "fiction", "novel", "poetry", "short stories",
    "literary", "literature", "biography", "memoir",
    "việt nam", "vietnamese", "ngôn tình", "kiếm hiệp",
    "văn xuôi", "ngụ ngôn", "truyện cười", "cổ tích", "tác giả",
]

# ============================================================
#  LOGGING
# ============================================================
def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )

logger = logging.getLogger(__name__)


# ============================================================
#  BƯỚC 1: LOAD
# ============================================================
def load_raw(limit: Optional[int] = None) -> list:
    files = sorted(RAW_DIR.glob("gbooks_*.json"))
    if limit:
        files = files[:limit]
    docs = []
    errors = 0
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            docs.append(d)
        except Exception as e:
            logger.warning(f"Lỗi đọc {f.name}: {e}")
            errors += 1
    logger.info(f"Đọc xong: {len(docs)} file gbooks ({errors} lỗi)")
    return docs


# ============================================================
#  BƯỚC 2: LỌC NGÔN NGỮ
# ============================================================
def filter_language(docs: list) -> tuple[list, int]:
    kept = [d for d in docs if d.get("language", "") in KEEP_LANGS]
    dropped = len(docs) - len(kept)
    logger.info(f"[Lọc ngôn ngữ] Giữ: {len(kept)} | Bỏ: {dropped} (language != vi)")
    return kept, dropped


# ============================================================
#  BƯỚC 3: LỌC CONTENT NGẮN
# ============================================================
def filter_short(docs: list) -> tuple[list, int]:
    kept = []
    dropped = 0
    for d in docs:
        content = d.get("content", "") or d.get("summary", "") or ""
        if len(content) >= MIN_CHARS:
            kept.append(d)
        else:
            dropped += 1
    logger.info(f"[Lọc ngắn]    Giữ: {len(kept)} | Bỏ: {dropped} (content < {MIN_CHARS} chars)")
    return kept, dropped


# ============================================================
#  BƯỚC 4: LỌC CHỦ ĐỀ KHÔNG LIÊN QUAN
# ============================================================
def _get_text_for_topic_check(doc: dict) -> str:
    """Gộp title + categories + genre để kiểm tra chủ đề."""
    parts = [
        doc.get("title", ""),
        " ".join(doc.get("categories", [])),
        doc.get("genre", "") or "",
        doc.get("crawl_category", ""),
    ]
    return " ".join(parts).lower()

def filter_irrelevant(docs: list) -> tuple[list, int]:
    kept = []
    dropped = 0
    for doc in docs:
        text = _get_text_for_topic_check(doc)
        
        # Ưu tiên giữ lại sách văn học dựa vào danh sách bảo vệ
        is_literature = any(kw in text for kw in LITERATURE_KEYWORDS)
        if is_literature:
            kept.append(doc)
            continue
            
        # Bỏ nếu chứa từ khóa không liên quan
        if any(kw in text for kw in IRRELEVANT_KEYWORDS):
            dropped += 1
            continue
        kept.append(doc)
    logger.info(f"[Lọc chủ đề]  Giữ: {len(kept)} | Bỏ: {dropped} (không liên quan VH)")
    return kept, dropped


# ============================================================
#  BƯỚC 5: DEDUPLICATE
# ============================================================
def deduplicate(docs: list) -> tuple[list, int]:
    """
    Deduplicate theo (title.lower(), author.lower()).
    Giữ bản có content dài nhất.
    """
    seen: dict[tuple, dict] = {}
    for doc in docs:
        key = (
            doc.get("title", "").strip().lower(),
            doc.get("author", "").strip().lower(),
        )
        if key not in seen:
            seen[key] = doc
        else:
            # Giữ bản content dài hơn
            existing_len = len(seen[key].get("content", "") or "")
            new_len = len(doc.get("content", "") or "")
            if new_len > existing_len:
                seen[key] = doc

    dropped = len(docs) - len(seen)
    result = list(seen.values())
    logger.info(f"[Deduplicate]  Giữ: {len(result)} | Bỏ: {dropped} (trùng title+author)")
    return result, dropped


# ============================================================
#  BƯỚC 6: CLEAN TEXT
# ============================================================
def clean_text(text: str) -> str:
    """Normalize whitespace, bỏ ký tự điều khiển."""
    if not text:
        return ""
    # Bỏ ký tự điều khiển (trừ newline)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def process_doc(doc: dict) -> dict:
    """Áp dụng clean text và chuẩn hóa trường."""
    content = clean_text(doc.get("content", "") or "")
    summary = doc.get("summary", "") or ""
    if not summary and content:
        summary = content[:500]
    summary = clean_text(summary)

    return {
        # Định danh
        "id":               doc.get("id", ""),
        "title":            doc.get("title", "").strip(),
        "url":              doc.get("url", ""),
        "source":           "google_books",
        "wikidata_id":      doc.get("wikidata_id", ""),

        # Metadata tác phẩm
        "author":           doc.get("author", "").strip(),
        "authors":          doc.get("authors", []),
        "publication_year": doc.get("publication_year", ""),
        "genre":            doc.get("genre", ""),
        "genres":           doc.get("genres", []),
        "publisher":        doc.get("publisher", ""),
        "page_count":       doc.get("page_count", 0),
        "isbn":             doc.get("isbn", ""),
        "isbn_list":        doc.get("isbn_list", []),
        "cover_url":        doc.get("cover_url", ""),

        # Nội dung
        "summary":          summary,
        "content":          content,

        # Phân loại
        "categories":       doc.get("categories", []),
        "crawl_category":   doc.get("crawl_category", ""),
        "language":         doc.get("language", "vi"),

        # Thống kê
        "word_count":       len(content.split()),
        "char_count":       len(content),

        # Timestamps
        "crawled_at":       doc.get("crawled_at", ""),
        "processed_at":     datetime.now().isoformat(),
    }


# ============================================================
#  BƯỚC 7: LƯU
# ============================================================
def save_docs(docs: list, dry_run: bool = False) -> int:
    if dry_run:
        logger.info(f"[DRY RUN] Sẽ lưu {len(docs)} file vào {OUT_DIR}")
        return len(docs)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0
    for doc in docs:
        doc_id = doc["id"]
        out_file = OUT_DIR / f"{doc_id}.json"
        try:
            out_file.write_text(
                json.dumps(doc, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            saved += 1
        except Exception as e:
            logger.warning(f"Lỗi lưu {doc_id}: {e}")
    logger.info(f"[Lưu] {saved} file → {OUT_DIR}")
    return saved


def save_meta(stats: dict):
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    META_FILE.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    logger.info(f"[Meta] → {META_FILE}")


# ============================================================
#  PRINT STATS (khi dùng --stats)
# ============================================================
def print_stats():
    if not META_FILE.exists():
        print("Chưa có dữ liệu. Chạy python preprocess_gbooks.py trước.")
        return
    meta = json.loads(META_FILE.read_text(encoding="utf-8"))
    print("\n" + "=" * 55)
    print("  THỐNG KÊ GBOOKS PROCESSED")
    print("=" * 55)
    print(f"  Raw input        : {meta.get('total_raw'):,}")
    print(f"  Sau lọc ngôn ngữ : {meta.get('after_lang'):,}")
    print(f"  Sau lọc ngắn     : {meta.get('after_short'):,}")
    print(f"  Sau lọc chủ đề   : {meta.get('after_topic'):,}")
    print(f"  Sau deduplicate  : {meta.get('after_dedup'):,}")
    print(f"  Đã lưu           : {meta.get('saved'):,}")
    print(f"  Tổng bỏ          : {meta.get('total_dropped'):,}")
    print(f"  Processed at     : {meta.get('processed_at')}")
    # Word count
    wc = meta.get("word_count_dist", {})
    if wc:
        print(f"\n  Phân bố word count:")
        for k, v in wc.items():
            print(f"    {k:>12}: {v:,}")
    print("=" * 55)


# ============================================================
#  MAIN
# ============================================================
def parse_args():
    p = argparse.ArgumentParser(description="Preprocess Google Books data")
    p.add_argument("--limit",   type=int, default=None, help="Giới hạn số file đọc (test)")
    p.add_argument("--stats",   action="store_true",    help="Chỉ xem thống kê")
    p.add_argument("--dry-run", action="store_true",    help="Chạy thử, không lưu file")
    p.add_argument("--no-filter-topic", action="store_true", help="Không lọc chủ đề (giữ các sách không liên quan VH)")
    return p.parse_args()


def main():
    setup_logging()
    args = parse_args()

    if args.stats:
        print_stats()
        return

    logger.info("=" * 55)
    logger.info("  BẮT ĐẦU PREPROCESS GBOOKS")
    logger.info("=" * 55)

    # Pipeline
    docs = load_raw(limit=args.limit)
    total_raw = len(docs)

    docs, d_lang  = filter_language(docs)
    after_lang = len(docs)

    docs, d_short = filter_short(docs)
    after_short = len(docs)

    if args.no_filter_topic:
        d_topic = 0
    else:
        docs, d_topic = filter_irrelevant(docs)
    after_topic = len(docs)

    docs, d_dedup = deduplicate(docs)
    after_dedup = len(docs)

    # Clean & chuẩn hóa
    docs = [process_doc(d) for d in docs]

    # Thống kê word count
    wc_dist = {"<50": 0, "50-200": 0, "200-500": 0, ">500": 0}
    for d in docs:
        wc = d["word_count"]
        if wc < 50:       wc_dist["<50"] += 1
        elif wc < 200:    wc_dist["50-200"] += 1
        elif wc < 500:    wc_dist["200-500"] += 1
        else:             wc_dist[">500"] += 1

    # Lưu
    saved = save_docs(docs, dry_run=args.dry_run)

    # Meta
    stats = {
        "total_raw":     total_raw,
        "after_lang":    after_lang,
        "after_short":   after_short,
        "after_topic":   after_topic,
        "after_dedup":   after_dedup,
        "saved":         saved,
        "total_dropped": total_raw - saved,
        "word_count_dist": wc_dist,
        "processed_at":  datetime.now().isoformat(),
        "min_chars":     MIN_CHARS,
        "dry_run":       args.dry_run,
        "no_filter_topic": args.no_filter_topic,
    }
    if not args.dry_run:
        save_meta(stats)

    # Summary
    logger.info("=" * 55)
    logger.info("  KẾT QUẢ PREPROCESS")
    logger.info(f"  Raw              : {total_raw:,}")
    logger.info(f"  Sau lọc ngôn ngữ : {after_lang:,}  (-{d_lang})")
    logger.info(f"  Sau lọc ngắn     : {after_short:,}  (-{d_short})")
    logger.info(f"  Sau lọc chủ đề   : {after_topic:,}  (-{d_topic})")
    logger.info(f"  Sau deduplicate  : {after_dedup:,}  (-{d_dedup})")
    logger.info(f"  Đã lưu           : {saved:,}")
    logger.info(f"  Word count dist  : {wc_dist}")
    logger.info("=" * 55)


if __name__ == "__main__":
    main()
