"""
config.py -- Cấu hình toàn bộ crawler
"""

from pathlib import Path

# ============================================================
#  WIKIPEDIA API SETTINGS
# ============================================================

# User-agent bat buoc theo quy dinh Wikipedia API
USER_AGENT = "DATN-LibraryChatbot/1.0 (sinh vien DHBKHN; lien he: your_email@hust.edu.vn)"

WIKI_LANGUAGE = "vi"                  # Tiếng Việt
WIKI_BASE_URL = "https://vi.wikipedia.org/w/api.php"

# ============================================================
#  RATE LIMITING
# ============================================================
# Wikipedia cho phep ~200 req/phut khong can dang nhap
# Ta dung 30 req/phut de an toan (tranh bi block)

REQUESTS_PER_MINUTE = 30             # Số request tối đa mỗi phút
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE   # = 2.0 giây
DELAY_BETWEEN_CATEGORIES = 3.0       # Nghỉ 3s khi chuyển sang danh mục mới

# Retry khi gap loi mang
MAX_RETRIES = 5
RETRY_WAIT_MIN = 2                   # Chờ tối thiểu 2s trước khi retry
RETRY_WAIT_MAX = 30                  # Chờ tối đa 30s

# ============================================================
#  CRAWL DE QUI DANH MUC CON
# ============================================================
# Crawl de quy vao subcategories (danh muc con)
# depth=0: chi bai truc tiep (~391 bai)
# depth=2: bai + subcategory + sub-subcategory (~vai nghin bai)
# depth=3: toan bo cay (~chuc nghin bai, chay rat lau)
SUBCATEGORY_MAX_DEPTH = 2

# ============================================================
#  NOI DUNG CRAWL
# ============================================================
MIN_CONTENT_LENGTH = 200             # Giảm xuống 200 để bắt thêm bài
MAX_ARTICLES_PER_CATEGORY = None     # None = không giới hạn (crawl hết)

# ============================================================
#  DANH MUC CRAWL (danh muc goc -- crawler se tu de quy vao con)
# ============================================================
# Dung cac danh muc CHA rong nhat de crawler tu kham pha subcategory

CATEGORIES = {
    # ── VĂN HỌC VIỆT NAM (danh mục cha bao quát nhất) ──
    "Văn học Việt Nam":         "Văn học Việt Nam",
    "Tác phẩm văn học Việt Nam":"Tác phẩm văn học Việt Nam",

    # ── THEO THỂ LOẠI ──
    "Tiểu thuyết Việt Nam":     "Tiểu thuyết Việt Nam",
    "Truyện ngắn Việt Nam":     "Truyện ngắn Việt Nam",
    "Thơ Việt Nam":             "Thơ Việt Nam",
    "Truyện thơ Việt Nam":      "Truyện thơ Việt Nam",
    "Kịch Việt Nam":            "Kịch Việt Nam",
    "Ký Việt Nam":              "Ký Việt Nam",
    "Truyện tranh Việt Nam":    "Truyện tranh Việt Nam",

    # ── THEO GIAI ĐOẠN ──
    "Văn học dân gian Việt Nam":    "Văn học dân gian Việt Nam",
    "Văn học cổ điển Việt Nam":     "Văn học cổ điển Việt Nam",
    "Văn học hiện đại Việt Nam":    "Văn học hiện đại Việt Nam",
    "Văn học đương đại Việt Nam":   "Văn học đương đại Việt Nam",

    # ── TÁC GIẢ ──
    "Nhà văn Việt Nam":     "Nhà văn Việt Nam",
    "Nhà thơ Việt Nam":     "Nhà thơ Việt Nam",
    "Tác giả Việt Nam":     "Tác giả Việt Nam",
    "Nhà văn Hà Nội":       "Nhà văn Hà Nội",

    # ── ĐỐI TƯỢNG ĐỌC GIẢ ──
    "Văn học thiếu nhi Việt Nam":  "Văn học thiếu nhi Việt Nam",
    "Sách thiếu nhi Việt Nam":     "Sách thiếu nhi Việt Nam",

    # ── SÁCH ──
    "Sách tiếng Việt":      "Sách tiếng Việt",
    "Sách Việt Nam":        "Sách Việt Nam",

    # ── BỔ SUNG LĨNH VỰC LIÊN QUAN ──
    "Tiểu sử người Việt Nam":  "Tiểu sử người Việt Nam",
    "Lịch sử Việt Nam":        "Lịch sử Việt Nam",
}

# ============================================================
#  LƯU TRỮ
# ============================================================

BASE_DIR = Path(__file__).parent.parent    # Thư mục ĐATN
DATA_DIR = BASE_DIR / "data" / "raw"       # Nơi lưu file JSON
PROGRESS_FILE = BASE_DIR / "data" / "crawl_progress.json"   # Theo dõi tiến độ

# Tự tạo thư mục nếu chưa có
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
#  LOGGING
# ============================================================
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "data" / "crawler.log"
