"""
wiki_crawler_v2.py -- Crawler V2: thu thập tác phẩm văn học & tác giả từ Wikipedia tiếng Việt.

Cải tiến so với V1:
  - Trích xuất metadata có cấu trúc: author, publication_year, genre (từ Infobox + Wikidata + Regex)
  - Lưu BookArticle và AuthorArticle riêng biệt
  - Resume được khi bị dừng giữa chừng
  - Bắt TOÀN BỘ tác phẩm văn học (không lọc mất) -- chỉ lọc bài quá ngắn
"""

import time
import logging
from datetime import datetime
from typing import Iterator, Optional, Dict, List

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from tqdm import tqdm

from models_v2 import BookArticle, AuthorArticle
from storage_v2 import StorageV2
from extractor import (
    get_wikidata_id,
    get_wikidata_book_metadata,
    get_wikidata_author_metadata,
    parse_infobox,
    extract_genre_from_content,
    extract_author_from_content,
    extract_year_from_content,
    classify_article,
)
from config_v2 import (
    USER_AGENT,
    WIKI_BASE_URL,
    WIKIDATA_API_URL,
    DELAY_BETWEEN_REQUESTS,
    DELAY_BETWEEN_CATEGORIES,
    MAX_RETRIES,
    RETRY_WAIT_MIN,
    RETRY_WAIT_MAX,
    MIN_CONTENT_LENGTH,
    MAX_ARTICLES_PER_CATEGORY,
    SUBCATEGORY_MAX_DEPTH,
    BOOK_CATEGORIES,
    AUTHOR_CATEGORIES,
)

logger = logging.getLogger(__name__)


