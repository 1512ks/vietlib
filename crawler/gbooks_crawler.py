"""
gbooks_crawler.py -- Crawler Google Books: tìm kiếm trực tiếp sách tiếng Việt.

Luồng:
  Với mỗi query trong ALL_QUERIES:
    → Gọi Google Books API (phân trang, max 1000 kết quả/query)
    → Parse volumeInfo: title, authors, description, publishedDate, categories, ISBN...
    → Lưu thành BookArticle JSON vào data/raw_v2/books/gbooks_{volumeId}.json
    → Bỏ qua nếu đã tồn tại (resume-safe)
"""

import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log,
)
from tqdm import tqdm

from models_v2 import BookArticle
from gbooks_config import (
    GOOGLE_BOOKS_API_KEY,
    GOOGLE_BOOKS_API_URL,
    DELAY_BETWEEN_REQUESTS,
    MAX_RETRIES,
    RETRY_WAIT_MIN,
    RETRY_WAIT_MAX,
    MAX_RESULTS_PER_REQUEST,
    MAX_PAGES_PER_QUERY,
    MIN_DESCRIPTION_LENGTH,
    ALL_QUERIES,
    DATA_DIR_GBOOKS,
    PROGRESS_FILE_GBOOKS,
    LOG_FILE,
)

logger = logging.getLogger(__name__)


