"""
gbooks_config.py -- Cấu hình Google Books Crawler.

Chiến lược tìm kiếm:
1. Theo thể loại + ngôn ngữ: "tiểu thuyết Việt Nam", "truyện ngắn"...
2. Theo tên tác giả nổi tiếng Việt Nam
3. Phân trang qua startIndex (max 40 kết quả/request)

API: https://www.googleapis.com/books/v1/volumes
Giới hạn miễn phí: 1000 request/ngày (với API key)
"""

from pathlib import Path

# ============================================================
#  API KEY -- lay mien phi tai:
#  https://console.cloud.google.com  Enable Books API  Create Credentials
# ============================================================
GOOGLE_BOOKS_API_KEY = "AIzaSyCfsmXjoG1juLm331ZMte0he_l-9FWvTA8"  # Để trống nếu chưa có (giới hạn hơn nhưng vẫn dùng được)

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

# ============================================================
#  RATE LIMITING
# ============================================================
DELAY_BETWEEN_REQUESTS = 1.2    # giây (an toàn cho 1000 req/ngày)
MAX_RETRIES = 4
RETRY_WAIT_MIN = 2
RETRY_WAIT_MAX = 20

# ============================================================
#  PHAN TRANG
# ============================================================
MAX_RESULTS_PER_REQUEST = 40    # Max của Google Books API
MAX_PAGES_PER_QUERY = 25        # 25 trang × 40 = 1000 kết quả/query
MIN_DESCRIPTION_LENGTH = 30     # Bỏ sách không có mô tả (giảm 50→30 để nhận nhiều hơn)

# ============================================================
#  TRUY VAN TIM KIEM -- van hoc Viet Nam
#
#  Moi query co the cho ~401000 ket qua (phan trang).
#  Ket qua se bi deduplicate theo volumeId.
# ============================================================

#  Theo the loai / chu de 
GENRE_QUERIES = [
    "tiểu thuyết Việt Nam",
    "truyện ngắn Việt Nam",
    "thơ Việt Nam",
    "văn học Việt Nam",
    "tuyển tập truyện ngắn Việt Nam",
    "tuyển tập thơ Việt Nam",
    "hồi ký Việt Nam",
    "bút ký Việt Nam",
    "tản văn Việt Nam",
    "ký sự Việt Nam",
    "truyện dài Việt Nam",
    "truyện cổ tích Việt Nam",
    "văn học dân gian Việt Nam",
    "văn học thiếu nhi Việt Nam",
    "truyện tranh Việt Nam",
    "kịch Việt Nam",
    # Thể loại đặc thù
    "tiểu thuyết lịch sử Việt Nam",
    "tiểu thuyết tình cảm Việt Nam",
    "tiểu thuyết chiến tranh Việt Nam",
    "tiểu thuyết trinh thám Việt Nam",
    # Sách dịch sang tiếng Việt (nổi tiếng)
    "tiểu thuyết kinh điển thế giới tiếng Việt",
    "sách dịch văn học nước ngoài",
]

