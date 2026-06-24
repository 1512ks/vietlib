"""
audit_coverage.py -- Kiểm toán độ phủ & chất lượng metadata của knowledge base.

Mục tiêu:
  1. Đối chiếu DANH SÁCH KINH ĐIỂN (parse trực tiếp từ SYSTEM_PROMPT trong
     retrieval_qa.py) với DB thật (data/bm25_index.pkl) -> tác phẩm nào CÓ / THIẾU.
  2. Với tác phẩm CÓ: kiểm tra metadata (tác giả rỗng? có năm? tóm tắt cụt?).
  3. Thống kê độ đầy đủ trường thông tin TOÀN DB -> scope việc enrichment.

Chạy:
    .venv/Scripts/python.exe -X utf8 audit_coverage.py
    .venv/Scripts/python.exe -X utf8 audit_coverage.py --json data/coverage_audit.json

Không gọi API, không cần mạng — chỉ đọc file local.
"""
from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BM25_PATH = Path("data/bm25_index.pkl")
RETRIEVAL_QA = Path("retrieval_qa.py")

# Ngưỡng coi tóm tắt là "cụt/rác" — phần "Nội dung chi tiết" dưới mức này là thiếu nội dung
JUNK_SUMMARY_CHARS = 200


# ------------------------------------------------------------------
#  Chuẩn hoá & so khớp tiêu đề
# ------------------------------------------------------------------
def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def norm(s: str) -> str:
    """Chuẩn hoá để so khớp: bỏ dấu, lowercase, gọn khoảng trắng, bỏ ký tự lạ."""
    s = strip_accents(s or "").lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ------------------------------------------------------------------
#  Parse danh sách kinh điển từ SYSTEM_PROMPT
# ------------------------------------------------------------------
def parse_canon_vn() -> list[tuple[str, str]]:
    """
    Trích (title, author) từ khối canon Việt Nam trong SYSTEM_PROMPT.
    Chỉ lấy phần TRƯỚC mục 'Văn học Thế giới' để tập trung văn học VN.
    Định dạng nguồn: 'Tên tác phẩm (Tác giả), Tên khác (Tác giả 2), ...'
    """
    text = RETRIEVAL_QA.read_text(encoding="utf-8")
    # Lấy khối từ "Danh sách tác phẩm kinh điển Văn học Việt Nam" tới "Văn học Thế giới"
    m = re.search(
        r"kinh điển Văn học Việt Nam(.*?)kinh điển Văn học Thế giới",
        text, re.DOTALL,
    )
    block = m.group(1) if m else ""
    # Bỏ các dòng tiêu đề in đậm "**...**"
    block = re.sub(r"\*\*[^*]+\*\*", " ", block)
    # Bắt cặp 'Tên (Tác giả)' — tên không chứa dấu phẩy/ngoặc; tác giả trong ngoặc
    pairs = []
    seen = set()
    for mm in re.finditer(r"([^,()\n]+?)\s*\(([^)]+)\)", block):
        title = mm.group(1).strip(" .,\n")
        author = mm.group(2).strip()
        # Tác giả có thể có ghi chú 'dịch', '/', '&' — lấy tên đầu cho hiển thị
        if not title or len(title) < 2:
            continue
        k = norm(title)
        if k in seen:
            continue
        seen.add(k)
        pairs.append((title, author))
    return pairs


# ------------------------------------------------------------------
#  Tải DB & dựng chỉ mục so khớp
# ------------------------------------------------------------------
def load_db():
    d = pickle.load(open(BM25_PATH, "rb"))
    titles = []
    for m in d["metadatas"]:
        titles.append((m.get("title") or m.get("name") or "").strip())
    return d["texts"], d["metadatas"], titles


def build_title_index(titles: list[str]) -> dict[str, list[int]]:
    idx: dict[str, list[int]] = {}
    for i, t in enumerate(titles):
        idx.setdefault(norm(t), []).append(i)
    return idx


def find_match(canon_title: str, norm_idx: dict[str, list[int]],
               norm_titles: list[str]) -> int | None:
    """Khớp chính xác (sau chuẩn hoá) trước; nếu không, khớp 'chứa trọn'."""
    nt = norm(canon_title)
    if nt in norm_idx:
        return norm_idx[nt][0]
    # Khớp chứa: tiêu đề DB chứa trọn tên canon (hoặc ngược lại) với độ dài đủ
    if len(nt) >= 4:
        for i, dbt in enumerate(norm_titles):
            if not dbt:
                continue
            if nt == dbt or (f" {nt} " in f" {dbt} ") or (f" {dbt} " in f" {nt} "):
                return i
    return None


