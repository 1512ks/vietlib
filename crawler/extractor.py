"""
extractor.py -- Trích xuất metadata có cấu trúc từ bài Wikipedia.

Hệ thống trích xuất đa nguồn (fallback chain):
    1. Infobox wikitext  (độ chính xác cao nhất)
    2. Wikidata API      (dữ liệu có cấu trúc, phủ rộng)
    3. Regex trên content (fallback cuối cùng)

Áp dụng cho: tác giả, năm xuất bản, thể loại.
"""

import re
import time
import logging
from typing import Optional, Tuple, List, Dict, Any

import requests

logger = logging.getLogger(__name__)

#  Wikidata property IDs 
WD = {
    "author":           "P50",    # tác giả
    "publication_date": "P577",   # ngày xuất bản
    "genre":            "P136",   # thể loại
    "nationality":      "P27",    # quốc tịch
    "birth":            "P569",   # ngày sinh
    "death":            "P570",   # ngày mất
    "notable_works":    "P800",   # tác phẩm nổi tiếng
    "instance_of":      "P31",    # là thể hiện của (để nhận biết book/human)
}

#  Instance-of Q-IDs 
WD_BOOK_INSTANCES = {
    "Q7725634",   # literary work
    "Q571",       # book
    "Q8261",      # novel
    "Q482994",    # album (loại trừ)
    "Q49084",     # short story
    "Q5185279",   # poem
    "Q5633421",   # scientific journal
    "Q1760610",   # collection of poems
    "Q386724",    # work
}
WD_HUMAN_INSTANCE = "Q5"


# ============================================================
#  WIKIDATA API
# ============================================================

def get_wikidata_id(page_id: int, session: requests.Session, base_url: str) -> str:
    """Lấy Wikidata Q-ID từ Wikipedia page_id qua pageprops."""
    params = {
        "action": "query",
        "pageids": page_id,
        "prop": "pageprops",
        "ppprop": "wikibase_item",
        "format": "json",
    }
    try:
        resp = session.get(base_url, params=params, timeout=15)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values()), {})
        return page.get("pageprops", {}).get("wikibase_item", "")
    except Exception as e:
        logger.debug(f"Cannot get wikidata_id for page {page_id}: {e}")
        return ""


def get_wikidata_claims(qid: str, session: requests.Session,
                        wikidata_url: str) -> Dict[str, Any]:
    """Lấy toàn bộ claims của một Wikidata entity."""
    if not qid:
        return {}
    params = {
        "action": "wbgetentities",
        "ids": qid,
        "props": "claims|labels",
        "languages": "vi|en",
        "format": "json",
    }
    try:
        resp = session.get(wikidata_url, params=params, timeout=15)
        data = resp.json()
        entity = data.get("entities", {}).get(qid, {})
        return entity.get("claims", {})
    except Exception as e:
        logger.debug(f"Cannot get wikidata claims for {qid}: {e}")
        return {}


def _wd_string_value(claims: dict, prop: str) -> str:
    """Lấy giá trị string đầu tiên của một property."""
    entries = claims.get(prop, [])
    if not entries:
        return ""
    try:
        val = entries[0]["mainsnak"]["datavalue"]["value"]
        if isinstance(val, str):
            return val
        if isinstance(val, dict):
            return val.get("text", "") or val.get("id", "")
    except (KeyError, IndexError):
        pass
    return ""


def _wd_year(claims: dict, prop: str) -> str:
    """Lấy năm từ datetime property (P577, P569, P570)."""
    entries = claims.get(prop, [])
    if not entries:
        return ""
    try:
        time_str = entries[0]["mainsnak"]["datavalue"]["value"]["time"]
        # Định dạng: "+1965-01-01T00:00:00Z"
        m = re.search(r'[+-](\d{4})', time_str)
        if m:
            return m.group(1)
    except (KeyError, IndexError, TypeError):
        pass
    return ""