# ── Theo tác giả Việt Nam nổi tiếng ─────────────────────────
# Tìm sách theo tên tác giả để cover những sách không lọc được qua genre
AUTHOR_QUERIES = [
    # ════ Văn học cổ điển ════
    "Nguyễn Du",
    "Nguyễn Đình Chiểu",
    "Hồ Xuân Hương",
    "Đoàn Thị Điểm",
    "Nguyễn Bỉnh Khiêm",

    # ════ Tiền chiến 1930–1945 ════
    "Nam Cao",
    "Vũ Trọng Phụng",
    "Ngô Tất Tố",
    "Nguyễn Công Hoan",
    "Thạch Lam",
    "Nhất Linh",
    "Khái Hưng",
    "Hoàng Đạo",
    "Nguyễn Tuân",
    "Tô Hoài",
    "Bùi Hiển",
    "Nguyên Hồng",
    "Lan Khai",
    "Nguyễn Tường Tam",
    "Đỗ Đức Thu",
    "Kim Lân",
    "Vũ Bằng",
    "Hàn Mặc Tử",
    "Xuân Diệu",
    "Huy Cận",
    "Nguyễn Bính",
    "Tế Hanh",
    "Chế Lan Viên",
    "Tố Hữu",
    "Lưu Trọng Lư",
    "Thế Lữ",
    "Vũ Đình Liên",

    # ════ Kháng chiến & hiện đại 1945–1975 ════
    "Nguyễn Đình Thi",
    "Nguyễn Huy Tưởng",
    "Nguyễn Khải",
    "Nguyễn Minh Châu",
    "Nguyễn Thành Long",
    "Anh Đức",
    "Nguyễn Thi",
    "Nguyễn Quang Sáng",
    "Quang Dũng",
    "Hoàng Cầm",
    "Xuân Quỳnh",
    "Lưu Quang Vũ",
    "Phạm Tiến Duật",
    "Nguyễn Duy",
    "Thanh Thảo",
    "Nguyễn Khoa Điềm",
    "Hữu Thỉnh",
    "Trần Đăng Khoa",
    "Ý Nhi",
    "Lê Anh Xuân",
    "Trần Dần",
    "Lê Đạt",

    # ════ Miền Nam 1954–1975 ════
    "Nhất Linh",
    "Võ Phiến",
    "Duyên Anh",
    "Doãn Quốc Sỹ",
    "Nguyễn Mộng Giác",
    "Nguyễn Thị Hoàng",
    "Sơn Nam",
    "Bình Nguyên Lộc",

    # ════ Đương đại 1975–2000 ════
    "Hồ Anh Thái",
    "Nguyễn Huy Thiệp",
    "Bảo Ninh",
    "Ma Văn Kháng",
    "Chu Lai",
    "Lê Lựu",
    "Dương Thu Hương",
    "Nguyễn Khắc Trường",
    "Nguyễn Quang Lập",
    "Lê Minh Khuê",
    "Phạm Thị Hoài",
    "Nguyễn Bình Phương",
    "Nguyễn Xuân Khánh",
    "Nguyễn Quang Thiều",
    "Nguyễn Việt Hà",
    "Đoàn Minh Phượng",
    "Trần Nhã Thụy",
    "Uông Triều",
    "Nguyễn Một",
    "Trần Thùy Mai",
    "Nguyễn Thị Thu Huệ",
    "Nguyễn Ngọc Tư",
    "Phan Thị Vàng Anh",
    "Nguyễn Quang Thân",
    "Nguyễn Đình Tú",
    "Nguyễn Trí",
    "Phạm Duy Nghĩa",
    "Nguyễn Đông Thức",
    "Nguyễn Thị Minh Ngọc",
    "Phạm Ngọc Tiến",
    "Đỗ Bích Thúy",
    "Tạ Duy Anh",
    "Phan Hồn Nhiên",
    "Trung Trung Đỉnh",
    "Thuận",
    "Nguyễn Vĩnh Nguyên",

    # ════ Đương đại 2000 đến nay ════
    "Nguyễn Nhật Ánh",
    "Trang Hạ",
    "Nguyễn Phong Việt",
    "Anh Khang",
    "Nguyễn Ngọc Thạch",
    "Hamlet Trương",
    "Iris Cao",
    "Rosie Nguyễn",
    "Tuệ Nghi",
    "Gào",
    "Nguyễn Phan Quế Mai",
    "Đặng Hoàng Giang",
    "Trần Thu Trang",
    "Phan Ý Yên",
    "Di Li",
    "Nguyễn Quỳnh Trang",
    "Phạm Hải Anh",
    "Nguyễn Thế Hoàng Linh",
    "Nguyễn Thị Kim Hòa",
    "Nguyễn Ngọc Tiến",
    "Nguyễn Vĩnh Nguyên",
    "Nguyễn Thị Thu Hà",
    "Nguyễn Thị Hậu",
    "Nguyễn Ngọc Tấn",

    # ════ Cận đại / Chí sĩ / Học giả ════
    "Phan Bội Châu",
    "Phan Chu Trinh",
    "Huỳnh Thúc Kháng",
    "Trần Trọng Kim",
    "Nguyễn Văn Vĩnh",
    "Trương Vĩnh Ký",
    "Paulus Huỳnh Tịnh Của",
    "Lương Văn Can",
    "Nguyễn Thượng Hiền",
    "Đào Duy Anh",

    # ════ Văn học hải ngoại ════
    "Mặc Đỗ",
    "Nguyễn Thị Vinh",
    "Nhất Hạnh",
    "Võ Hồng",
    "Sơn Khanh",
    "Kiên Giang",
    "Lê Văn Siêu",
    "Nguyễn Đình Toàn",
    "Nguyễn Tà Cúc",
    "Nguyễn Xuân Hoàng",
    "Trần Vũ",
    "Lê Thị Huệ",
    "Nguyễn Thị Hoàng Bắc",
    "Lê Minh Hà",
    "Phan Việt",
    "Nguyễn Văn Thọ",
    "Nguyễn Thanh Việt",

    # ════ Đương đại bổ sung ════
    "Khuất Quang Thụy",
    "Nguyễn Bảo Sinh",
    "Nguyễn Bắc Sơn",
    "Nguyễn Hữu Quý",
    "Nguyễn Thị Mai",
    "Hồ Thủy Giang",
    "Nguyễn Thị Ngọc Tú",
    "Vũ Tú Nam",
    "Phạm Ngọc Dương",
    "Nguyễn Thị Phương Trâm",
    "Lê Anh Hoài",
    "Nguyễn Ngọc Thuần",
    "Phong Điệp",
    "Nguyễn Danh Lam",
    "Nguyễn Thị Thu Trà",
    "Nguyễn Xuân Thủy",
    "Phạm Thanh Hà",
    "Đỗ Tiến Thụy",

    # ════ Thế hệ 8X–9X ════
    "June Phạm",
    "Huỳnh Trọng Khang",
    "Lê Nguyễn Phương Liên",
    "Keng",
    "Bích Lan",

    # ════ Văn học thiếu nhi ════
    "Võ Quảng",
    "Tô Ngọc Hiến",
    "Nguyễn Kiên",
    "Vũ Hùng",
    "Nguyễn Huy Thắng",
    "Phạm Hổ",
    "Lê Phương Liên",

    # ════ Nghiên cứu / Phê bình văn học ════
    "Trần Đình Sử",
    "Phương Lựu",
    "Lại Nguyên Ân",
    "Nguyễn Đăng Mạnh",
    "Hà Minh Đức",
    "Đỗ Lai Thúy",
    "Chu Văn Sơn",
    "Trịnh Bá Đĩnh",
    "Đặng Anh Đào",

    # ════ Thơ & Văn xuôi bổ sung ════
    "Đặng Nguyệt Anh",
    "Trương Nam Hương",
    "Bích Ngân",
    "Trầm Hương",
    "Ngô Thị Ý Nhi",
    "Lê Thiếu Nhơn",
    "Nguyễn Bính Hồng Cầu",
    "Hoàng Đình Quang",
    "Phạm Sĩ Sáu",
    "Phan Trung Thành",
    "Nguyễn Thị Ngọc Hải",
    "Nguyễn Thu Trân",
    "Cao Xuân Sơn",
    "Phan Ngọc Thường Đoan",
    "Lê Thị Kim",
    "Phan Hoàng",
    "Nguyễn Thu Phương",
    "Lê Hoàng Anh",
    "Trần Hoài Anh",
    "Trần Thị Thắng",
    "Nguyễn Thị Thanh Xuân",
    "Nguyễn Quang Hà",
    "Lê Minh Quốc",
    "Nguyễn Trọng Tạo",

    # ════ Nghiên cứu / Phê bình bổ sung ════
    "Phạm Xuân Nguyên",
    "Nguyễn Huệ Chi",
    "Trần Nho Thìn",
    "Nguyễn Văn Long",
    "Phan Cự Đệ",
    "Đinh Trí Dũng",
    "Nguyễn Thị Bình",
    "Đỗ Đức Hiểu",
    "Lê Ngọc Trà",
    "Nguyễn Thị Minh Thái",
    "Trần Hữu Tá",

    # ════ Sách kỹ năng / Phi hư cấu nổi tiếng ════
    "Nguyễn Hiến Lê",
    "Giản Tư Trung",
    "Phan Văn Trường",
    "Nguyễn Cảnh Bình",
    "Trần Đình Thiên",
    "Phạm Đoan Trang",

    # ════ Nhà sử học / Văn hóa học / Dịch giả nổi tiếng ════
    "Trần Quốc Vượng",
    "Phan Huy Lê",
    "Dương Trung Quốc",
    "Hà Văn Tấn",
    "Nguyễn Khắc Viện",
    "Nguyễn Văn Huyên",
    "Trần Văn Giàu",
    "Phạm Văn Đồng",
    "Võ Nguyên Giáp",
    "Nguyễn Lân",
    "Đinh Gia Khánh",
    "Trần Ngọc Thêm",
    "Nguyễn Từ Chi",
    "Tô Ngọc Thanh",

    # ════ Nhà khoa học Việt Nam có sách phổ biến / hồi ký ════
    "Ngô Bảo Châu",           # Toán học - Nobel, viết tản văn
    "Hoàng Tụy",              # Toán học - hồi ký
    "Tạ Quang Bửu",           # Vật lý - giáo dục
    "Nguyễn Văn Hiệu",        # Vật lý - hồi ký
    "Phan Đình Diệu",         # Tin học - triết học khoa học
    "Tôn Thất Tùng",          # Y học - hồi ký
    "Hồ Đắc Di",              # Y học - y đức
    "Phạm Ngọc Thạch",        # Y tế - hồi ký
    "Lương Định Của",         # Nông học - tiểu sử
    "Trần Đại Nghĩa",         # Kỹ thuật quân sự - hồi ký
    "Nguyễn Lân Dũng",        # Sinh học - sách phổ biến KH
    "Vũ Hà Văn",              # Toán học - sách phổ biến
    "Nguyễn Tiến Dũng",       # Toán học - blog/sách
    "Hồ Tú Bảo",              # AI/Machine learning - phổ biến KH
    "Nguyễn Xuân Xanh",       # Lịch sử khoa học - dịch thuật
    "Lê Nguyên Hoàng",        # Tôn giáo - Phật học
    "Thích Nhất Hạnh",        # Phật học - sách thiền
    "Thích Trí Quang",        # Phật học
    "Thích Thanh Từ",         # Phật học
    "Nhất Hạnh",              # đã bao gồm trên
]

# ── Kết hợp GENRE_QUERIES + AUTHOR_QUERIES → ALL_QUERIES ────
ALL_QUERIES = GENRE_QUERIES + AUTHOR_QUERIES

# ============================================================
#  LƯU TRỮ
# ============================================================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR_GBOOKS = BASE_DIR / "data" / "raw_v2" / "books"   # Dùng CHUNG với wiki books
PROGRESS_FILE_GBOOKS = BASE_DIR / "data" / "gbooks_progress.json"

# Tạo thư mục nếu chưa có
DATA_DIR_GBOOKS.mkdir(parents=True, exist_ok=True)

# ============================================================
#  LOGGING
# ============================================================
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "data" / "gbooks_crawler.log"