# ------------------------------------------------------------------
#  Đánh giá chất lượng 1 entry
# ------------------------------------------------------------------
def summary_part(text: str) -> str:
    """Lấy phần 'Nội dung chi tiết' (sau metadata injection) để đo độ dài thực."""
    m = re.search(r"Nội dung chi tiết:\s*(.*)", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


def has_year(text: str) -> bool:
    return bool(re.search(r"\[Năm xuất bản:\s*\S", text)) or bool(
        re.search(r"\b(1[5-9]\d\d|20[0-2]\d)\b", text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None, help="Ghi báo cáo chi tiết ra file JSON")
    args = ap.parse_args()

    if not BM25_PATH.exists():
        print(f"❌ Không thấy {BM25_PATH}. Hãy build knowledge base trước.")
        return

    texts, metas, titles = load_db()
    norm_titles = [norm(t) for t in titles]
    norm_idx = build_title_index(titles)
    canon = parse_canon_vn()

    print("=" * 64)
    print("  AUDIT ĐỘ PHỦ & CHẤT LƯỢNG KNOWLEDGE BASE")
    print("=" * 64)
    print(f"  Tổng entry trong DB        : {len(titles):,}")
    print(f"  Tác phẩm kinh điển VN (canon): {len(canon)}")
    print()

    # ---- 1. Đối chiếu canon ----
    present, missing, thin = [], [], []
    for title, author in canon:
        i = find_match(title, norm_idx, norm_titles)
        if i is None:
            missing.append((title, author))
            continue
        s = summary_part(texts[i])
        db_author = (metas[i].get("author") or "").strip()
        row = {
            "canon_title": title, "canon_author": author,
            "db_title": titles[i], "db_author": db_author,
            "summary_chars": len(s),
            "missing_author": not db_author,
            "missing_year": not has_year(texts[i]),
            "junk_summary": len(s) < JUNK_SUMMARY_CHARS,
        }
        present.append(row)
        if row["junk_summary"] or row["missing_author"] or row["missing_year"]:
            thin.append(row)

    cov = len(present) / len(canon) * 100 if canon else 0
    print("─" * 64)
    print(f"  [1] ĐỘ PHỦ CANON: {len(present)}/{len(canon)} có mặt ({cov:.0f}%) | "
          f"thiếu {len(missing)} | có-nhưng-thiếu-field {len(thin)}")
    print("─" * 64)

    if missing:
        print(f"\n  ❌ THIẾU HẲN ({len(missing)}):")
        for t, a in missing:
            print(f"     · {t} — {a}")

    if thin:
        print(f"\n  ⚠️  CÓ NHƯNG THIẾU TRƯỜNG ({len(thin)}):")
        for r in thin:
            flags = []
            if r["junk_summary"]: flags.append(f"tóm tắt cụt({r['summary_chars']}c)")
            if r["missing_author"]: flags.append("thiếu tác giả")
            if r["missing_year"]: flags.append("thiếu năm")
            print(f"     · {r['canon_title']:32.32s} | {', '.join(flags)}")

    # ---- 2. Thống kê toàn DB (scope enrichment) ----
    empty_author = sum(1 for m in metas if not (m.get("author") or "").strip())
    no_year = sum(1 for t in texts if not has_year(t))
    junk_sum = sum(1 for t in texts if len(summary_part(t)) < JUNK_SUMMARY_CHARS)
    n = len(texts)
    print()
    print("─" * 64)
    print("  [2] ĐỘ ĐẦY ĐỦ TRƯỜNG — TOÀN DB (scope enrichment web-search)")
    print("─" * 64)
    print(f"     Thiếu tác giả   : {empty_author:6,} / {n:,} ({empty_author/n*100:.0f}%)")
    print(f"     Thiếu năm       : {no_year:6,} / {n:,} ({no_year/n*100:.0f}%)")
    print(f"     Tóm tắt cụt(<{JUNK_SUMMARY_CHARS}c): {junk_sum:6,} / {n:,} ({junk_sum/n*100:.0f}%)")

    # Phân bố theo nguồn
    src = Counter((m.get("source") or "?") for m in metas)
    print("\n     Phân bố theo nguồn:")
    for s, c in src.most_common():
        print(f"        {s:30.30s}: {c:6,}")

    if args.json:
        out = {
            "db_total": n,
            "canon_total": len(canon),
            "present": present,
            "missing": [{"title": t, "author": a} for t, a in missing],
            "db_field_completeness": {
                "empty_author": empty_author, "no_year": no_year,
                "junk_summary": junk_sum,
            },
        }
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(out, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
        print(f"\n  💾 Đã ghi báo cáo chi tiết: {args.json}")


if __name__ == "__main__":
    main()
