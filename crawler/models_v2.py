"""
models_v2.py -- Dataclass cho crawler V2: BookArticle & AuthorArticle.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class BookArticle:
    """
    Một tác phẩm văn học (sách, tiểu thuyết, tập thơ, truyện ngắn...) từ Wikipedia.
    
    Ưu tiên fill các trường: author, publication_year, genre.
    Nguồn: Infobox wikitext → Wikidata → Regex trên content.
    """

    # --- Dinh danh ---
    id: str                          # page_id Wikipedia
    title: str                       # Tiêu đề tác phẩm
    url: str                         # URL đầy đủ
    wikidata_id: str = ""            # Q-ID trên Wikidata (nếu có)

    # --- Noi dung ---
    summary: str = ""                # Tóm tắt (đoạn đầu bài)
    content: str = ""                # Toàn bộ nội dung

    # --- Metadata tac pham (quan trong nhat) ---
    author: str = ""                 # Tên tác giả/tác giả chính
    authors: List[str] = field(default_factory=list)   # Danh sách tác giả (nếu nhiều)
    publication_year: str = ""       # Năm xuất bản (chuỗi, vd: "1941", "1965-1968")
    genre: str = ""                  # Thể loại chính (Tiểu thuyết, Thơ, Truyện ngắn...)
    genres: List[str] = field(default_factory=list)    # Tất cả thể loại

    # --- Nhan dien bo sung ---
    isbn: str = ""                   # ISBN-13 hoặc ISBN-10 (từ Google Books)
    isbn_list: List[str] = field(default_factory=list) # Tất cả ISBN
    publisher: str = ""              # Nhà xuất bản
    page_count: int = 0             # Số trang
    cover_url: str = ""              # URL ảnh bìa sách
    source: str = "wikipedia"        # "wikipedia" | "google_books"

    # --- Nguon metadata (de debug) ---
    author_source: str = ""          # "infobox" | "wikidata" | "regex" | ""
    year_source: str = ""            # "infobox" | "wikidata" | "regex" | ""
    genre_source: str = ""           # "infobox" | "wikidata" | "categories" | ""

    # --- Phan loai ---
    crawl_category: str = ""         # Danh mục dùng để crawl bài này
    categories: List[str] = field(default_factory=list)  # Tất cả danh mục Wikipedia của bài

    # --- Crawl metadata ---
    language: str = "vi"
    word_count: int = 0
    char_count: int = 0
    crawled_at: str = ""
    last_modified: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "BookArticle":
        return BookArticle(**{k: v for k, v in d.items() if k in BookArticle.__dataclass_fields__})


@dataclass
class AuthorArticle:
    """
    Một tác giả văn học (nhà văn, nhà thơ...) từ Wikipedia.
    """

    # --- Định danh ---
    id: str
    title: str                       # Tên tác giả
    url: str
    wikidata_id: str = ""

    # --- Nội dung ---
    summary: str = ""
    content: str = ""

    # --- Metadata tác giả ---
    birth_year: str = ""             # Năm sinh (vd: "1765", "1942")
    death_year: str = ""             # Năm mất (vd: "1820", để trống nếu còn sống)
    nationality: str = ""            # Quốc tịch (vd: "Việt Nam", "Nga")
    notable_works: List[str] = field(default_factory=list)  # Tác phẩm nổi tiếng
    genres: List[str] = field(default_factory=list)          # Thể loại sáng tác

    # --- Nguồn metadata ---
    birth_source: str = ""
    nationality_source: str = ""

    # --- Phân loại ---
    crawl_category: str = ""
    categories: List[str] = field(default_factory=list)

    # --- Crawl metadata ---
    language: str = "vi"
    word_count: int = 0
    char_count: int = 0
    crawled_at: str = ""
    last_modified: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "AuthorArticle":
        return AuthorArticle(**{k: v for k, v in d.items() if k in AuthorArticle.__dataclass_fields__})
