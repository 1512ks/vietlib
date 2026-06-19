"""
preprocess.py -- Tiền xử lý dữ liệu raw Wikipedia → data/processed/

Các bước xử lý:
    1. Đọc tất cả file JSON trong data/raw/
    2. Deduplicate theo page_id
    3. Clean content: xoá headings (== ... ==), section rác (Xem thêm, Tham khảo...)
    4. Filter categories: bỏ nhãn kỹ thuật nội bộ Wikipedia
    5. Classify type: gán nhãn author / work / concept dựa vào danh mục crawl
    6. Rebuild summary từ content đã clean
    7. Lưu vào data/processed/<type>/<id>.json

Chạy:
    cd C:\\Users\\Admin\\Desktop\\ĐATN
    python preprocess.py
    python preprocess.py --stats        # chỉ xem thống kê
    python preprocess.py --limit 100    # xử lý thử 100 bài
"""

import re
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import defaultdict

# ============================================================
#  CAU HINH
# ============================================================

BASE_DIR  = Path(__file__).parent
RAW_DIR   = BASE_DIR / "data" / "raw"
PROC_DIR  = BASE_DIR / "data" / "processed"

LOG_FILE  = BASE_DIR / "data" / "preprocess.log"

# Nhan phan loai bai viet
TYPE_AUTHOR  = "author"   # Tác giả / nhà văn / nhà thơ
TYPE_WORK    = "work"     # Tác phẩm văn học
TYPE_CONCEPT = "concept"  # Thể loại, khái niệm, lịch sử

# Danh muc nao  type nao (uu tien tu tren xuong duoi)
AUTHOR_CATEGORIES = {
    "Nhà văn Việt Nam", "Nhà thơ Việt Nam", "Tác giả Việt Nam",
    "Nhà văn Hà Nội", "Tiểu sử người Việt Nam",
}

WORK_CATEGORIES = {
    "Tác phẩm văn học Việt Nam", "Tiểu thuyết Việt Nam",
    "Truyện ngắn Việt Nam", "Thơ Việt Nam", "Truyện thơ Việt Nam",
    "Kịch Việt Nam", "Ký Việt Nam", "Truyện tranh Việt Nam",
    "Sách tiếng Việt", "Sách Việt Nam", "Sách thiếu nhi Việt Nam",
    "Văn học thiếu nhi Việt Nam",
}

# Các nhãn kỹ thuật Wikipedia không có nghĩa ngữ nghĩa → loại bỏ
CATEGORY_BLACKLIST_PATTERNS = [
    r"^Bài viết có ",
    r"^Bản mẫu ",
    r"^Trang ",
    r"^Wikipedia:",
    r"^Thể loại:",
    r"mất năm \d+",
    r"sinh năm \d+",
    r"^\d{4}$",                       # năm thuần túy "1820"
    r"^Năm \d+",
]

# Section rác ở cuối bài Wikipedia → xoá từ đây trở đi
JUNK_SECTIONS = [
    "Xem thêm", "Chú thích", "Tham khảo", "Liên kết ngoài",
    "Ghi chú", "Thư mục", "Chú giải", "Nguồn", "Tài liệu tham khảo",
]

# Độ dài tối thiểu content sau khi clean
MIN_CLEAN_LENGTH = 50

# ============================================================
#  LOGGING
# ============================================================

def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )

logger = logging.getLogger(__name__)


# ============================================================
#  BƯỚC 1: ĐỌC TẤT CẢ FILE JSON RAW
# ============================================================

def load_all_raw(limit: Optional[int] = None):
    """
    Đọc tất cả file page_*.json trong data/raw/.
    Trả về dict {page_id: record} (đã deduplicate).
    """
    all_records = {}
    total_read = 0

    for cat_dir in sorted(RAW_DIR.iterdir()):
        if not cat_dir.is_dir():
            continue
        for json_file in sorted(cat_dir.glob("page_*.json")):
            try:
                with open(json_file, encoding="utf-8") as f:
                    record = json.load(f)
            except Exception as e:
                logger.warning(f"Lỗi đọc {json_file.name}: {e}")
                continue

            page_id = record.get("id", "")
            if not page_id:
                continue

            # Deduplicate: giữ bản đầu tiên gặp
            if page_id not in all_records:
                all_records[page_id] = record

            total_read += 1
            if limit and total_read >= limit:
                logger.info(f"Đạt giới hạn --limit {limit}, dừng đọc.")
                return all_records

    logger.info(
        f"Đọc xong: {total_read} files, {len(all_records)} bài duy nhất "
        f"(bỏ {total_read - len(all_records)} bài trùng)"
    )
    return all_records


