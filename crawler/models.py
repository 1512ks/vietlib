"""
models.py -- Dataclass định nghĩa cấu trúc dữ liệu bài viết Wikipedia
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime


@dataclass
class WikiArticle:
    """Mot bai viet Wikipedia tieng Viet da duoc crawl."""

    # --- Metadata ---
    id: str                          # page_id từ Wikipedia
    title: str                       # Tiêu đề bài viết
    url: str                         # URL đầy đủ
    category: str                    # Danh mục crawl (ví dụ: "Sách tiếng Việt")
    categories: List[str] = field(default_factory=list)  # Tất cả danh mục của bài

    # --- Noi dung ---
    summary: str = ""                # Tóm tắt đầu bài (1-2 đoạn đầu)
    content: str = ""                # Toàn bộ nội dung văn bản

    # --- Thong tin crawl ---
    crawled_at: str = ""             # Thời điểm crawl (ISO 8601)
    last_modified: str = ""          # Lần sửa đổi cuối từ Wikipedia
    language: str = "vi"
    word_count: int = 0
    is_valid: bool = True            # False nếu bài quá ngắn hoặc redirect

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "WikiArticle":
        return WikiArticle(**d)
