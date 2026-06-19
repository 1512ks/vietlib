"""
main.py -- Entry point: chạy crawler từ command line.

Cách dùng:
    # Crawl toan bo tat ca danh muc
    python main.py

    # Crawl thu 1 danh muc (de kiem tra)
    python main.py --test

    # Crawl danh muc cu the
    python main.py --category "Nhà văn Việt Nam"

    # Xem thong ke hien tai (khong crawl)
    python main.py --stats
"""

import sys
import logging
import argparse
from pathlib import Path

# De Python tim thay cac module trong cung thu muc
sys.path.insert(0, str(Path(__file__).parent))

from wiki_crawler import WikiCrawler
from storage import Storage
from config import LOG_LEVEL, LOG_FILE, CATEGORIES


def setup_logging():
    """Cau hinh logging: hien thi tren terminal + luu ra file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=fmt,
        datefmt=datefmt,
        handlers=[
            logging.StreamHandler(sys.stdout),          # In ra terminal
            logging.FileHandler(LOG_FILE, encoding="utf-8"),  # Lưu ra file
        ],
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Wikipedia Crawler — Thu thập tài liệu tiếng Việt"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Chế độ thử: chỉ crawl danh mục đầu tiên, tối đa 10 bài",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Chỉ crawl một danh mục cụ thể (ví dụ: 'Nhà văn Việt Nam')",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Hiển thị thống kê crawl hiện tại rồi thoát",
    )
    return parser.parse_args()


def main():
    setup_logging()
    args = parse_args()
    logger = logging.getLogger("main")

    # ----- Chỉ xem thống kê -----
    if args.stats:
        storage = Storage()
        storage.print_summary()
        return

    # ----- Chế độ TEST -----
    if args.test:
        logger.info("=== CHẾ ĐỘ THỬ: crawl tối đa 10 bài từ danh mục đầu tiên ===")

        import config
        config.MAX_ARTICLES_PER_CATEGORY = 10
        config.DELAY_BETWEEN_REQUESTS = 1.0

        # Chỉ truyền 1 danh mục vào crawl_all() — không cần override config
        first_key = next(iter(CATEGORIES))
        test_cats = {first_key: CATEGORIES[first_key]}

        crawler = WikiCrawler()
        crawler.crawl_all(categories=test_cats)
        return

    # ----- Crawl một danh mục -----
    if args.category:
        if args.category not in CATEGORIES:
            logger.error(f"Danh mục '{args.category}' không có trong config.")
            logger.info(f"Các danh mục hợp lệ: {list(CATEGORIES.keys())}")
            sys.exit(1)

        single_cat = {args.category: CATEGORIES[args.category]}
        logger.info(f"=== CHỈ CRAWL: '{args.category}' ===")

        crawler = WikiCrawler()
        crawler.crawl_all(categories=single_cat)
        return

    # ----- Crawl TẤT CẢ (mặc định) -----
    logger.info("=== BẮT ĐẦU CRAWL TẤT CẢ DANH MỤC ===")
    logger.info(f"Danh sách: {list(CATEGORIES.keys())}")

    crawler = WikiCrawler()
    crawler.crawl_all()

    logger.info("=== CRAWL HOÀN TẤT ===")


if __name__ == "__main__":
    main()