class WikiCrawlerV2:
    """
    Crawler Wikipedia V2 — thu thập sách & tác giả với metadata đầy đủ.

    Dùng:
        crawler = WikiCrawlerV2()
        crawler.crawl_all()           # Crawl tất cả
        crawler.crawl_books_only()    # Chỉ crawl sách
        crawler.crawl_authors_only()  # Chỉ crawl tác giả
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.storage = StorageV2()
        self.total_books = 0
        self.total_authors = 0
        self.total_errors = 0

    # ===========================================================
    #  PUBLIC API
    # ===========================================================
    def crawl_all(self):
        """Crawl cả sách lẫn tác giả."""
        logger.info("=" * 60)
        logger.info("  CRAWLER V2 — TÁC PHẨM VĂN HỌC & TÁC GIẢ")
        logger.info("=" * 60)
        all_cats = {**BOOK_CATEGORIES, **AUTHOR_CATEGORIES}
        self._run(all_cats)

    def crawl_books_only(self, custom_cats: dict = None):
        """Chỉ crawl tác phẩm văn học."""
        cats = custom_cats or BOOK_CATEGORIES
        logger.info(f"Crawl {len(cats)} danh mục sách...")
        self._run(cats)

    def crawl_authors_only(self, custom_cats: dict = None):
        """Chỉ crawl tác giả."""
        cats = custom_cats or AUTHOR_CATEGORIES
        logger.info(f"Crawl {len(cats)} danh mục tác giả...")
        self._run(cats)

    # ===========================================================
    #  VÒNG LẶP CHÍNH
    # ===========================================================
    def _run(self, categories: dict):
        for display_name, wiki_category in categories.items():
            if self.storage.is_category_done(display_name):
                logger.info(f"[SKIP] '{display_name}' đã crawl xong.")
                continue

            logger.info(f"\n→ Crawl: '{display_name}'")
            n_books, n_authors = self._crawl_category(display_name, wiki_category)
            self.storage.mark_category_done(display_name, n_books, n_authors)

            logger.info(f"  Nghỉ {DELAY_BETWEEN_CATEGORIES}s...")
            time.sleep(DELAY_BETWEEN_CATEGORIES)

        self.storage.update_stats(self.total_books, self.total_authors, self.total_errors)
        self.storage.save_summary_json()
        self.storage.print_summary()

    # ===========================================================
    #  CRAWL 1 DANH MỤC
    # ===========================================================
    def _crawl_category(self, display_name: str, wiki_category: str):
        """Thu thập tất cả bài trong danh mục (đệ quy subcategories)."""
        visited_cats: set = set()
        page_ids = list(self._collect_page_ids(wiki_category, 0, visited_cats))
        page_ids = list(dict.fromkeys(page_ids))  # Bỏ trùng, giữ thứ tự

        logger.info(
            f"  Tìm được {len(page_ids)} bài trong {len(visited_cats)} danh mục"
        )

        if MAX_ARTICLES_PER_CATEGORY:
            page_ids = page_ids[:MAX_ARTICLES_PER_CATEGORY]

        n_books = 0
        n_authors = 0
        pbar = tqdm(page_ids, desc=f"{display_name[:28]}", unit="bài")

        for page_id in pbar:
            if self.storage.article_exists(str(page_id)):
                pbar.set_postfix(status="cached")
                continue

            try:
                article = self._fetch_and_build(page_id, display_name)
                if article is None:
                    continue

                self.storage.save(article)

                if isinstance(article, BookArticle):
                    n_books += 1
                    self.total_books += 1
                    pbar.set_postfix(sách=n_books, tácgiả=n_authors,
                                     tên=article.title[:18])
                else:
                    n_authors += 1
                    self.total_authors += 1
                    pbar.set_postfix(sách=n_books, tácgiả=n_authors,
                                     tên=article.title[:18])

            except Exception as e:
                self.total_errors += 1
                logger.warning(f"Lỗi page_id={page_id}: {e}")

            finally:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        return n_books, n_authors

    # ===========================================================
    #  ĐỆ QUY THU THẬP PAGE_ID
    # ===========================================================
    def _collect_page_ids(self, wiki_category: str, depth: int, visited: set):
        if wiki_category in visited:
            return
        visited.add(wiki_category)

        yield from self._get_pages_in_category(wiki_category)
        time.sleep(DELAY_BETWEEN_REQUESTS)

        if depth < SUBCATEGORY_MAX_DEPTH:
            for subcat in self._get_subcategories(wiki_category):
                time.sleep(DELAY_BETWEEN_REQUESTS)
                yield from self._collect_page_ids(subcat, depth + 1, visited)

    def _get_pages_in_category(self, wiki_category: str):
        yield from self._query_categorymembers(wiki_category, cmtype="page")

    def _get_subcategories(self, wiki_category: str):
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
                title = m["title"].replace("Thể loại:", "").replace("Thể_loại:", "")
                yield title
            if "continue" in data:
                params.update(data["continue"])
                time.sleep(DELAY_BETWEEN_REQUESTS)
            else:
                break

    def _query_categorymembers(self, wiki_category: str, cmtype: str = "page"):
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
            if "query" not in data or "categorymembers" not in data.get("query", {}):
                break
            for member in data["query"]["categorymembers"]:
                yield member["pageid"]
            if "continue" in data:
                params.update(data["continue"])
                time.sleep(DELAY_BETWEEN_REQUESTS)
            else:
                break

    # ===========================================================
    #  FETCH 1 BÀI — TẤT CẢ THÔNG TIN
    # ===========================================================
    def _fetch_and_build(self, page_id: int, crawl_category: str):
        """
        Fetch nội dung bài, wikitext, và wikidata_id.
        Phân loại thành BookArticle hoặc AuthorArticle.
        Điền metadata từ Infobox → Wikidata → Regex.
        """
        # ── Bước 1: Lấy extract + info + categories ──
        params_content = {
            "action": "query",
            "pageids": page_id,
            "prop": "extracts|info|categories|revisions|pageprops",
            "explaintext": True,
            "inprop": "url|touched",
            "cllimit": 50,
            "rvprop": "content",
            "rvslots": "main",
            "ppprop": "wikibase_item",
            "format": "json",
        }
        data = self._api_call(params_content)
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None

        page = next(iter(pages.values()))

        if "missing" in page or "invalid" in page:
            return None

        title = page.get("title", "")
        content = page.get("extract", "") or ""
        url = page.get("fullurl", f"https://vi.wikipedia.org/?curid={page_id}")
        touched = page.get("touched", "")
        wikidata_id = page.get("pageprops", {}).get("wikibase_item", "")

        # Categories của bài
        wiki_cats = [
            c["title"].replace("Thể loại:", "").replace("Thể_loại:", "")
            for c in page.get("categories", [])
        ]

        # Lọc bài quá ngắn
        if len(content) < MIN_CONTENT_LENGTH:
            logger.debug(f"Quá ngắn: '{title}' ({len(content)} ký tự)")
            return None

        # Tóm tắt = 3 đoạn đầu có nội dung
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        summary = "\n".join(paragraphs[:3])

        # ── Bước 2: Lấy wikitext thô từ revisions ──
        wikitext = ""
        try:
            revisions = page.get("revisions", [])
            if revisions:
                wikitext = revisions[0].get("slots", {}).get("main", {}).get("*", "") or ""
        except Exception:
            pass

        # ── Bước 3: Phân loại book vs author ──
        article_type = classify_article(title, wiki_cats, content, crawl_category)

        # ── Bước 4: Parse Infobox ──
        infobox_data = parse_infobox(wikitext) if wikitext else {}

        common = {
            "id": str(page_id),
            "title": title,
            "url": url,
            "summary": summary,
            "content": content,
            "wikidata_id": wikidata_id,
            "categories": wiki_cats,
            "crawl_category": crawl_category,
            "language": "vi",
            "word_count": len(content.split()),
            "char_count": len(content),
            "crawled_at": datetime.now().isoformat(),
            "last_modified": touched,
        }

        if article_type == "author":
            return self._build_author(common, infobox_data, wikidata_id)
        else:
            return self._build_book(common, infobox_data, wikidata_id, wiki_cats)

    # ===========================================================
    #  XÂY DỰNG BOOK ARTICLE
    # ===========================================================
    def _build_book(self, common: dict, infobox: dict,
                    wikidata_id: str, categories: list) -> BookArticle:
        content = common["content"]

        # ── Tác giả ──
        author = infobox.get("author", "")
        author_source = "infobox" if author else ""
        authors = []

        # ── Năm xuất bản ──
        pub_year = infobox.get("publication_year", "")
        year_source = "infobox" if pub_year else ""

        # ── Thể loại ──
        genre = infobox.get("genre", "")
        genres = []
        genre_source = "infobox" if genre else ""

        # ── Wikidata fallback ──
        if wikidata_id and (not author or not pub_year or not genre):
            try:
                wd = get_wikidata_book_metadata(wikidata_id, self.session, WIKIDATA_API_URL)
                if not author and wd.get("author"):
                    author = wd["author"]
                    authors = wd.get("authors", [author])
                    author_source = "wikidata"
                if not pub_year and wd.get("publication_year"):
                    pub_year = wd["publication_year"]
                    year_source = "wikidata"
                if not genre and wd.get("genre"):
                    genre = wd["genre"]
                    genres = wd.get("genres", [genre])
                    genre_source = "wikidata"
            except Exception as e:
                logger.debug(f"Wikidata error for {wikidata_id}: {e}")
            finally:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        # ── Regex fallback ──
        if not author:
            author, author_source = extract_author_from_content(content)
        if not pub_year:
            pub_year, year_source = extract_year_from_content(content)
        if not genre:
            genre, genre_source = extract_genre_from_content(content, categories)

        if not authors and author:
            authors = [author]
        if not genres and genre:
            genres = [genre]

        return BookArticle(
            **common,
            author=author,
            authors=authors,
            publication_year=pub_year,
            genre=genre,
            genres=genres,
            author_source=author_source,
            year_source=year_source,
            genre_source=genre_source,
        )

    # ===========================================================
    #  XÂY DỰNG AUTHOR ARTICLE
    # ===========================================================
    def _build_author(self, common: dict, infobox: dict,
                      wikidata_id: str) -> AuthorArticle:
        birth = infobox.get("birth_year", "")
        birth_source = "infobox" if birth else ""
        death = infobox.get("death_year", "")
        nationality = infobox.get("nationality", "")
        nat_source = "infobox" if nationality else ""
        notable_works = []

        raw_works = infobox.get("notable_works", "")
        if raw_works:
            notable_works = [w.strip() for w in raw_works.split(",") if w.strip()]

        # Wikidata fallback
        if wikidata_id and (not birth or not nationality):
            try:
                wd = get_wikidata_author_metadata(wikidata_id, self.session, WIKIDATA_API_URL)
                if not birth and wd.get("birth_year"):
                    birth = wd["birth_year"]
                    birth_source = "wikidata"
                if not death and wd.get("death_year"):
                    death = wd["death_year"]
                if not nationality and wd.get("nationality"):
                    nationality = wd["nationality"]
                    nat_source = "wikidata"
            except Exception as e:
                logger.debug(f"Wikidata author error for {wikidata_id}: {e}")
            finally:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        return AuthorArticle(
            **common,
            birth_year=birth,
            death_year=death,
            nationality=nationality,
            notable_works=notable_works,
            genres=[],
            birth_source=birth_source,
            nationality_source=nat_source,
        )

    # ===========================================================
    #  GỌI API VỚI RETRY
    # ===========================================================
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _api_call(self, params: dict) -> dict:
        resp = self.session.get(WIKI_BASE_URL, params=params, timeout=30)
        if resp.status_code == 429:
            logger.warning("429 Too Many Requests — chờ 60s...")
            time.sleep(60)
            raise requests.ConnectionError("Rate limited")
        resp.raise_for_status()
        return resp.json()
