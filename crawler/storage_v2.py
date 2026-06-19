"""
storage_v2.py -- Lưu trữ BookArticle & AuthorArticle vào thư mục data/raw_v2/.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Union

from models_v2 import BookArticle, AuthorArticle
from config_v2 import DATA_DIR_BOOKS, DATA_DIR_AUTHORS, PROGRESS_FILE_V2

logger = logging.getLogger(__name__)


class StorageV2:
    """
    Lưu sách vào data/raw_v2/books/page_{id}.json
    Lưu tác giả vào data/raw_v2/authors/page_{id}.json
    Theo dõi tiến độ crawl để resume.
    """

    def __init__(self):
        self.progress = self._load_progress()

    # ----------------------------------------------------------
    #  LUU
    # ----------------------------------------------------------
    def save_book(self, article: BookArticle) -> Path:
        filepath = DATA_DIR_BOOKS / f"page_{article.id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(article.to_dict(), f, ensure_ascii=False, indent=2)
        logger.debug(f"[BOOK] Saved: {filepath.name}")
        return filepath

    def save_author(self, article: AuthorArticle) -> Path:
        filepath = DATA_DIR_AUTHORS / f"page_{article.id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(article.to_dict(), f, ensure_ascii=False, indent=2)
        logger.debug(f"[AUTHOR] Saved: {filepath.name}")
        return filepath

    def save(self, article: Union[BookArticle, AuthorArticle]) -> Path:
        """Tu dong chon ham luu phu hop."""
        if isinstance(article, BookArticle):
            return self.save_book(article)
        elif isinstance(article, AuthorArticle):
            return self.save_author(article)
        raise ValueError(f"Unknown article type: {type(article)}")

    # ----------------------------------------------------------
    #  KIỂM TRA TỒN TẠI
    # ----------------------------------------------------------
    def book_exists(self, page_id: str) -> bool:
        return (DATA_DIR_BOOKS / f"page_{page_id}.json").exists()

    def author_exists(self, page_id: str) -> bool:
        return (DATA_DIR_AUTHORS / f"page_{page_id}.json").exists()

    def article_exists(self, page_id: str) -> bool:
        """Bài đã được lưu ở bất kỳ loại nào chưa."""
        return self.book_exists(page_id) or self.author_exists(page_id)

    # ----------------------------------------------------------
    #  THEO DÕI TIẾN ĐỘ
    # ----------------------------------------------------------
    def mark_category_done(self, category: str, count_books: int, count_authors: int):
        self.progress["completed_categories"][category] = {
            "books": count_books,
            "authors": count_authors,
            "finished_at": datetime.now().isoformat(),
        }
        self._save_progress()
        logger.info(f"[DONE] '{category}' — {count_books} sách, {count_authors} tác giả")

    def is_category_done(self, category: str) -> bool:
        return category in self.progress["completed_categories"]

    def update_stats(self, total_books: int, total_authors: int, total_errors: int):
        self.progress["total_books"] = total_books
        self.progress["total_authors"] = total_authors
        self.progress["total_errors"] = total_errors
        self.progress["last_updated"] = datetime.now().isoformat()
        self._save_progress()

    # ----------------------------------------------------------
    #  THỐNG KÊ
    # ----------------------------------------------------------
    def print_summary(self):
        p = self.progress
        # Đếm file thực tế
        n_books = len(list(DATA_DIR_BOOKS.glob("page_*.json")))
        n_authors = len(list(DATA_DIR_AUTHORS.glob("page_*.json")))

        print("\n" + "=" * 55)
        print("  THỐNG KÊ CRAWL V2")
        print("=" * 55)
        print(f"  Sách đã lưu    : {n_books:,}")
        print(f"  Tác giả đã lưu: {n_authors:,}")
        print(f"  Tổng lỗi       : {p.get('total_errors', 0)}")
        print(f"  Danh mục hoàn thành ({len(p.get('completed_categories', {}))}):")
        for cat, info in list(p.get("completed_categories", {}).items())[:20]:
            print(f"    ✓ {cat[:40]:<40}  {info.get('books',0)} sách, {info.get('authors',0)} tác giả")
        if len(p.get("completed_categories", {})) > 20:
            print(f"    ... (còn {len(p['completed_categories']) - 20} danh mục nữa)")
        print("=" * 55)

    def save_summary_json(self):
        """Xuất file tổng hợp ra data/raw_v2/_summary.json."""
        from config_v2 import DATA_DIR_V2
        n_books = len(list(DATA_DIR_BOOKS.glob("page_*.json")))
        n_authors = len(list(DATA_DIR_AUTHORS.glob("page_*.json")))

        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_books": n_books,
            "total_authors": n_authors,
            **self.progress,
        }
        out = DATA_DIR_V2 / "_summary.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"Summary saved: {out}")

    # ----------------------------------------------------------
    #  INTERNAL
    # ----------------------------------------------------------
    def _load_progress(self) -> dict:
        if PROGRESS_FILE_V2.exists():
            with open(PROGRESS_FILE_V2, encoding="utf-8") as f:
                data = json.load(f)
            n_done = len(data.get("completed_categories", {}))
            logger.info(f"Resumed progress: {n_done} categories done")
            return data
        return {
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_books": 0,
            "total_authors": 0,
            "total_errors": 0,
            "completed_categories": {},
        }

    def _save_progress(self):
        PROGRESS_FILE_V2.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE_V2, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