# ============================================================
#  BƯỚC 2: CLASSIFY TYPE
# ============================================================

def classify_type(record: dict) -> str:
    """
    Phân loại bài viết thành author / work / concept
    dựa theo trường `category` (danh mục crawl gốc).
    """
    cat = record.get("category", "")

    if cat in AUTHOR_CATEGORIES:
        return TYPE_AUTHOR
    if cat in WORK_CATEGORIES:
        return TYPE_WORK
    return TYPE_CONCEPT


# ============================================================
#  BƯỚC 3: CLEAN CONTENT
# ============================================================

def clean_content(text: str) -> str:
    """
    Làm sạch văn bản raw từ Wikipedia:
    1. Cắt bỏ các section rác từ == Xem thêm == trở đi
    2. Xoá dòng heading (== ... ==)
    3. Xoá dòng trống dư thừa
    """
    if not text:
        return ""

    # 1. Xoá đuôi từ section rác
    for section in JUNK_SECTIONS:
        # Pattern: == Xem thêm ==  (có thể có thêm = ở 2 đầu, và khoảng trắng)
        pattern = rf"(?m)^=+\s*{re.escape(section)}\s*=+.*"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            text = text[:match.start()]

    # 2. Xoá dòng heading còn lại (== ... ==, === ... ===)
    text = re.sub(r"(?m)^=+[^=]+=+\s*$", "", text)

    # 3. Xoá dòng trống dư thừa (≥ 2 dòng trống liên tiếp → 1 dòng)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
#  BƯỚC 4: FILTER CATEGORIES
# ============================================================

_blacklist_re = re.compile(
    "|".join(CATEGORY_BLACKLIST_PATTERNS), re.IGNORECASE
)

def filter_categories(cats: list) -> list:
    """Lọc bỏ nhãn kỹ thuật Wikipedia, giữ lại nhãn có nghĩa ngữ nghĩa."""
    return [c for c in cats if not _blacklist_re.search(c)]


# ============================================================
#  BƯỚC 5: REBUILD SUMMARY
# ============================================================

def rebuild_summary(clean_text: str, n_paragraphs: int = 3) -> str:
    """
    Lấy N đoạn văn đầu tiên từ content đã clean làm summary.
    (Thay thế summary cũ có thể chứa heading rác.)
    """
    paragraphs = [p.strip() for p in clean_text.split("\n") if p.strip()]
    return "\n".join(paragraphs[:n_paragraphs])


# ============================================================
#  BƯỚC 6: XỬ LÝ MỘT BÀI
# ============================================================

def process_record(record: dict) -> Optional[dict]:
    """
    Áp dụng toàn bộ pipeline lên 1 bài.
    Trả về dict đã xử lý, hoặc None nếu bài không đủ chất lượng.
    """
    # --- Clean content ---
    raw_content = record.get("content", "")
    clean_text = clean_content(raw_content)

    if len(clean_text) < MIN_CLEAN_LENGTH:
        return None  # Bài quá ngắn sau khi clean → loại bỏ

    # --- Classify ---
    doc_type = classify_type(record)

    # --- Filter categories ---
    raw_cats = record.get("categories", [])
    clean_cats = filter_categories(raw_cats)

    # --- Rebuild summary ---
    summary = rebuild_summary(clean_text)

    return {
        # Metadata định danh
        "id":            record["id"],
        "title":         record.get("title", ""),
        "url":           record.get("url", ""),
        "type":          doc_type,              # author / work / concept [MỚI]

        # Danh mục
        "category":      record.get("category", ""),
        "categories":    clean_cats,            # Đã lọc nhãn kỹ thuật

        # Nội dung
        "summary":       summary,               # Rebuild từ content sạch
        "content":       clean_text,            # Content đã clean

        # Thống kê
        "word_count":    len(clean_text.split()),
        "char_count":    len(clean_text),       # [MỚI]

        # Thông tin crawl & xử lý
        "language":      record.get("language", "vi"),
        "crawled_at":    record.get("crawled_at", ""),
        "last_modified": record.get("last_modified", ""),
        "processed_at":  datetime.now().isoformat(),  # [MỚI]
    }