def _wd_entity_label(qid: str, session: requests.Session, wikidata_url: str) -> str:
    """Lấy nhãn tiếng Việt (hoặc tiếng Anh) của một Wikidata entity."""
    if not qid:
        return ""
    params = {
        "action": "wbgetentities",
        "ids": qid,
        "props": "labels",
        "languages": "vi|en",
        "format": "json",
    }
    try:
        resp = session.get(wikidata_url, params=params, timeout=10)
        data = resp.json()
        labels = data.get("entities", {}).get(qid, {}).get("labels", {})
        return labels.get("vi", {}).get("value", "") or labels.get("en", {}).get("value", "")
    except Exception:
        return ""


def get_wikidata_book_metadata(qid: str, session: requests.Session,
                               wikidata_url: str) -> Dict[str, str]:
    """
    Lấy metadata sách từ Wikidata: author, publication_year, genre.
    Trả về dict với keys: author, publication_year, genre (đều là string).
    """
    if not qid:
        return {}
    claims = get_wikidata_claims(qid, session, wikidata_url)
    if not claims:
        return {}

    result = {}

    # Năm xuất bản (P577)
    year = _wd_year(claims, WD["publication_date"])
    if year:
        result["publication_year"] = year

    # Tác giả (P50) — lấy label của QID tác giả
    author_entries = claims.get(WD["author"], [])
    if author_entries:
        try:
            author_qid = author_entries[0]["mainsnak"]["datavalue"]["value"]["id"]
            label = _wd_entity_label(author_qid, session, wikidata_url)
            if label:
                result["author"] = label
                result["authors"] = [
                    _wd_entity_label(
                        e["mainsnak"]["datavalue"]["value"]["id"],
                        session, wikidata_url
                    )
                    for e in author_entries[:5]
                    if e.get("mainsnak", {}).get("datavalue")
                ]
                result["authors"] = [a for a in result["authors"] if a]
        except (KeyError, IndexError):
            pass

    # Thể loại (P136)
    genre_entries = claims.get(WD["genre"], [])
    if genre_entries:
        genres = []
        for e in genre_entries[:3]:
            try:
                gqid = e["mainsnak"]["datavalue"]["value"]["id"]
                label = _wd_entity_label(gqid, session, wikidata_url)
                if label:
                    genres.append(label)
            except (KeyError, IndexError):
                pass
        if genres:
            result["genres"] = genres
            result["genre"] = genres[0]

    return result


def get_wikidata_author_metadata(qid: str, session: requests.Session,
                                 wikidata_url: str) -> Dict[str, Any]:
    """Lấy metadata tác giả từ Wikidata: birth_year, death_year, nationality."""
    if not qid:
        return {}
    claims = get_wikidata_claims(qid, session, wikidata_url)
    if not claims:
        return {}

    result = {}

    birth = _wd_year(claims, WD["birth"])
    if birth:
        result["birth_year"] = birth

    death = _wd_year(claims, WD["death"])
    if death:
        result["death_year"] = death

    nat_entries = claims.get(WD["nationality"], [])
    if nat_entries:
        try:
            nat_qid = nat_entries[0]["mainsnak"]["datavalue"]["value"]["id"]
            label = _wd_entity_label(nat_qid, session, wikidata_url)
            if label:
                result["nationality"] = label
        except (KeyError, IndexError):
            pass

    return result


# ============================================================
#  INFOBOX PARSER
# ============================================================

# Map các tên trường infobox phổ biến (tiếng Việt & tiếng Anh) sang key chuẩn
_INFOBOX_FIELD_MAP = {
    # Tác giả
    "tác giả":          "author",
    "tac gia":          "author",
    "author":           "author",
    "authors":          "author",
    "người viết":       "author",
    "nhà văn":          "author",

    # Năm / ngày xuất bản
    "năm phát hành":    "publication_year",
    "năm xuất bản":     "publication_year",
    "ngày xuất bản":    "publication_year",
    "publication date": "publication_year",
    "published":        "publication_year",
    "release date":     "publication_year",
    "năm":              "publication_year",

    # Thể loại
    "thể loại":         "genre",
    "thể loại văn học": "genre",
    "genre":            "genre",
    "loại hình":        "genre",

    # Tác giả (Author article)
    "sinh":             "birth_year",
    "ngày sinh":        "birth_year",
    "born":             "birth_year",
    "mất":              "death_year",
    "ngày mất":         "death_year",
    "died":             "death_year",
    "quốc tịch":        "nationality",
    "nationality":      "nationality",
    "quê hương":        "nationality",

    # Tác phẩm nổi tiếng
    "tác phẩm nổi tiếng": "notable_works",
    "notable works":      "notable_works",
    "tác phẩm":           "notable_works",
}


