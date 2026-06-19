"""
main_v2.py -- Entry point cho Crawler V2.

Cách dùng:
    # Crawl tat ca (sach + tac gia)
    python main_v2.py

    # Chi crawl sach/tac pham van hoc
    python main_v2.py --books

    # Chi crawl tac gia
    python main_v2.py --authors

    # Test nhanh (5 bai dau moi danh muc)
    python main_v2.py --test

    # Xem thong ke hien tai
    python main_v2.py --stats

    # Reset tien do, crawl lai tu dau
    python main_v2.py --reset
"""

import sys
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from wiki_crawler_v2 import WikiCrawlerV2
from storage_v2 import StorageV2
from config_v2 import LOG_LEVEL, LOG_FILE, BOOK_CATEGORIES, AUTHOR_CATEGORIES, PROGRESS_FILE_V2


def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=fmt,
        datefmt=datefmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def parse_args():
    p = argparse.ArgumentParser(
        description="Crawler V2 — Thu thập tác phẩm văn học & tác giả từ Wikipedia tiếng Việt"
    )
    p.add_argument("--books",   action="store_true", help="Chỉ crawl tác phẩm văn học")
    p.add_argument("--authors", action="store_true", help="Chỉ crawl tác giả")
    p.add_argument("--test",    action="store_true", help="Test: crawl tối đa 5 bài mỗi danh mục")
    p.add_argument("--stats",   action="store_true", help="Hiển thị thống kê rồi thoát")
    p.add_argument("--reset",   action="store_true", help="Xoá progress và crawl lại từ đầu")
    return p.parse_args()


def main():
    setup_logging()
    args = parse_args()
    logger = logging.getLogger("main_v2")

    # ── Xem thống kê ──
    if args.stats:
        StorageV2().print_summary()
        return

    # ── Reset progress ──
    if args.reset:
        if PROGRESS_FILE_V2.exists():
            PROGRESS_FILE_V2.unlink()
            logger.info("Đã xoá progress file. Sẽ crawl lại từ đầu.")
        else:
            logger.info("Không có progress file để xoá.")

    # ── Chế độ test ──
    if args.test:
        logger.info("=== CHẾ ĐỘ TEST: tối đa 5 bài/danh mục ===")
        import config_v2
        config_v2.MAX_ARTICLES_PER_CATEGORY = 5
        config_v2.DELAY_BETWEEN_REQUESTS = 1.0
        config_v2.SUBCATEGORY_MAX_DEPTH = 0

        # Chỉ test 3 danh mục sách + 1 tác giả
        test_book_cats = dict(list(BOOK_CATEGORIES.items())[:3])
        test_auth_cats = dict(list(AUTHOR_CATEGORIES.items())[:1])

        crawler = WikiCrawlerV2()
        if args.books:
            crawler.crawl_books_only(test_book_cats)
        elif args.authors:
            crawler.crawl_authors_only(test_auth_cats)
        else:
            crawler.crawl_books_only(test_book_cats)
            crawler.crawl_authors_only(test_auth_cats)
        return

    # ── Crawl thực sự ──
    crawler = WikiCrawlerV2()

    if args.books:
        logger.info(f"=== CHỈ CRAWL SÁCH ({len(BOOK_CATEGORIES)} danh mục) ===")
        crawler.crawl_books_only()
    elif args.authors:
        logger.info(f"=== CHỈ CRAWL TÁC GIẢ ({len(AUTHOR_CATEGORIES)} danh mục) ===")
        crawler.crawl_authors_only()
    else:
        logger.info(
            f"=== CRAWL TẤT CẢ: {len(BOOK_CATEGORIES)} danh mục sách + "
            f"{len(AUTHOR_CATEGORIES)} danh mục tác giả ==="
        )
        crawler.crawl_all()

    logger.info("=== CRAWL HOÀN TẤT ===")


if __name__ == "__main__":
    main()
