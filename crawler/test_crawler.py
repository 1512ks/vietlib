"""
test_crawler.py -- Script kiểm tra nhanh (chạy trước khi crawl thật)

Chạy:
    cd C:\\Users\\Admin\\Desktop\\ĐATN\\crawler
    python test_crawler.py
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_api_connection():
    """Kiem tra ket noi Wikipedia API."""
    print("1️⃣  Kiểm tra kết nối API Wikipedia tiếng Việt...")
    import requests
    from config import WIKI_BASE_URL, USER_AGENT

    try:
        r = requests.get(
            WIKI_BASE_URL,
            params={"action": "query", "meta": "siteinfo", "format": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        sitename = data["query"]["general"]["sitename"]
        print(f"   ✅ Kết nối OK -- Site: {sitename}")
        return True
    except Exception as e:
        print(f"   ❌ Lỗi kết nối: {e}")
        return False


def test_category_members():
    """Lay thu 5 bai tu 'The_loai:Nha van Viet Nam'."""
    print("\n2️⃣  Lấy thử danh sách bài từ 'Nhà văn Việt Nam'...")
    import requests
    from config import WIKI_BASE_URL, USER_AGENT

    try:
        r = requests.get(
            WIKI_BASE_URL,
            params={
                "action": "query",
                "list": "categorymembers",
                "cmtitle": "Thể_loại:Nhà văn Việt Nam",
                "cmlimit": 5,
                "cmtype": "page",
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        r.raise_for_status()
        members = r.json()["query"]["categorymembers"]
        print(f"   ✅ Tìm thấy {len(members)} bài (sample):")
        for m in members:
            print(f"      - [{m['pageid']}] {m['title']}")
        return True
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return False


def test_fetch_article():
    """Lấy thử nội dung bài 'Nguyễn Du'."""
    print("\n3️⃣  Lấy thử nội dung bài 'Nguyễn Du'...")
    import requests
    from config import WIKI_BASE_URL, USER_AGENT

    try:
        r = requests.get(
            WIKI_BASE_URL,
            params={
                "action": "query",
                "titles": "Nguyễn Du",
                "prop": "extracts|info",
                "exintro": True,
                "explaintext": True,
                "inprop": "url",
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        r.raise_for_status()
        pages = r.json()["query"]["pages"]
        page = next(iter(pages.values()))
        content = page.get("extract", "")[:300]
        url = page.get("fullurl", "N/A")
        print(f"   ✅ Bài: {page.get('title')}")
        print(f"   URL: {url}")
        print(f"   Nội dung (300 ký tự đầu):\n   {content}...")
        return True
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return False


def test_storage():
    """Kiểm tra lưu và đọc file JSON."""
    print("\n4️⃣  Kiểm tra lưu JSON...")
    try:
        from models import WikiArticle
        from storage import Storage

        art = WikiArticle(
            id="test_001",
            title="Bài kiểm tra",
            url="https://vi.wikipedia.org/wiki/Test",
            category="Test Category",
            content="Đây là nội dung thử nghiệm " * 30,
            summary="Tóm tắt thử nghiệm.",
        )
        storage = Storage()
        path = storage.save_article(art)
        print(f"   ✅ Lưu thành công: {path}")

        # Đọc lại
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        print(f"   ✅ Đọc lại OK — title: {data['title']}, word_count: {data['word_count']}")
        return True
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("  KIỂM TRA CRAWLER WIKIPEDIA")
    print("=" * 50)

    results = [
        test_api_connection(),
        test_category_members(),
        test_fetch_article(),
        test_storage(),
    ]

    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"  ✅ TẤT CẢ {total}/{total} KIỂM TRA THÀNH CÔNG!")
        print("  → Sẵn sàng chạy crawler thật: python main.py --test")
    else:
        print(f"  ⚠️  {passed}/{total} kiểm tra thành công. Kiểm tra lỗi phía trên.")
    print("=" * 50)