class GoogleBooksCrawler:
    """
    Crawler tìm kiếm sách tiếng Việt qua Google Books API.

    Dùng:
        crawler = GoogleBooksCrawler(api_key="YOUR_KEY")
        crawler.crawl_all()
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or GOOGLE_BOOKS_API_KEY
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DATN-BookCrawler/1.0"})
        self.progress = self._load_progress()
        self.total_saved = 0
        self.total_skipped = 0
        self.total_errors = 0

    # ===========================================================
    #  PUBLIC API
    # ===========================================================
    def crawl_all(self, queries: List[str] = None):
        """Crawl tất cả queries trong danh sách."""
        queries = queries or ALL_QUERIES
        logger.info("=" * 60)
        logger.info(f"  GOOGLE BOOKS CRAWLER — {len(queries)} queries")
        logger.info(f"  API Key: {'Có' if self.api_key else 'Không (limited)'}")
        logger.info("=" * 60)

        for query in queries:
            if self.progress["completed_queries"].get(query):
                logger.info(f"[SKIP] '{query}' đã crawl xong.")
                continue

            logger.info(f"\n→ Query: \"{query}\"")
            count = self._crawl_query(query)
            self.progress["completed_queries"][query] = {
                "count": count,
                "finished_at": datetime.now().isoformat(),
            }
            self._save_progress()
            logger.info(f"  Lưu {count} sách mới từ '{query}'")
            time.sleep(DELAY_BETWEEN_REQUESTS * 2)

        self._print_summary()

    # ===========================================================
    #  CRAWL 1 QUERY (với phân trang)
    # ===========================================================
    def _crawl_query(self, query: str) -> int:
        """Phân trang qua tất cả kết quả của 1 query."""
        saved = 0
        total_items = None

        pbar = tqdm(
            range(MAX_PAGES_PER_QUERY),
            desc=f"{query[:30]}",
            unit="trang",
        )

        for page_idx in pbar:
            start_index = page_idx * MAX_RESULTS_PER_REQUEST

            # Dừng nếu đã lấy hết kết quả
            if total_items is not None and start_index >= total_items:
                break

            try:
                data = self._search(query, start_index)
            except Exception as e:
                self.total_errors += 1
                logger.warning(f"Lỗi trang {page_idx}: {e}")
                break

            if not data or "items" not in data:
                break

            # Cập nhật tổng số kết quả
            if total_items is None:
                total_items = min(
                    data.get("totalItems", 0),
                    MAX_PAGES_PER_QUERY * MAX_RESULTS_PER_REQUEST,
                )
                logger.info(
                    f"  Tổng kết quả: {data.get('totalItems', 0)} "
                    f"(crawl tối đa {total_items})"
                )

            items = data.get("items", [])
            for item in items:
                volume_id = item.get("id", "")
                if not volume_id:
                    continue

                filepath = DATA_DIR_GBOOKS / f"gbooks_{volume_id}.json"
                if filepath.exists():
                    self.total_skipped += 1
                    continue

                article = self._parse_volume(item, query)
                if article is None:
                    continue

                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(article.to_dict(), f, ensure_ascii=False, indent=2)
                    saved += 1
                    self.total_saved += 1
                    pbar.set_postfix(saved=saved, title=article.title[:20])
                except Exception as e:
                    logger.warning(f"Lỗi lưu {volume_id}: {e}")

            time.sleep(DELAY_BETWEEN_REQUESTS)

        return saved

    # ===========================================================
    #  PARSE 1 VOLUME
    # ===========================================================
    def _parse_volume(self, item: dict, crawl_query: str) -> Optional[BookArticle]:
        """Parse Google Books volumeInfo → BookArticle."""
        volume_id = item.get("id", "")
        vol = item.get("volumeInfo", {})

        title = vol.get("title", "").strip()
        if not title:
            return None

        # Bỏ sách không có mô tả hoặc mô tả quá ngắn
        description = vol.get("description", "").strip()
        if len(description) < MIN_DESCRIPTION_LENGTH:
            return None

        # Tác giả
        authors_raw = vol.get("authors", [])
        author = authors_raw[0] if authors_raw else ""
        authors = authors_raw[:5]

        # Năm xuất bản
        pub_date = vol.get("publishedDate", "")
        pub_year = self._extract_year(pub_date)

        # Thể loại
        categories = vol.get("categories", [])
        genre = categories[0] if categories else ""
        # Bổ sung mapping thể loại tiếng Anh → tiếng Việt
        genre = self._map_genre(genre)
        genres = [self._map_genre(c) for c in categories]

        # ISBN
        isbn_list = []
        for id_info in vol.get("industryIdentifiers", []):
            if id_info.get("type") in ("ISBN_13", "ISBN_10"):
                isbn_list.append(id_info.get("identifier", ""))
        isbn = next((x for x in isbn_list if len(x) == 13), "")
        if not isbn and isbn_list:
            isbn = isbn_list[0]

        # Ảnh bìa
        image_links = vol.get("imageLinks", {})
        cover_url = (
            image_links.get("thumbnail", "")
            or image_links.get("smallThumbnail", "")
        )

        # URL sách
        url = vol.get("infoLink", "") or f"https://books.google.com/books?id={volume_id}"

        # Publisher
        publisher = vol.get("publisher", "")

        # Số trang
        page_count = vol.get("pageCount", 0) or 0

        # Content = description (Google Books không cung cấp full text)
        content = description
        summary = description[:500] if len(description) > 500 else description

        return BookArticle(
            id=f"gbooks_{volume_id}",
            title=title,
            url=url,
            wikidata_id="",
            summary=summary,
            content=content,
            author=author,
            authors=authors,
            publication_year=pub_year,
            genre=genre,
            genres=genres,
            isbn=isbn,
            isbn_list=isbn_list,
            publisher=publisher,
            page_count=page_count,
            cover_url=cover_url,
            source="google_books",
            author_source="google_books" if author else "",
            year_source="google_books" if pub_year else "",
            genre_source="google_books" if genre else "",
            crawl_category=crawl_query,
            categories=categories,
            language=vol.get("language", "vi"),
            word_count=len(content.split()),
            char_count=len(content),
            crawled_at=datetime.now().isoformat(),
            last_modified="",
        )

    # ===========================================================
    #  HELPERS
    # ===========================================================
    def _extract_year(self, date_str: str) -> str:
        """Trích năm từ chuỗi ngày dạng '2005', '2005-03', '2005-03-15'."""
        if not date_str:
            return ""
        m = re.search(r'\b(19|20)\d{2}\b', date_str)
        return m.group(0) if m else ""

    # Map thể loại tiếng Anh sang tiếng Việt (phổ biến nhất)
    _GENRE_MAP = {
        "fiction":              "Tiểu thuyết",
        "novel":                "Tiểu thuyết",
        "short stories":        "Truyện ngắn",
        "poetry":               "Thơ",
        "juvenile fiction":     "Văn học thiếu nhi",
        "juvenile nonfiction":  "Sách thiếu nhi",
        "biography":            "Tiểu sử",
        "history":              "Lịch sử",
        "drama":                "Kịch",
        "literary collections": "Tuyển tập văn học",
        "literary criticism":   "Phê bình văn học",
    }

    def _map_genre(self, genre: str) -> str:
        if not genre:
            return ""
        lower = genre.lower().strip()
        for en, vi in self._GENRE_MAP.items():
            if en in lower:
                return vi
        return genre  # Giữ nguyên nếu không map được

    # ===========================================================
    #  API CALL VỚI RETRY
    # ===========================================================
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _search(self, query: str, start_index: int = 0) -> dict:
        """Gọi Google Books volumes.list API."""
        params = {
            "q":           query,
            # langRestrict bị bỏ: Google Books không tag ngôn ngữ nhất quán
            # → sách tiếng Việt có thể bị gán nhãn 'en' hoặc ngôn ngữ khác
            "maxResults":  MAX_RESULTS_PER_REQUEST,
            "startIndex":  start_index,
            "printType":   "books",
            "orderBy":     "relevance",
        }
        if self.api_key:
            params["key"] = self.api_key

        resp = self.session.get(GOOGLE_BOOKS_API_URL, params=params, timeout=20)

        if resp.status_code == 429:
            logger.warning("429 Too Many Requests — chờ 60s...")
            time.sleep(60)
            raise requests.ConnectionError("Rate limited")

        if resp.status_code == 403:
            logger.error("403 Forbidden — kiểm tra API key hoặc quota")
            raise RuntimeError("Google Books API 403")

        resp.raise_for_status()
        return resp.json()

    # ===========================================================
    #  PROGRESS + SUMMARY
    # ===========================================================
    def _load_progress(self) -> dict:
        if PROGRESS_FILE_GBOOKS.exists():
            with open(PROGRESS_FILE_GBOOKS, encoding="utf-8") as f:
                data = json.load(f)
            n = len(data.get("completed_queries", {}))
            logger.info(f"Resume: {n} queries đã xong")
            return data
        return {
            "started_at": datetime.now().isoformat(),
            "completed_queries": {},
        }

    def _save_progress(self):
        PROGRESS_FILE_GBOOKS.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE_GBOOKS, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

    def _print_summary(self):
        n_total = len(list(DATA_DIR_GBOOKS.glob("gbooks_*.json")))
        print("\n" + "=" * 55)
        print("  TỔNG KẾT GOOGLE BOOKS CRAWLER")
        print("=" * 55)
        print(f"  Sách mới lưu   : {self.total_saved:,}")
        print(f"  Bỏ qua (đã có): {self.total_skipped:,}")
        print(f"  Lỗi            : {self.total_errors}")
        print(f"  Tổng file gbooks: {n_total:,}")
        print("=" * 55)
