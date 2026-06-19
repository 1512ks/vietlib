"""
config_v2.py -- Cấu hình crawler V2: tập trung thu thập tác phẩm văn học & tác giả.
"""

from pathlib import Path

# ============================================================
#  WIKIPEDIA API SETTINGS
# ============================================================
USER_AGENT = "DATN-LibraryChatbot/2.0 (sinh vien DHBKHN; lien he: datn@hust.edu.vn)"
WIKI_LANGUAGE = "vi"
WIKI_BASE_URL = "https://vi.wikipedia.org/w/api.php"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"

# ============================================================
#  RATE LIMITING
# ============================================================
REQUESTS_PER_MINUTE = 30
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE   # = 2.0 giây
DELAY_BETWEEN_CATEGORIES = 3.0

MAX_RETRIES = 5
RETRY_WAIT_MIN = 2
RETRY_WAIT_MAX = 30

# ============================================================
#  CRAWL DE QUI
# ============================================================
# depth=3 de bat duoc toi da bai tu cac subcategory long nhau
SUBCATEGORY_MAX_DEPTH = 3

# ============================================================
#  NOI DUNG CRAWL
# ============================================================
MIN_CONTENT_LENGTH = 150   # Thấp hơn để không bỏ sót tác phẩm ngắn
MAX_ARTICLES_PER_CATEGORY = None   # Không giới hạn

# ============================================================
#  DANH MUC TAC PHAM VAN HOC -- toan dien VN + quoc te
#
#  Nguyen tac: Chi giu danh muc CHA thuc su DISJOINT.
#  SUBCATEGORY_MAX_DEPTH=3 tu de quy vao tat ca danh muc con.
# ============================================================
BOOK_CATEGORIES = {
# 
    #  VAN HOC VIET NAM -- liet ke TUONG MINH tung the loai
    #  Ly do: depth=3 co the bo sot bai o depth 4+
    #  (VD: VH VN  Van xuoi VN  Tieu thuyet VN  bai cu the)
    # 

    # Tác phẩm & thể loại chính
    "Tác phẩm văn học Việt Nam":         "Tác phẩm văn học Việt Nam",
    "Văn xuôi Việt Nam":                 "Văn xuôi Việt Nam",       # chứa TT, truyện ngắn...
    "Tiểu thuyết Việt Nam":              "Tiểu thuyết Việt Nam",
    "Truyện ngắn Việt Nam":              "Truyện ngắn Việt Nam",
    "Thơ Việt Nam":                      "Thơ Việt Nam",
    "Bút ký Việt Nam":                   "Bút ký Việt Nam",
    "Sân khấu cổ truyền Việt Nam":       "Sân khấu cổ truyền Việt Nam",  # kịch, tuồng, chèo...
    "Sách Việt Nam":                     "Sách Việt Nam",

    # Văn học theo nguồn gốc / thời kỳ
    "Văn học dân gian Việt Nam":         "Văn học dân gian Việt Nam",
    "Truyền thuyết Việt Nam":            "Truyền thuyết Việt Nam",
    "Văn học thiếu nhi Việt Nam":        "Văn học thiếu nhi Việt Nam",
    "Truyện tranh Việt Nam":             "Truyện tranh Việt Nam",

    # ═══════════════════════════════════════════════════════
    #  VĂN HỌC NƯỚC NGOÀI — TIỂU THUYẾT theo quốc gia
    #  (disjoint nhau, không nằm trong "Văn học Việt Nam")
    # ═══════════════════════════════════════════════════════
    "Tiểu thuyết Nga":                   "Tiểu thuyết Nga",
    "Tiểu thuyết Pháp":                  "Tiểu thuyết Pháp",
    "Tiểu thuyết Anh":                   "Tiểu thuyết Anh",
    "Tiểu thuyết Mỹ":                    "Tiểu thuyết Mỹ",
    "Tiểu thuyết Trung Quốc":            "Tiểu thuyết Trung Quốc",
    "Tiểu thuyết Nhật Bản":              "Tiểu thuyết Nhật Bản",
    "Tiểu thuyết Đức":                   "Tiểu thuyết Đức",
    "Tiểu thuyết Tây Ban Nha":           "Tiểu thuyết Tây Ban Nha",
    "Tiểu thuyết Ý":                     "Tiểu thuyết Ý",
    "Tiểu thuyết Hàn Quốc":              "Tiểu thuyết Hàn Quốc",
    "Tiểu thuyết Bồ Đào Nha":           "Tiểu thuyết Bồ Đào Nha",
    "Tiểu thuyết Colombia":              "Tiểu thuyết Colombia",
    "Tiểu thuyết Argentina":             "Tiểu thuyết Argentina",

    # ═══════════════════════════════════════════════════════
    #  VĂN HỌC NƯỚC NGOÀI — TRUYỆN NGẮN theo quốc gia
    # ═══════════════════════════════════════════════════════
    "Truyện ngắn Nga":                   "Truyện ngắn Nga",
    "Truyện ngắn Pháp":                  "Truyện ngắn Pháp",
    "Truyện ngắn Mỹ":                    "Truyện ngắn Mỹ",
    "Truyện ngắn Trung Quốc":            "Truyện ngắn Trung Quốc",
    "Truyện ngắn Nhật Bản":              "Truyện ngắn Nhật Bản",

    # ═══════════════════════════════════════════════════════
    #  VĂN HỌC NƯỚC NGOÀI — THƠ theo quốc gia
    # ═══════════════════════════════════════════════════════
    "Thơ Nga":                           "Thơ Nga",
    "Thơ Pháp":                          "Thơ Pháp",
    "Thơ Anh":                           "Thơ Anh",
    "Thơ Mỹ":                            "Thơ Mỹ",
    "Thơ Trung Quốc":                    "Thơ Trung Quốc",
    "Thơ Nhật Bản":                      "Thơ Nhật Bản",

    # ═══════════════════════════════════════════════════════
    #  DANH MỤC CHÉO — GIẢI THƯỞNG & ĐẶC BIỆT
    #  (disjoint hoàn toàn với tất cả danh mục trên)
    # ═══════════════════════════════════════════════════════
    "Tác phẩm đoạt giải Nobel văn học":  "Tác phẩm đoạt giải Nobel văn học",
    "Tác phẩm đoạt giải Pulitzer":       "Tác phẩm đoạt giải Pulitzer",
    "Sách được chuyển thể thành phim":   "Sách được chuyển thể thành phim",
    "Sách thiếu nhi":                    "Sách thiếu nhi",
}