# ============================================================
#  BƯỚC 7: LƯU KẾT QUẢ
# ============================================================

def save_record(record: dict):
    """Lưu bài đã xử lý vào data/processed/<type>/page_<id>.json"""
    out_dir = PROC_DIR / record["type"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"page_{record['id']}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def save_meta(stats: dict):
    """Lưu file metadata tổng hợp."""
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    out = PROC_DIR / "_meta.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    logger.info(f"Metadata saved: {out}")


# ============================================================
#  MAIN
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Tiền xử lý dữ liệu Wikipedia crawl"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Giới hạn số bài xử lý (dùng để test nhanh)"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Chỉ hiển thị thống kê processed, không xử lý lại"
    )
    return parser.parse_args()


def print_stats():
    """Đọc và in thống kê từ data/processed/."""
    meta_path = PROC_DIR / "_meta.json"
    if not meta_path.exists():
        print("Chưa có dữ liệu processed. Chạy python preprocess.py trước.")
        return
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    print("\n" + "=" * 55)
    print("  THỐNG KÊ DỮ LIỆU PROCESSED")
    print("=" * 55)
    print(f"  Tổng bài đầu vào  : {meta.get('total_raw')}")
    print(f"  Sau deduplicate   : {meta.get('total_unique')}")
    print(f"  Bài đã xử lý OK  : {meta.get('total_processed')}")
    print(f"  Bị loại (quá ngắn): {meta.get('total_skipped')}")
    print(f"  Thời gian xử lý   : {meta.get('processed_at')}")
    print(f"\n  Phân loại:")
    for t, cnt in meta.get("by_type", {}).items():
        print(f"    {t:12s}: {cnt} bài")
    print("=" * 55)


def main():
    setup_logging()
    args = parse_args()

    if args.stats:
        print_stats()
        return

    logger.info("=" * 55)
    logger.info("  BẮT ĐẦU TIỀN XỬ LÝ DỮ LIỆU")
    logger.info("=" * 55)

    # 1. Đọc raw
    raw_records = load_all_raw(limit=args.limit)
    total_unique = len(raw_records)

    # 2. Xử lý từng bài
    counts = defaultdict(int)
    total_processed = 0
    total_skipped = 0

    for i, (page_id, record) in enumerate(raw_records.items(), 1):
        processed = process_record(record)

        if processed is None:
            total_skipped += 1
            continue

        save_record(processed)
        counts[processed["type"]] += 1
        total_processed += 1

        if i % 500 == 0:
            logger.info(f"  [{i}/{total_unique}] đã xử lý {total_processed} bài...")

    # 3. Lưu metadata
    stats = {
        "total_raw":       sum(1 for _ in RAW_DIR.rglob("page_*.json")),
        "total_unique":    total_unique,
        "total_processed": total_processed,
        "total_skipped":   total_skipped,
        "by_type":         dict(counts),
        "processed_at":    datetime.now().isoformat(),
        "min_clean_length": MIN_CLEAN_LENGTH,
    }
    save_meta(stats)

    # 4. In kết quả
    logger.info("=" * 55)
    logger.info("  HOÀN THÀNH TIỀN XỬ LÝ")
    logger.info(f"  Tổng unique  : {total_unique}")
    logger.info(f"  Đã xử lý    : {total_processed}")
    logger.info(f"  Bị loại     : {total_skipped}")
    for t, cnt in counts.items():
        logger.info(f"    {t:12s}: {cnt} bài")
    logger.info(f"  Output       : {PROC_DIR}")
    logger.info("=" * 55)


if __name__ == "__main__":
    main()
