"""
wiki_crawler.py -- Crawler chính: gọi Wikipedia API, xử lý rate limiting và retry.

Luồng hoạt động:
    1. Lấy danh sách bài từ Category API (phân trang)
    2. Với mỗi bài, gọi Page Content API để lấy nội dung
    3. Rate limiting: ngủ DELAY_BETWEEN_REQUESTS giây giữa mỗi request
    4. Nếu gặp lỗi mạng → retry với exponential backoff (tenacity)
    5. Lưu mỗi bài thành 1 file JSON riêng (qua Storage)
"""

import time
import logging
from datetime import datetime
from typing import Iterator, Optional, Dict

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from tqdm import tqdm

from models import WikiArticle
from storage import Storage
from config import (
    USER_AGENT,
    WIKI_LANGUAGE,
    WIKI_BASE_URL,
    DELAY_BETWEEN_REQUESTS,
    DELAY_BETWEEN_CATEGORIES,
    MAX_RETRIES,
    RETRY_WAIT_MIN,
    RETRY_WAIT_MAX,
    MIN_CONTENT_LENGTH,
    MAX_ARTICLES_PER_CATEGORY,
    SUBCATEGORY_MAX_DEPTH,
    CATEGORIES as _DEFAULT_CATEGORIES,
)

logger = logging.getLogger(__name__)


