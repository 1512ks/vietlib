"""
vnthuquan_crawler.py -- Crawler thu thập sách toàn văn từ thư viện trực tuyến vnthuquan.net.

Khác với Wikipedia/Google Books (có API), vnthuquan.net chỉ có giao diện web nên
crawler phải tải HTML và bóc tách nội dung (HTML parsing).

Luồng:
  1. Duyệt các trang mục lục/phân loại (SEED_LISTINGS) -> thu thập link tới từng truyện.
  2. Với mỗi truyện: lấy tiêu đề + tác giả, duyệt tuần tự các chương, bóc nội dung,
     loại bỏ thẻ/điều hướng/quảng cáo rồi ghép thành toàn văn.
  3. Lưu thành tệp .txt đặt tên "Tên tác phẩm - Tác giả.txt" vào data/archive/output/
     (chính là raw mà preprocess_archive.py đọc). Bỏ qua tệp đã tồn tại (resume).

Cài đặt phụ thuộc:
    pip install beautifulsoup4 lxml

Cách dùng:
    python crawler/vnthuquan_crawler.py                       # crawl theo SEED_LISTINGS
    python crawler/vnthuquan_crawler.py --limit 20            # thử 20 truyện
    python crawler/vnthuquan_crawler.py --listing "<url muc luc>"

⚠️ LƯU Ý: vnthuquan.net là site ASP.NET; cấu trúc HTML có thể thay đổi. Các CSS selector
trong phần CẤU HÌNH bên dưới (CONTENT_SELECTORS, TITLE_SELECTORS, CHAPTER_LINK_PATTERN…)
được đặt theo quy ước phổ biến của site và CẦN KIỂM CHỨNG / tinh chỉnh lại với trang thật.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# ============================================================
#  CẤU HÌNH
# ============================================================
BASE_URL   = "https://vnthuquan.net"
USER_AGENT = "DATN-LibraryChatbot/1.0 (sinh vien DHBKHN; lien he: datn@hust.edu.vn)"

# Ghi raw .txt vào đúng thư mục mà pipeline archive đọc
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "archive" / "output"

# Politeness / Robustness (khớp tham số nêu trong báo cáo)
DELAY_BETWEEN_REQUESTS = 1.5     # giây giữa các yêu cầu
MAX_RETRIES            = 3
RETRY_WAIT_MIN         = 2
RETRY_WAIT_MAX         = 20
REQUEST_TIMEOUT        = 25

MIN_TEXT_LEN = 500               # bỏ truyện tải lỗi / quá ngắn (số ký tự)

# Danh sách trang mục lục/phân loại để bắt đầu (điền URL thật của vnthuquan vào đây)
SEED_LISTINGS: list[str] = [
    # ví dụ: "https://vnthuquan.net/truyen/?tac_pham=...",
]

# ── CSS selector / regex — CẦN KIỂM CHỨNG với HTML thật của vnthuquan ──
BOOK_LINK_PATTERN    = re.compile(r"truyen\.aspx\?tid=", re.I)   # link tới 1 truyện
CHAPTER_LINK_PATTERN = re.compile(r"tid=.*?(chuong|chap)", re.I) # link chương trong 1 truyện
CONTENT_SELECTORS    = ["#noidung", "div.truyen", "#divtoanvan", "td.chude"]  # khối nội dung
TITLE_SELECTORS      = ["h1", "#tieude", "div.tualon"]
AUTHOR_SELECTORS     = ["#tacgia", "div.tacgia", "a.tacgia"]
# Thẻ cần loại bỏ khỏi nội dung
STRIP_TAGS = ["script", "style", "noscript", "iframe", "table", "form"]


# ============================================================
#  CRAWLER
# ============================================================
class VnThuQuanCrawler:
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        try:
            from bs4 import BeautifulSoup  # noqa: F401
        except ImportError:
            raise ImportError("Thiếu beautifulsoup4. Cài: pip install beautifulsoup4 lxml")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.saved = self.skipped = self.errors = 0

    # ---------- HTTP với retry + backoff ----------
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _get(self, url: str) -> str:
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 429:                 # Too Many Requests
            logger.warning("429 — nghỉ 60s...")
            time.sleep(60)
            raise requests.ConnectionError("rate limited")
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text

    def _soup(self, html: str):
        from bs4 import BeautifulSoup
        try:
            return BeautifulSoup(html, "lxml")
        except Exception:
            return BeautifulSoup(html, "html.parser")

    # ---------- B1: thu thập link truyện từ trang mục lục ----------
    def collect_book_urls(self, listing_url: str) -> list[str]:
        urls, seen = [], set()
        try:
            soup = self._soup(self._get(listing_url))
        except Exception as e:
            logger.warning(f"Lỗi tải mục lục {listing_url}: {e}")
            return urls
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if BOOK_LINK_PATTERN.search(href):
                full = urljoin(BASE_URL, href)
                if full not in seen:
                    seen.add(full)
                    urls.append(full)
        logger.info(f"  Mục lục {listing_url}: tìm được {len(urls)} truyện")
        return urls

    # ---------- B2: lấy tiêu đề + tác giả + toàn văn 1 truyện ----------
    def _select_text(self, soup, selectors: list[str]) -> str:
        for sel in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(" ", strip=True)
        return ""

    def _extract_content(self, soup) -> str:
        for tag in STRIP_TAGS:
            for t in soup.find_all(tag):
                t.decompose()
        for sel in CONTENT_SELECTORS:
            el = soup.select_one(sel)
            if el:
                txt = el.get_text("\n", strip=True)
                if len(txt) > 100:
                    return txt
        return ""

    def crawl_book(self, book_url: str) -> tuple[str, str, str]:
        """Trả về (title, author, fulltext)."""
        soup = self._soup(self._get(book_url))
        title  = self._select_text(soup, TITLE_SELECTORS) or (soup.title.get_text(strip=True) if soup.title else "")
        author = self._select_text(soup, AUTHOR_SELECTORS)
        # Tách "Tác giả:" nếu dính nhãn
        author = re.sub(r"^\s*tác giả\s*:?\s*", "", author, flags=re.I).strip()

        # Thu thập link chương (nếu truyện chia nhiều chương)
        chapter_urls = []
        for a in soup.find_all("a", href=True):
            if CHAPTER_LINK_PATTERN.search(a["href"]):
                chapter_urls.append(urljoin(BASE_URL, a["href"]))
        chapter_urls = list(dict.fromkeys(chapter_urls))

        parts = [self._extract_content(soup)]           # nội dung trang đầu (nếu có)
        for ch in chapter_urls:
            time.sleep(DELAY_BETWEEN_REQUESTS)
            try:
                parts.append(self._extract_content(self._soup(self._get(ch))))
            except Exception as e:
                logger.debug(f"Lỗi chương {ch}: {e}")
        fulltext = re.sub(r"\n{3,}", "\n\n", "\n\n".join(p for p in parts if p)).strip()
        return title.strip(), author.strip(), fulltext

    # ---------- B3: lưu .txt "Tên - Tác giả.txt" ----------
    @staticmethod
    def _safe(name: str) -> str:
        return re.sub(r'[\\/:*?"<>|]', "", name).strip()[:150]

    def save(self, title: str, author: str, text: str) -> bool:
        if not title or len(text) < MIN_TEXT_LEN:
            return False
        fname = f"{self._safe(title)} - {self._safe(author) or 'Khuyết danh'}.txt"
        path = self.output_dir / fname
        if path.exists():                               # resume: bỏ qua truyện đã tải
            self.skipped += 1
            return False
        path.write_text(text, encoding="utf-8")
        self.saved += 1
        return True

    # ---------- Điều phối ----------
    def crawl_all(self, listings: list[str], limit: int = 0):
        if not listings:
            logger.error("SEED_LISTINGS rỗng — hãy điền URL trang mục lục vnthuquan (hoặc dùng --listing).")
            return
        book_urls = []
        for lst in listings:
            book_urls.extend(self.collect_book_urls(lst))
            time.sleep(DELAY_BETWEEN_REQUESTS)
        book_urls = list(dict.fromkeys(book_urls))
        if limit:
            book_urls = book_urls[:limit]
        logger.info(f"Tổng {len(book_urls)} truyện cần crawl.")

        for i, url in enumerate(book_urls, 1):
            try:
                title, author, text = self.crawl_book(url)
                if self.save(title, author, text):
                    logger.info(f"[{i}/{len(book_urls)}] ✅ {title} — {author or 'Khuyết danh'} ({len(text):,} ký tự)")
                else:
                    logger.info(f"[{i}/{len(book_urls)}] ⏭ bỏ qua (đã có / quá ngắn): {title[:40]}")
            except Exception as e:
                self.errors += 1
                logger.warning(f"[{i}/{len(book_urls)}] ❌ lỗi {url}: {str(e)[:80]}")
            time.sleep(DELAY_BETWEEN_REQUESTS)

        print("\n" + "=" * 50)
        print(f"  vnthuquan crawler — lưu {self.saved} | bỏ qua {self.skipped} | lỗi {self.errors}")
        print(f"  Output: {self.output_dir}")
        print("=" * 50)


def main():
    ap = argparse.ArgumentParser(description="Crawler vnthuquan.net -> data/archive/output/*.txt")
    ap.add_argument("--listing", action="append", default=None,
                    help="URL trang mục lục (lặp lại nhiều lần được). Mặc định dùng SEED_LISTINGS.")
    ap.add_argument("--limit", type=int, default=0, help="Giới hạn số truyện (thử nghiệm)")
    args = ap.parse_args()
    listings = args.listing if args.listing else SEED_LISTINGS
    VnThuQuanCrawler().crawl_all(listings, limit=args.limit)


if __name__ == "__main__":
    main()