def parse_infobox(wikitext: str) -> Dict[str, str]:
    """
    Parse Infobox từ wikitext thô.
    Trả về dict {field_key: value} theo _INFOBOX_FIELD_MAP.
    """
    result = {}
    if not wikitext:
        return result

    # Tìm tất cả các trường dạng: | tên trường = giá trị
    # Xử lý nhiều dòng bằng cách tách theo dấu |
    # Dùng regex lookahead để split chính xác
    field_pattern = re.compile(
        r'\|\s*([^=|\n<{}]+?)\s*=\s*([^|{}\n]*(?:\n(?![|{}]).*)*)',
        re.MULTILINE
    )

    for m in field_pattern.finditer(wikitext):
        raw_key = m.group(1).strip().lower().rstrip(":")
        raw_val = m.group(2).strip()

        # Loại bỏ wiki markup cơ bản: [[link|text]] → text, {{...}} → trống
        raw_val = re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]', r'\1', raw_val)
        raw_val = re.sub(r'\{\{[^}]+\}\}', '', raw_val)
        raw_val = re.sub(r"'''?", '', raw_val)
        raw_val = re.sub(r'<[^>]+>', '', raw_val)
        raw_val = raw_val.strip()

        if not raw_val:
            continue

        std_key = _INFOBOX_FIELD_MAP.get(raw_key, "")
        if not std_key:
            continue

        # Nếu đã có giá trị, không ghi đè (ưu tiên trường đầu tiên)
        if std_key not in result:
            result[std_key] = raw_val

    # Post-process: trích năm từ giá trị ngày dạng "1 tháng 1 năm 1965"
    for year_key in ("publication_year", "birth_year", "death_year"):
        if year_key in result:
            y = _extract_year_from_string(result[year_key])
            if y:
                result[year_key] = y

    return result


def _extract_year_from_string(s: str) -> str:
    """Trích xuất năm (4 chữ số 19xx/20xx) từ chuỗi bất kỳ."""
    m = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', s)
    return m.group(1) if m else ""


# ============================================================
#  REGEX FALLBACK
# ============================================================

# Các pattern nhận biết thể loại từ đầu bài (content)
_GENRE_PATTERNS = [
    (r'\btiểu thuyết\b',        "Tiểu thuyết"),
    (r'\btruyện ngắn\b',        "Truyện ngắn"),
    (r'\btập thơ\b',            "Tập thơ"),
    (r'\btrường ca\b',          "Trường ca"),
    (r'\btruyện thơ\b',         "Truyện thơ"),
    (r'\bkịch\b',               "Kịch"),
    (r'\bhồi ký\b',             "Hồi ký"),
    (r'\bký sự\b',              "Ký sự"),
    (r'\btruyện cổ tích\b',     "Truyện cổ tích"),
    (r'\btruyện tranh\b',       "Truyện tranh"),
    (r'\bthơ\b',                "Thơ"),
    (r'\bnovel\b',              "Tiểu thuyết"),
    (r'\bshort story\b',        "Truyện ngắn"),
]