class WikiCrawler:
    """
    Crawler Wikipedia tiếng Việt với rate limiting và retry tự động.

    Ví dụ sử dụng:
        crawler = WikiCrawler()
        crawler.crawl_all()
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.storage = Storage()
        self.total_articles = 0
        self.total_errors = 0

    # ===========================================================
    #  PUBLIC: CRAWL TOÀN BỘ
    # ===========================================================
    def crawl_all(self, categories: dict = None):
        """
        Crawl toàn bộ các danh mục.
        Nếu truyền `categories`, sử dụng bộ đó thay vì config.CATEGORIES.
        """
        cats = categories if categories is not None else _DEFAULT_CATEGORIES
        logger.info(f"Bắt đầu crawl {len(cats)} danh mục...")

        for display_name, wiki_category in cats.items():
            if self.storage.is_category_done(display_name):
                logger.info(f"[SKIP] '{display_name}' đã crawl xong trước đó.")
                continue

            logger.info(f"\n→ Crawl danh mục: '{display_name}'")
            count = self._crawl_category(display_name, wiki_category)
            self.storage.mark_category_done(display_name, count)

            # Nghỉ giữa các danh mục
            logger.info(f"Nghỉ {DELAY_BETWEEN_CATEGORIES}s trước danh mục tiếp...")
            time.sleep(DELAY_BETWEEN_CATEGORIES)

        self.storage.update_stats(self.total_articles, self.total_errors)
        self.storage.save_summary_json()
        self.storage.print_summary()

    # ===========================================================
    #  CRAWL MỘT DANH MỤC (+ đệ quy subcategory)
    # ===========================================================
    def _crawl_category(self, display_name: str, wiki_category: str) -> int:
        """
        Crawl toàn bộ bài trong một danh mục Wikipedia,
        bao gồm tất cả danh mục con đến độ sâu SUBCATEGORY_MAX_DEPTH.
        Trả về số bài đã lưu thành công.
        """
        logger.info(f"Thu thập page_id từ cây danh mục '{display_name}' (depth={SUBCATEGORY_MAX_DEPTH})...")
        visited_cats: set = set()
        page_ids = list(self._collect_all_page_ids(wiki_category, depth=0, visited=visited_cats))
        # Loại trùng
        page_ids = list(dict.fromkeys(page_ids))
        logger.info(f"Tổng: {len(page_ids)} bài (từ {len(visited_cats)} danh mục) trong '{display_name}'")

        if MAX_ARTICLES_PER_CATEGORY:
            page_ids = page_ids[:MAX_ARTICLES_PER_CATEGORY]

        count = 0
        pbar = tqdm(page_ids, desc=display_name[:30], unit="bài")

        for page_id in pbar:
            # Bỏ qua nếu đã crawl
            if self.storage.article_exists(str(page_id), display_name):
                pbar.set_postfix(status="cached")
                continue

            try:
                article = self._fetch_article(page_id, display_name)

                if article is None:
                    continue

                self.storage.save_article(article)
                count += 1
                self.total_articles += 1
                pbar.set_postfix(saved=count, title=article.title[:20])

            except Exception as e:
                self.total_errors += 1
                logger.warning(f"Lỗi page_id={page_id}: {e}")

            finally:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        return count

    # ===========================================================
    #  ĐỆ QUY THU THẬP PAGE_ID TỪ CÂY DANH MỤC
    # ===========================================================
    def _collect_all_page_ids(
        self,
        wiki_category: str,
        depth: int,
        visited: set,
    ):
        """
        Đệ quy thu thập tất cả page_id từ danh mục và các danh mục con.
        - depth=0: chỉ bài trực tiếp
        - depth=1: bài + subcategory cấp 1
        - depth=SUBCATEGORY_MAX_DEPTH: toàn bộ cây
        visited: set tên danh mục đã ghé (tránh vòng lặp vô hạn)
        """
        if wiki_category in visited:
            return
        visited.add(wiki_category)

        # 1. Truyền các bài trực tiếp trong danh mục này
        yield from self._get_pages_in_category(wiki_category)
        time.sleep(DELAY_BETWEEN_REQUESTS)

        # 2. Nếu chưa đến giới hạn độ sâu → đệ quy vào subcategory
        if depth < SUBCATEGORY_MAX_DEPTH:
            for subcat_title in self._get_subcategories(wiki_category):
                time.sleep(DELAY_BETWEEN_REQUESTS)
                yield from self._collect_all_page_ids(subcat_title, depth + 1, visited)

    # ===========================================================
    #  LẤY BÀI TRỰC TIẼ P TRONG DANH MỤC
    # ===========================================================
    def _get_pages_in_category(self, wiki_category: str):
        """
        Trả về page_id các bài Viết (không phải subcategory) trong danh mục.
        """
        yield from self._query_categorymembers(wiki_category, cmtype="page")

    # ===========================================================
    #  LẤY DANH MỤC CON (subcategories)
    # ===========================================================
    def _get_subcategories(self, wiki_category: str):
        """
        Trả về tên (string) các subcategory trong danh mục,
        đã bỏ tiền tố 'Thể_loại:' để dùng trong đệ quy.
        """
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Thể_loại:{wiki_category}",
            "cmlimit": 500,
            "cmtype": "subcat",
            "format": "json",
        }
        while True:
            data = self._api_call(params)
            members = data.get("query", {}).get("categorymembers", [])
            for m in members:
                # title dạng "Thể loại:Nhà văn miền Nam" → bỏ prefix
                title = m["title"].replace("Thể loại:", "").replace("Thể_loại:", "")
                yield title
            if "continue" in data:
                params.update(data["continue"])
                time.sleep(DELAY_BETWEEN_REQUESTS)
            else:
                break

    # ===========================================================
    #  HELPER: GỌI categorymembers API (phân trang)
    # ===========================================================
    def _query_categorymembers(self, wiki_category: str, cmtype: str = "page"):
        """
        Gọi MediaWiki categorymembers API và yield page_id (kiểu int).
        Tự động xử lý phân trang (continue token).
        """
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Thể_loại:{wiki_category}",
            "cmlimit": 500,
            "cmtype": cmtype,
            "format": "json",
        }

        while True:
            data = self._api_call(params)

            if "query" not in data or "categorymembers" not in data["query"]:
                logger.debug(f"Danh mục '{wiki_category}' trống hoặc không tồn tại.")
                break

            members = data["query"]["categorymembers"]
            for member in members:
                yield member["pageid"]

            if "continue" in data:
                params.update(data["continue"])
                time.sleep(DELAY_BETWEEN_REQUESTS)
            else:
                break

    # ===========================================================
    #  LẤY NỘI DUNG MỘT BÀI
    # ===========================================================
    def _fetch_article(self, page_id: int, category: str) -> Optional[WikiArticle]:
        """
        Gọi API lấy nội dung bài viết theo page_id.
        Trả về WikiArticle hoặc None nếu bài không hợp lệ.
        """
        params = {
            "action": "query",
            "pageids": page_id,
            "prop": "extracts|info|categories",
            # "exintro" được BỎ ra → API trả về TOÀN BỘ nội dung bài
            # (Nếu đặt exintro=False, API vẫn hiểu là "chỉ lấy intro" vì đây là flag)
            "explaintext": True,     # Lấy text thuần, không HTML
            "inprop": "url|touched", # Lấy URL và ngày sửa đổi
            "cllimit": 20,           # Lấy tối đa 20 danh mục của bài
            "format": "json",
        }

        data = self._api_call(params)
        pages = data.get("query", {}).get("pages", {})

        if not pages:
            return None

        page = next(iter(pages.values()))

        # Bỏ qua trang lỗi
        if "missing" in page or "invalid" in page:
            logger.debug(f"Bỏ qua page_id={page_id}: missing/invalid")
            return None

        title = page.get("title", "")
        content = page.get("extract", "") or ""
        url = page.get("fullurl", f"https://vi.wikipedia.org/?curid={page_id}")
        touched = page.get("touched", "")

        # Lấy danh sách categories
        cats = [c["title"].replace("Thể loại:", "")
                for c in page.get("categories", [])]

        # Lọc bài quá ngắn (stub, redirect, ...)
        if len(content) < MIN_CONTENT_LENGTH:
            logger.debug(f"Bỏ qua '{title}': nội dung quá ngắn ({len(content)} ký tự)")
            return None

        # Tóm tắt = 3 đoạn đầu
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        summary = "\n".join(paragraphs[:3])

        return WikiArticle(
            id=str(page_id),
            title=title,
            url=url,
            category=category,
            categories=cats,
            summary=summary,
            content=content,
            crawled_at=datetime.now().isoformat(),
            last_modified=touched,
            language="vi",
            word_count=len(content.split()),
            is_valid=True,
        )

    # ===========================================================
    #  GỌI API VỚI RETRY TỰ ĐỘNG
    # ===========================================================
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _api_call(self, params: dict) -> dict:
        """
        Gọi MediaWiki API với retry tự động khi gặp lỗi mạng.
        Exponential backoff: chờ 2s → 4s → 8s → 16s → 30s.
        """
        response = self.session.get(
            WIKI_BASE_URL,
            params=params,
            timeout=30,
        )

        # HTTP error (4xx, 5xx)
        if response.status_code == 429:
            # Too Many Requests → chờ lâu hơn
            logger.warning("429 Too Many Requests — chờ 60s...")
            time.sleep(60)
            raise requests.ConnectionError("Rate limited")

        response.raise_for_status()

        return response.json()
