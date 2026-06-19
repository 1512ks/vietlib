"""
storage.py -- Lưu trữ dữ liệu JSON và theo dõi tiến độ crawl
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from models import WikiArticle
from config import DATA_DIR, PROGRESS_FILE

logger = logging.getLogger(__name__)


class Storage:
    """
    Quản lý lưu trữ bài viết dạng JSON và theo dõi tiến độ crawl.

    Cấu trúc thư mục output:
        data/raw/
            Sach_tieng_Viet/
                page_12345.json
                page_67890.json
                ...
            Nha_van_Viet_Nam/
                ...
            _summary.json       ← Thống kê tổng hợp
    """

    def __init__(self):
        self.progress = self._load_progress()

    # ----------------------------------------------------------
    #  LUU BAI VIET
    # ----------------------------------------------------------
    def save_article(self, article: WikiArticle) -> Path:
        """Luu mot bai viet vao file JSON rieng biet."""
        # Tao thu muc cho danh muc nay
        cat_dir = DATA_DIR / self._safe_dirname(article.category)
        cat_dir.mkdir(parents=True, exist_ok=True)

        # Ten file = page_id de tranh trung
        filepath = cat_dir / f"page_{article.id}.json"

        # Ghi JSON voi encoding UTF-8, doc duoc bang mat thuong
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(article.to_dict(), f, ensure_ascii=False, indent=2)

        logger.debug(f"Saved: {filepath.name}")
        return filepath

    def article_exists(self, page_id: str, category: str) -> bool:
        """Kiểm tra bài đã crawl chưa (tránh crawl trùng)."""
        cat_dir = DATA_DIR / self._safe_dirname(category)
        return (cat_dir / f"page_{page_id}.json").exists()

    # ----------------------------------------------------------
    #  THEO DÕI TIẾN ĐỘ (RESUME)
    # ----------------------------------------------------------
    def mark_category_done(self, category: str, count: int):
        """Đánh dấu một danh mục đã crawl xong."""
        self.progress["completed_categories"][category] = {
            "count": count,
            "finished_at": datetime.now().isoformat(),
        }
        self._save_progress()
        logger.info(f"Category done: '{category}' — {count} articles")

    def is_category_done(self, category: str) -> bool:
        """Danh mục này đã crawl xong chưa?"""
        return category in self.progress["completed_categories"]

    def update_stats(self, total_articles: int, total_errors: int):
        self.progress["total_articles"] = total_articles
        self.progress["total_errors"] = total_errors
        self.progress["last_updated"] = datetime.now().isoformat()
        self._save_progress()

    # ----------------------------------------------------------
    #  THỐNG KÊ
    # ----------------------------------------------------------
    def print_summary(self):
        """In thống kê crawl ra terminal."""
        p = self.progress
        print("\n" + "=" * 50)
        print("  THỐNG KÊ CRAWL")
        print("=" * 50)
        print(f"  Tổng bài đã lưu : {p.get('total_articles', 0)}")
        print(f"  Tổng lỗi        : {p.get('total_errors', 0)}")
        print(f"  Danh mục hoàn thành:")
        for cat, info in p.get("completed_categories", {}).items():
            print(f"    ✓ {cat}: {info['count']} bài")
        print("=" * 50)

    def save_summary_json(self):
        """Lưu file tổng hợp _summary.json vào data/raw/."""
        summary = {
            "generated_at": datetime.now().isoformat(),
            **self.progress,
            "per_category": {},
        }
        # Đếm số file thực tế trong mỗi thư mục
        for cat_dir in DATA_DIR.iterdir():
            if cat_dir.is_dir():
                count = len(list(cat_dir.glob("page_*.json")))
                summary["per_category"][cat_dir.name] = count

        out = DATA_DIR / "_summary.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"Summary saved: {out}")

    # ----------------------------------------------------------
    #  INTERNAL
    # ----------------------------------------------------------
    @staticmethod
    def _safe_dirname(name: str) -> str:
        """Chuyển tên danh mục thành tên thư mục hợp lệ."""
        return name.replace(" ", "_").replace("/", "-")

    def _load_progress(self) -> dict:
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Resumed progress: {len(data.get('completed_categories', {}))} categories done")
            return data
        return {
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_articles": 0,
            "total_errors": 0,
            "completed_categories": {},
        }

    def _save_progress(self):
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