# Patterns trích xuất tác giả từ câu đầu bài
_AUTHOR_PATTERNS = [
    r'(?:của|do|viết bởi|sáng tác bởi)\s+(?:nhà văn\s+)?([A-ZĐÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂẮẶẢẠẦỐ][^\s,\.]{1,30}(?:\s+[A-ZĐÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂẮẶẢẠẦỐ][^\s,\.]{1,30}){0,3})',
    r'là\s+(?:một\s+)?(?:tiểu thuyết|tác phẩm|truyện ngắn|tập thơ|bài thơ|hồi ký|kịch)\s+của\s+([A-ZĐÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂẮẶẢẠẦỐ][^\s,\.]{1,30}(?:\s+[A-ZĐÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂẮẶẢẠẦỐ][^\s,\.]{1,30}){0,3})',
]


def extract_genre_from_content(content: str, categories: List[str]) -> Tuple[str, str]:
    """
    Thể loại từ content regex + categories.
    Trả về (genre, source).
    """
    # Nguồn 1: Regex trên 3 đoạn đầu
    first_section = " ".join(content.split("\n")[:10]).lower()
    for pattern, genre_label in _GENRE_PATTERNS:
        if re.search(pattern, first_section, re.IGNORECASE):
            return genre_label, "regex"

    # Nguồn 2: Từ categories
    cats_lower = " ".join(categories).lower()
    for pattern, genre_label in _GENRE_PATTERNS:
        if re.search(pattern, cats_lower, re.IGNORECASE):
            return genre_label, "categories"

    return "", ""


def extract_author_from_content(content: str) -> Tuple[str, str]:
    """
    Trích xuất tên tác giả từ content bằng regex.
    Trả về (author_name, source).
    """
    first_para = " ".join(content.split("\n")[:5])
    for pattern in _AUTHOR_PATTERNS:
        m = re.search(pattern, first_para)
        if m:
            candidate = m.group(1).strip()
            words = candidate.split()
            if 2 <= len(words) <= 5:
                return candidate, "regex"
    return "", ""


def extract_year_from_content(content: str) -> Tuple[str, str]:
    """
    Trích xuất năm xuất bản từ nội dung bài.
    Trả về (year, source).
    """
    first_section = "\n".join(content.split("\n")[:20])
    patterns = [
        r'(?:xuất bản|phát hành|ra mắt|in lần đầu|công bố)\s+(?:năm\s+)?(\b(?:19|20)\d{2}\b)',
        r'năm\s+(\b(?:19|20)\d{2}\b)\s*[,\.]?\s*(?:bởi|do|nhà xuất bản)',
        r'\((\b(?:19|20)\d{2}\b)\)',
    ]
    for p in patterns:
        m = re.search(p, first_section, re.IGNORECASE)
        if m:
            return m.group(1), "regex"
    return "", ""


# ============================================================
#  PHÂN LOẠI BÀI VIẾT
# ============================================================

def classify_article(title: str, categories: List[str], content: str,
                     crawl_category: str) -> str:
    """
    Phân loại article thành 'book' hoặc 'author'.
    
    Logic:
    - Nếu crawl_category nằm trong AUTHOR_CATEGORIES → "author"
    - Nếu categories chứa từ khoá tác giả  → "author"
    - Mặc định → "book" (ưu tiên không bỏ sót tác phẩm)
    """
    from config_v2 import AUTHOR_CATEGORY_KEYWORDS, AUTHOR_CATEGORIES

    # Kiểm tra từ danh mục crawl gốc
    if crawl_category in AUTHOR_CATEGORIES:
        return "author"

    cats_text = " ".join(categories).lower()
    content_start = content[:500].lower()

    # Kiểm tra từ khoá tác giả trong categories
    for kw in AUTHOR_CATEGORY_KEYWORDS:
        if kw in cats_text:
            return "author"

    # Kiểm tra các dấu hiệu rõ ràng của tác giả trong content
    author_signals = [
        r'\blà\s+(?:một\s+)?(?:nhà văn|nhà thơ|tác giả|nhà soạn kịch)\b',
        r'\bsinh\s+(?:ngày\s+)?\d+\s+tháng\b',
        r'\bsinh\s+năm\s+(?:19|20)\d{2}\b',
    ]
    for sig in author_signals:
        if re.search(sig, content_start, re.IGNORECASE):
            return "author"

    return "book"
