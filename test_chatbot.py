"""
test_chatbot.py -- Batch kiểm thử Chatbot RAG với 15 kịch bản.

Kịch bản kiểm thử:
    - FACTUAL  : Câu hỏi tác giả, tên sách cụ thể
    - AUTHOR   : Tìm tác phẩm theo tác giả
    - SEMANTIC : Tìm theo chủ đề, cảm xúc, ẩn dụ
    - HARD     : Hỏi về sách không có trong corpus (kiểm tra hallucination)

Metrics tự động:
    - has_citation   : Câu trả lời có trích dẫn nguồn không
    - answer_len     : Độ dài câu trả lời (số từ)
    - is_fallback    : Chatbot trả lời "không tìm thấy" (cho HARD queries)
    - latency_ms     : Thời gian phản hồi toàn bộ

Cách chạy:
    python test_chatbot.py                     # Full test (15 queries)
    python test_chatbot.py --type FACTUAL      # Chỉ test FACTUAL
    python test_chatbot.py --no-rerank         # Không dùng reranker
    python test_chatbot.py --save              # Lưu kết quả ra JSON
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

# Ensure project root in path
sys.path.insert(0, str(Path(__file__).parent))

# Fix Unicode encoding trên Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
#  Test Cases
# ============================================================
@dataclass
class TestCase:
    case_id: str
    query: str
    case_type: str          # FACTUAL | AUTHOR | SEMANTIC | HARD
    expect_keywords: List[str]  # Kỳ vọng có những từ này trong câu trả lời
    expect_fallback: bool = False   # True = kỳ vọng chatbot nói "không tìm thấy"
    description: str = ""


TEST_CASES: List[TestCase] = [
    # ── FACTUAL ──────────────────────────────────────────────
    TestCase(
        case_id="TC_F01",
        query="Tóm tắt truyện Chí Phèo của Nam Cao",
        case_type="FACTUAL",
        expect_keywords=["chí phèo", "nam cao"],
        description="Tóm tắt tác phẩm nổi tiếng",
    ),
    TestCase(
        case_id="TC_F02",
        query="Số đỏ của Vũ Trọng Phụng viết về điều gì",
        case_type="FACTUAL",
        expect_keywords=["số đỏ", "vũ trọng phụng"],
        description="Nội dung tác phẩm cụ thể",
    ),
    TestCase(
        case_id="TC_F03",
        query="Tắt đèn của Ngô Tất Tố nói về cuộc sống của ai",
        case_type="FACTUAL",
        expect_keywords=["tắt đèn", "ngô tất tố"],
        description="Nhân vật chính trong tác phẩm",
    ),
    TestCase(
        case_id="TC_F04",
        query="Nỗi buồn chiến tranh của Bảo Ninh ra đời năm nào",
        case_type="FACTUAL",
        expect_keywords=["bảo ninh", "chiến tranh"],
        description="Câu hỏi về năm xuất bản",
    ),

    # ── AUTHOR ───────────────────────────────────────────────
    TestCase(
        case_id="TC_A01",
        query="Nguyễn Nhật Ánh đã viết những tác phẩm nổi tiếng nào",
        case_type="AUTHOR",
        expect_keywords=["nguyễn nhật ánh"],
        description="Liệt kê tác phẩm theo tác giả",
    ),
    TestCase(
        case_id="TC_A02",
        query="Nam Cao có những truyện ngắn nào về người nông dân",
        case_type="AUTHOR",
        expect_keywords=["nam cao"],
        description="Tác phẩm theo chủ đề của tác giả",
    ),
    TestCase(
        case_id="TC_A03",
        query="Tô Hoài nổi tiếng với tác phẩm nào dành cho thiếu nhi",
        case_type="AUTHOR",
        expect_keywords=["tô hoài"],
        description="Tác giả thiếu nhi",
    ),

    # ── SEMANTIC CƠ BẢN ──────────────────────────────────────
    TestCase(
        case_id="TC_S01",
        query="Gợi ý sách về cuộc sống người nông dân nghèo khổ Việt Nam",
        case_type="SEMANTIC",
        expect_keywords=["nông dân"],
        description="Tư vấn sách theo chủ đề",
    ),
    TestCase(
        case_id="TC_S02",
        query="Tôi muốn tìm sách văn học thiếu nhi Việt Nam hay",
        case_type="SEMANTIC",
        expect_keywords=["thiếu nhi"],
        description="Gợi ý sách thiếu nhi",
    ),
    TestCase(
        case_id="TC_S03",
        query="Sách nào hay về chủ đề chiến tranh kháng chiến chống Mỹ",
        case_type="SEMANTIC",
        expect_keywords=["chiến tranh", "kháng chiến"],
        description="Gợi ý sách chiến tranh",
    ),

    # ── SEMANTIC KHÓ (cảm xúc / ẩn dụ) ─────────────────────
    TestCase(
        case_id="TC_H01",
        query="Tôi đang rất buồn và muốn đọc một cuốn sách về nỗi cô đơn và hy vọng",
        case_type="SEMANTIC",
        expect_keywords=["sách", "tác phẩm"],
        description="Query theo cảm xúc — kỳ vọng chatbot diễn giải nhu cầu",
    ),
    TestCase(
        case_id="TC_H02",
        query="Câu chuyện về người phụ nữ bị xã hội chà đạp số phận bi thảm",
        case_type="SEMANTIC",
        expect_keywords=["phụ nữ", "số phận"],
        description="Query ẩn dụ xã hội",
    ),
    TestCase(
        case_id="TC_H03",
        query="Văn học Việt Nam thời tiền chiến 1930-1945 có những dòng chảy nào",
        case_type="SEMANTIC",
        expect_keywords=["văn học"],
        description="Query học thuật về giai đoạn văn học",
    ),

    # ── HARD (kiểm tra hallucination) ────────────────────────
    TestCase(
        case_id="TC_HARD01",
        query="Tóm tắt cốt truyện bộ truyện tranh Naruto bản tiếng Việt",
        case_type="HARD",
        expect_keywords=[],
        expect_fallback=True,
        description="Truyện tranh không có trong corpus — kỳ vọng fallback",
    ),
    TestCase(
        case_id="TC_HARD02",
        query="Cho tôi biết nội dung manga One Piece tiếng Việt",
        case_type="HARD",
        expect_keywords=[],
        expect_fallback=True,
        description="Nội dung hoàn toàn ngoài corpus — kiểm tra không hallucinate",
    ),
]


# ============================================================
#  Auto-check helpers
# ============================================================
CITATION_MARKERS = ["nguồn tham khảo", "📚", "[1]", "[2]", "— tác giả", "tài liệu"]
FALLBACK_MARKERS = [
    "không tìm thấy",
    "không đủ thông tin",
    "không có thông tin",
    "thư viện không",
    "thư viện hiện tập trung",
    "không tìm thấy thông tin về",
    "xin lỗi",
]


def has_citation(answer: str) -> bool:
    """Kiểm tra câu trả lời có trích dẫn nguồn không."""
    lower = answer.lower()
    return any(m in lower for m in CITATION_MARKERS)


def is_fallback(answer: str) -> bool:
    """Kiểm tra chatbot có báo không tìm thấy thông tin không."""
    lower = answer.lower()
    return any(m in lower for m in FALLBACK_MARKERS)


def has_expected_keywords(answer: str, keywords: List[str]) -> bool:
    """Kiểm tra câu trả lời có chứa ít nhất 1 keyword kỳ vọng."""
    if not keywords:
        return True
    lower = answer.lower()
    return any(kw.lower() in lower for kw in keywords)


# ============================================================
#  Result dataclass
# ============================================================
@dataclass
class TestResult:
    case_id: str
    case_type: str
    query: str
    description: str
    answer: str
    answer_len_words: int
    has_citation: bool
    has_keywords: bool
    is_fallback: bool
    expect_fallback: bool
    passed: bool
    latency_ms: int
    contexts_used: int


# ============================================================
#  Runner
# ============================================================
def run_tests(
    qa,
    test_cases: List[TestCase],
    mode: str = "hybrid",
) -> List[TestResult]:
    results = []

    for i, tc in enumerate(test_cases, 1):
        print(f"\n[{i:02d}/{len(test_cases)}] {tc.case_id} — {tc.description[:50]}")
        print(f"  ❓ {tc.query[:80]}")

        t0 = time.time()
        try:
            result = qa.ask(tc.query, mode=mode)
            answer = result["answer"]
            latency = result["latency"]["total_ms"]
            contexts_used = len(result.get("contexts", []))
        except Exception as e:
            print(f"  ❌ Lỗi: {e}")
            answer = f"[ERROR: {e}]"
            latency = int((time.time() - t0) * 1000)
            contexts_used = 0

        # Auto-check
        citation_ok   = has_citation(answer)
        keywords_ok   = has_expected_keywords(answer, tc.expect_keywords)
        fallback_ok   = is_fallback(answer)
        word_count    = len(answer.split())

        # Pass criteria:
        # - HARD queries: fallback phải đúng (không hallucinate)
        # - Khác: có keywords + có citation
        if tc.expect_fallback:
            passed = fallback_ok
        else:
            passed = keywords_ok and citation_ok

        status = "✅ PASS" if passed else "⚠️  FAIL"
        print(f"  {status} | citation={citation_ok} | keywords={keywords_ok} | "
              f"fallback={fallback_ok} | {word_count} từ | {latency}ms")
        print(f"  📝 {answer[:120].replace(chr(10), ' ')}…")

        results.append(TestResult(
            case_id=tc.case_id,
            case_type=tc.case_type,
            query=tc.query,
            description=tc.description,
            answer=answer,
            answer_len_words=word_count,
            has_citation=citation_ok,
            has_keywords=keywords_ok,
            is_fallback=fallback_ok,
            expect_fallback=tc.expect_fallback,
            passed=passed,
            latency_ms=latency,
            contexts_used=contexts_used,
        ))

    return results


# ============================================================
#  Print Summary
# ============================================================
def print_summary(results: List[TestResult]):
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    has_cit = sum(1 for r in results if r.has_citation)
    avg_latency = sum(r.latency_ms for r in results) / total if total else 0
    avg_words = sum(r.answer_len_words for r in results) / total if total else 0

    print(f"\n{'='*65}")
    print("  📊 KẾT QUẢ KIỂM THỬ CHATBOT — TỔNG HỢP")
    print(f"{'='*65}")
    print(f"  Tổng queries    : {total}")
    print(f"  PASS            : {passed}/{total}  ({passed/total*100:.1f}%)")
    print(f"  Có trích dẫn   : {has_cit}/{total}  ({has_cit/total*100:.1f}%)")
    print(f"  Avg latency     : {avg_latency:.0f}ms")
    print(f"  Avg độ dài      : {avg_words:.0f} từ")

    # Per-type breakdown
    print(f"\n  {'Type':<12} {'Pass':>6} {'Citation':>10} {'Avg(ms)':>10}")
    print(f"  {'-'*42}")
    for qtype in ["FACTUAL", "AUTHOR", "SEMANTIC", "HARD"]:
        subset = [r for r in results if r.case_type == qtype]
        if not subset:
            continue
        n = len(subset)
        p = sum(1 for r in subset if r.passed)
        c = sum(1 for r in subset if r.has_citation)
        lat = sum(r.latency_ms for r in subset) / n
        print(f"  {qtype:<12} {p:>3}/{n:<2}  {c:>3}/{n:<6}  {lat:>8.0f}ms")

    print()

    # Failed cases
    failed = [r for r in results if not r.passed]
    if failed:
        print(f"  ⚠️  Các trường hợp FAIL ({len(failed)}):")
        for r in failed:
            print(f"    [{r.case_id}] {r.description[:50]}")
            reason = []
            if not r.has_citation and not r.expect_fallback:
                reason.append("thiếu citation")
            if not r.has_keywords and not r.expect_fallback:
                reason.append("thiếu keywords")
            if r.expect_fallback and not r.is_fallback:
                reason.append("có thể hallucinate")
            print(f"            → {', '.join(reason) or 'Xem log chi tiết'}")
    print()


# ============================================================
#  Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Batch kiểm thử Chatbot RAG — 15 kịch bản"
    )
    parser.add_argument("--type", choices=["FACTUAL", "AUTHOR", "SEMANTIC", "HARD"],
                        default=None, help="Chỉ chạy test theo loại")
    parser.add_argument("--mode", choices=["hybrid", "bm25", "vector"],
                        default="hybrid", help="Chiến lược retrieval (default: hybrid)")
    parser.add_argument("--no-rerank", action="store_true",
                        help="Tắt Cross-Encoder reranking")
    parser.add_argument("--save", action="store_true",
                        help="Lưu kết quả ra JSON")
    parser.add_argument("--output-dir", default="data/chatbot_test_results",
                        help="Thư mục lưu kết quả")
    args = parser.parse_args()

    # Chọn test cases
    cases = TEST_CASES
    if args.type:
        cases = [tc for tc in TEST_CASES if tc.case_type == args.type]
    print(f"\n🔍 Kiểm thử {len(cases)} kịch bản (mode={args.mode}, "
          f"rerank={not args.no_rerank})\n")

    # Build QA engine
    from retrieval_qa import RetrievalQA
    use_reranker = not args.no_rerank and args.mode == "hybrid"
    qa = RetrievalQA.build(use_reranker=use_reranker)

    # Chạy tests
    t_start = time.time()
    results = run_tests(qa, cases, mode=args.mode)
    t_total = time.time() - t_start

    # Summary
    print_summary(results)
    print(f"  ⏱ Tổng thời gian: {t_total:.1f}s\n")

    # Save
    if args.save:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        out_path = output_dir / f"chatbot_test_{args.mode}_{timestamp}.json"
        data = {
            "timestamp": timestamp,
            "mode": args.mode,
            "use_reranker": use_reranker,
            "n_cases": len(results),
            "n_passed": sum(1 for r in results if r.passed),
            "results": [asdict(r) for r in results],
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 Kết quả lưu → {out_path}\n")


if __name__ == "__main__":
    main()
