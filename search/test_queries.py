"""
test_queries.py -- Tập test queries + ground truth cho đánh giá retrieval.

Ground truth được xây dựng thủ công từ metadata của corpus:
  - Mỗi query có 1 danh sách relevant_doc_ids
  - Relevant doc_ids là Chroma IDs (chunk_id) chứa thông tin liên quan

Phân loại queries:
  - FACTUAL  : Hỏi về tác giả, tên sách cụ thể
  - SEMANTIC : Hỏi theo chủ đề, thể loại, nội dung
  - AUTHOR   : Tìm tác phẩm của tác giả cụ thể
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class TestQuery:
    query_id: str
    query: str
    query_type: str          # "FACTUAL" | "SEMANTIC" | "AUTHOR"
    relevant_doc_ids: List[str] = field(default_factory=list)
    # Neu relevant_doc_ids rong  dung relevant_keywords de danh gia gan dung
    relevant_keywords: List[str] = field(default_factory=list)
    description: str = ""


# ============================================================
#  Test Queries
#  Chu y: relevant_doc_ids se duoc tu dong dien sau khi
#  chay search lan dau va kiem tra ket qua thu cong.
#  Hien tai dung relevant_keywords de auto-evaluate.
# ============================================================
TEST_QUERIES: List[TestQuery] = [
    #  FACTUAL 
    TestQuery(
        query_id="F001",
        query="Chí Phèo là tác phẩm của tác giả nào",
        query_type="FACTUAL",
        relevant_keywords=["chí phèo", "nam cao"],
        description="Hỏi tác giả của tác phẩm cụ thể",
    ),
    TestQuery(
        query_id="F002",
        query="Số đỏ của Vũ Trọng Phụng",
        query_type="FACTUAL",
        relevant_keywords=["số đỏ", "vũ trọng phụng"],
        description="Tìm sách theo tên + tác giả",
    ),
    TestQuery(
        query_id="F003",
        query="Truyện Kiều Nguyễn Du",
        query_type="FACTUAL",
        relevant_keywords=["truyện kiều", "nguyễn du"],
        description="Tìm tác phẩm văn học cổ điển",
    ),
    TestQuery(
        query_id="F004",
        query="Tắt đèn Ngô Tất Tố viết về nông dân",
        query_type="FACTUAL",
        relevant_keywords=["tắt đèn", "ngô tất tố"],
        description="Tìm sách theo tên + chủ đề",
    ),
    TestQuery(
        query_id="F005",
        query="Đoạn trường tân thanh Nguyễn Gia Thiều",
        query_type="FACTUAL",
        relevant_keywords=["đoạn trường tân thanh", "nguyễn gia thiều"],
        description="Tác phẩm văn học chữ Nôm",
    ),

    # ── AUTHOR ──
    TestQuery(
        query_id="A001",
        query="Tác phẩm của Nguyễn Nhật Ánh",
        query_type="AUTHOR",
        relevant_keywords=["nguyễn nhật ánh"],
        description="Tìm tác phẩm của tác giả đương đại",
    ),
    TestQuery(
        query_id="A002",
        query="Sách của Nam Cao trước cách mạng",
        query_type="AUTHOR",
        relevant_keywords=["nam cao"],
        description="Tác giả hiện thực phê phán",
    ),
    TestQuery(
        query_id="A003",
        query="Tô Hoài viết những tác phẩm gì",
        query_type="AUTHOR",
        relevant_keywords=["tô hoài"],
        description="Tác giả viết cho thiếu nhi",
    ),
    TestQuery(
        query_id="A004",
        query="Truyện của Nguyễn Huy Thiệp",
        query_type="AUTHOR",
        relevant_keywords=["nguyễn huy thiệp"],
        description="Nhà văn đổi mới",
    ),
    TestQuery(
        query_id="A005",
        query="Các tiểu thuyết của Hồ Biểu Chánh",
        query_type="AUTHOR",
        relevant_keywords=["hồ biểu chánh"],
        description="Nhà văn Nam Bộ đầu thế kỷ 20",
    ),
    TestQuery(
        query_id="A006",
        query="Thơ Xuân Diệu tình yêu lãng mạn",
        query_type="AUTHOR",
        relevant_keywords=["xuân diệu"],
        description="Nhà thơ lãng mạn",
    ),
    TestQuery(
        query_id="A007",
        query="Bảo Ninh Nỗi buồn chiến tranh",
        query_type="AUTHOR",
        relevant_keywords=["bảo ninh", "nỗi buồn chiến tranh"],
        description="Văn học chiến tranh hậu chiến",
    ),

    # ── SEMANTIC ──
    TestQuery(
        query_id="S001",
        query="Truyện ngắn về cuộc sống người nông dân Việt Nam nghèo khổ",
        query_type="SEMANTIC",
        relevant_keywords=["nông dân", "nghèo", "làng quê"],
        description="Tìm theo chủ đề xã hội",
    ),
    TestQuery(
        query_id="S002",
        query="Sách thiếu nhi văn học Việt Nam dành cho trẻ em",
        query_type="SEMANTIC",
        relevant_keywords=["thiếu nhi", "trẻ em"],
        description="Thể loại thiếu nhi",
    ),
    TestQuery(
        query_id="S003",
        query="Tiểu thuyết lịch sử Việt Nam thời kỳ phong kiến",
        query_type="SEMANTIC",
        relevant_keywords=["lịch sử", "phong kiến", "triều đình"],
        description="Văn học lịch sử",
    ),
    TestQuery(
        query_id="S004",
        query="Thơ tình yêu đôi lứa lãng mạn",
        query_type="SEMANTIC",
        relevant_keywords=["tình yêu", "tình cảm", "lãng mạn"],
        description="Chủ đề tình yêu",
    ),
    TestQuery(
        query_id="S005",
        query="Văn học chiến tranh kháng chiến chống Mỹ",
        query_type="SEMANTIC",
        relevant_keywords=["chiến tranh", "kháng chiến", "chống Mỹ"],
        description="Văn học chiến tranh",
    ),
    TestQuery(
        query_id="S006",
        query="Truyện cổ tích dân gian Việt Nam",
        query_type="SEMANTIC",
        relevant_keywords=["cổ tích", "dân gian", "truyền thuyết"],
        description="Văn học dân gian",
    ),
    TestQuery(
        query_id="S007",
        query="Tiểu thuyết kiếm hiệp võ thuật",
        query_type="SEMANTIC",
        relevant_keywords=["kiếm hiệp", "võ thuật", "giang hồ"],
        description="Thể loại kiếm hiệp",
    ),
    TestQuery(
        query_id="S008",
        query="Hồi ký tự truyện nhà văn Việt Nam",
        query_type="SEMANTIC",
        relevant_keywords=["hồi ký", "tự truyện", "ký ức"],
        description="Thể loại hồi ký",
    ),
    TestQuery(
        query_id="S009",
        query="Truyện dài về gia đình và tình thân",
        query_type="SEMANTIC",
        relevant_keywords=["gia đình", "tình thân", "cha mẹ"],
        description="Chủ đề gia đình",
    ),
    TestQuery(
        query_id="S010",
        query="Sách văn học đương đại Việt Nam sau đổi mới",
        query_type="SEMANTIC",
        relevant_keywords=["đổi mới", "đương đại", "hiện đại"],
        description="Văn học đương đại",
    ),

    # ── SEMANTIC (kịch bản khó) ──
    TestQuery(
        query_id="S011",
        query="Tôi muốn đọc sách buồn về nỗi cô đơn và sự mất mát",
        query_type="SEMANTIC",
        relevant_keywords=["cô đơn", "mất mát", "buồn", "tâm trạng"],
        description="Query cảm xúc — semantic khó",
    ),
    TestQuery(
        query_id="S012",
        query="Câu chuyện về người phụ nữ bị xã hội áp bức và phân biệt đối xử",
        query_type="SEMANTIC",
        relevant_keywords=["phụ nữ", "áp bức", "bất công", "số phận"],
        description="Query ẩn dụ xã hội",
    ),
    TestQuery(
        query_id="S013",
        query="Văn học Việt Nam giai đoạn 1930 đến 1945 trước cách mạng",
        query_type="SEMANTIC",
        relevant_keywords=["1930", "1945", "tiền chiến", "thực dân"],
        description="Query theo giai đoạn lịch sử văn học",
    ),
    TestQuery(
        query_id="S014",
        query="Tiểu thuyết có yếu tố tâm linh ma quỷ và huyền bí",
        query_type="SEMANTIC",
        relevant_keywords=["tâm linh", "ma", "huyền bí", "kỳ ảo"],
        description="Thể loại kỳ ảo / huyền bí",
    ),

    # ── FACTUAL (phức tạp) ──
    TestQuery(
        query_id="F006",
        query="Ai là tác giả của tập thơ Từ ấy",
        query_type="FACTUAL",
        relevant_keywords=["từ ấy", "tố hữu"],
        description="Tập thơ cách mạng",
    ),
    TestQuery(
        query_id="F007",
        query="Vợ nhặt là truyện ngắn của Kim Lân",
        query_type="FACTUAL",
        relevant_keywords=["vợ nhặt", "kim lân"],
        description="Truyện ngắn nổi tiếng",
    ),

    # ── AUTHOR (thêm) ──
    TestQuery(
        query_id="A008",
        query="Sáng tác của Thạch Lam về cuộc sống bình dị",
        query_type="AUTHOR",
        relevant_keywords=["thạch lam"],
        description="Nhà văn Tự lực văn đoàn",
    ),
    TestQuery(
        query_id="A009",
        query="Truyện ngắn của Nguyễn Công Hoan châm biếm xã hội",
        query_type="AUTHOR",
        relevant_keywords=["nguyễn công hoan"],
        description="Nhà văn hiện thực châm biếm",
    ),
]


def get_queries_by_type(query_type: str) -> List[TestQuery]:
    """Lọc queries theo type."""
    return [q for q in TEST_QUERIES if q.query_type == query_type]


def get_all_queries() -> List[TestQuery]:
    return TEST_QUERIES
