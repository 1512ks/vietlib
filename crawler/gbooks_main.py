"""
gbooks_main.py -- Entry point cho Google Books Crawler.

Cách dùng:
    # Crawl toan bo (khong can API key, dung public endpoint)
    python crawler\gbooks_main.py

    # Crawl voi API key (1000 req/ngay, on dinh hon)
    python crawler\gbooks_main.py --api-key YOUR_KEY

    # Test nhanh (chi 3 queries dau, 1 trang/query)
    python crawler\gbooks_main.py --test

    # Reset tien do va crawl lai
    python crawler\gbooks_main.py --reset

    # Xem thong ke hien tai
    python crawler\gbooks_main.py --stats
"""

import sys
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gbooks_crawler import GoogleBooksCrawler
from gbooks_config import (
    ALL_QUERIES, GENRE_QUERIES, AUTHOR_QUERIES,
    DATA_DIR_GBOOKS, PROGRESS_FILE_GBOOKS,
    LOG_FILE, LOG_LEVEL,
    GOOGLE_BOOKS_API_KEY,   # Key mặc định từ config
)


def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def parse_args():
    p = argparse.ArgumentParser(
        description="Google Books Crawler — Thu thập sách tiếng Việt"
    )
    p.add_argument("--api-key",  default="", help="Google Books API key (tuỳ chọn)")
    p.add_argument("--test",     action="store_true", help="Test: 3 queries, 1 trang mỗi query")
    p.add_argument("--reset",    action="store_true", help="Xoá progress, crawl lại từ đầu")
    p.add_argument("--stats",    action="store_true", help="In thống kê, thoát")
    p.add_argument("--genre-only",   action="store_true", help="Chỉ crawl queries theo thể loại")
    p.add_argument("--author-only",  action="store_true", help="Chỉ crawl queries theo tác giả")
    return p.parse_args()



def _log_api_key(logger, key: str):
    """In trạng thái API key ra log."""
    if key:
        masked = key[:8] + "..." + key[-4:]
        logger.info(f"API key: {masked} (Có)")
    else:
        logger.warning("Không có API key — dùng public endpoint (giới hạn ~100 req/ngày)")


def main():
    setup_logging()
    args = parse_args()
    logger = logging.getLogger("gbooks_main")

    # ── Stats ──
    if args.stats:
        n = len(list(DATA_DIR_GBOOKS.glob("gbooks_*.json")))
        print(f"\nGoogle Books files: {n:,}")
        if PROGRESS_FILE_GBOOKS.exists():
            import json
            with open(PROGRESS_FILE_GBOOKS, encoding="utf-8") as f:
                prog = json.load(f)
            print(f"Queries hoàn thành: {len(prog.get('completed_queries', {}))}/{len(ALL_QUERIES)}")
        return

    # ── Reset ──
    if args.reset:
        if PROGRESS_FILE_GBOOKS.exists():
            PROGRESS_FILE_GBOOKS.unlink()
            logger.info("Đã xoá progress. Crawl lại từ đầu.")

    # ── Test mode ──
    if args.test:
        logger.info("=== CHẾ ĐỘ TEST ===")
        import gbooks_config
        gbooks_config.MAX_PAGES_PER_QUERY = 1      # Chỉ 1 trang = 40 results/query
        gbooks_config.MIN_DESCRIPTION_LENGTH = 20  # Nhận nhiều hơn trong test
        test_queries = ALL_QUERIES[:3]
        # Ưu tiên key từ args, fallback sang key trong config
        effective_key = args.api_key or GOOGLE_BOOKS_API_KEY
        _log_api_key(logger, effective_key)
        crawler = GoogleBooksCrawler(api_key=effective_key)
        crawler.crawl_all(test_queries)
        return

    # ── Chọn danh sách queries ──
    if args.genre_only:
        queries = GENRE_QUERIES
        logger.info(f"=== CRAWL THEO THỂ LOẠI ({len(queries)} queries) ===")
    elif args.author_only:
        queries = AUTHOR_QUERIES
        logger.info(f"=== CRAWL THEO TÁC GIẢ ({len(queries)} queries) ===")
    else:
        queries = ALL_QUERIES
        logger.info(f"=== CRAWL TẤT CẢ ({len(queries)} queries) ===")

    effective_key = args.api_key or GOOGLE_BOOKS_API_KEY
    _log_api_key(logger, effective_key)
    crawler = GoogleBooksCrawler(api_key=effective_key)
    crawler.crawl_all(queries)
    logger.info("=== HOÀN TẤT ===")


if __name__ == "__main__":
    main()