# ============================================================
#  DANH MỤC TÁC GIẢ VĂN HỌC
#  Nguyên tắc: danh mục cha disjoint.
#  "Nhà văn Việt Nam" đã bao gồm "Nhà văn Hà Nội", "Nhà văn nữ VN"...
# ============================================================
AUTHOR_CATEGORIES = {
    # ── TÁC GIẢ VIỆT NAM ──
    "Nhà văn Việt Nam":                  "Nhà văn Việt Nam",
    "Nhà thơ Việt Nam":                  "Nhà thơ Việt Nam",

    # ── TÁC GIẢ NƯỚC NGOÀI — disjoint theo quốc gia ──
    "Nhà văn đoạt giải Nobel Văn học":   "Nhà văn đoạt giải Nobel Văn học",
    "Nhà văn Nga":                       "Nhà văn Nga",
    "Nhà văn Pháp":                      "Nhà văn Pháp",
    "Nhà văn Mỹ":                        "Nhà văn Mỹ",
    "Nhà văn Anh":                       "Nhà văn Anh",
    "Nhà văn Trung Quốc":                "Nhà văn Trung Quốc",
    "Nhà văn Nhật Bản":                  "Nhà văn Nhật Bản",
    "Nhà văn Đức":                       "Nhà văn Đức",
    "Nhà văn Tây Ban Nha":               "Nhà văn Tây Ban Nha",
    "Nhà văn Ý":                         "Nhà văn Ý",
    "Nhà văn Hàn Quốc":                  "Nhà văn Hàn Quốc",
}

# ── TỪ KHOÁ PHÂN LOẠI (dùng để nhận diện article là sách hay tác giả) ──

# Từ khoá trong TITLE cho thấy đây là tác phẩm văn học
WORK_TITLE_KEYWORDS = []  # Không dùng title keywords, dùng categories

# Categories của bài che rõ đây là SÁCH/TÁC PHẨM
WORK_CATEGORY_KEYWORDS = [
    "tiểu thuyết", "truyện ngắn", "tập thơ", "thơ", "truyện thơ",
    "kịch", "ký", "hồi ký", "truyện dài", "tác phẩm văn học",
    "sách", "truyện cổ tích", "truyện tranh", "văn học",
    "novel", "poem", "poetry", "book", "fiction",
]

# Categories của bài cho thấy đây là TÁC GIẢ
AUTHOR_CATEGORY_KEYWORDS = [
    "nhà văn", "nhà thơ", "tác giả", "nhà soạn kịch",
    "nhà viết kịch", "nhà văn nữ",
]

# ============================================================
#  LƯU TRỮ — Thư mục mới (v2) để không ghi đè dữ liệu cũ
# ============================================================
BASE_DIR = Path(__file__).parent.parent          # Thư mục ĐATN
DATA_DIR_V2 = BASE_DIR / "data" / "raw_v2"      # Thư mục gốc mới
DATA_DIR_BOOKS = DATA_DIR_V2 / "books"           # Tác phẩm văn học
DATA_DIR_AUTHORS = DATA_DIR_V2 / "authors"       # Tác giả
PROGRESS_FILE_V2 = BASE_DIR / "data" / "crawl_progress_v2.json"

# Tự tạo thư mục
DATA_DIR_BOOKS.mkdir(parents=True, exist_ok=True)
DATA_DIR_AUTHORS.mkdir(parents=True, exist_ok=True)

# ============================================================
#  LOGGING
# ============================================================
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "data" / "crawler_v2.log"
