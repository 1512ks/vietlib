"""
report_stats.py -- Sinh số liệu thống kê cho báo cáo từ books_metadata_enriched.csv.

Chạy SAU khi enrich xong (hoặc giữa chừng để xem tạm). In ra:
  1. Fill-rate từng trường: TRƯỚC làm giàu  ->  SAU làm giàu (và số dòng AI bổ sung).
  2. Phân bố thể loại trên TOÀN corpus (không chỉ vnthuquan).
  3. Bảng LaTeX dán thẳng vào báo cáo (mục 3.x fill-rate và tab:genre-dist).

Cách dùng:
    .venv/Scripts/python.exe -X utf8 report_stats.py
    .venv/Scripts/python.exe -X utf8 report_stats.py --in data/books_metadata_enriched.csv --top 10

"Trước làm giàu" được suy ra từ cột ai_filled: trường đang có giá trị mà KHÔNG nằm
trong ai_filled => vốn đã có từ nguồn gốc; ngược lại là do AI bổ sung.
"""
from __future__ import annotations

import argparse
import collections
import csv
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIELDS = ["author", "publication_year", "genre", "publisher", "page_count", "summary"]
LABEL = {
    "author": "Tác giả (author)", "publication_year": "Năm xuất bản (publication\\_year)",
    "genre": "Thể loại (genre)", "publisher": "Nhà xuất bản (publisher)",
    "page_count": "Số trang (page\\_count)", "summary": "Tóm tắt (summary)",
}
SUMMARY_MIN = 50


def is_filled(v: str, field: str) -> bool:
    v = (v or "").strip()
    return len(v) >= SUMMARY_MIN if field == "summary" else bool(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/books_metadata_enriched.csv")
    ap.add_argument("--top", type=int, default=10, help="Số thể loại hàng đầu liệt kê")
    args = ap.parse_args()

    try:
        rows = list(csv.DictReader(open(args.inp, encoding="utf-8-sig")))
    except FileNotFoundError:
        print(f"❌ Chưa thấy {args.inp}. Hãy chạy enrich (Pha 2) trước.")
        return
    n = len(rows)
    if n == 0:
        print("File rỗng.")
        return

    works = [r for r in rows if (r.get("entity_type") or "work") == "work"]
    authors_n = n - len(works)

    # ── Fill-rate: trước -> sau ──
    after = {f: 0 for f in FIELDS}
    ai_add = {f: 0 for f in FIELDS}
    for r in rows:
        aifilled = set((r.get("ai_filled") or "").split(","))
        for f in FIELDS:
            if is_filled(r.get(f, ""), f):
                after[f] += 1
                if f in aifilled:
                    ai_add[f] += 1
    before = {f: after[f] - ai_add[f] for f in FIELDS}

    print("=" * 68)
    print("  THỐNG KÊ CHO BÁO CÁO")
    print("=" * 68)
    print(f"  Tổng dòng trong file enriched : {n:,}"
          + ("" if n >= 13576 else f"  ⚠️ (< 13.576 — enrich CHƯA xong, số liệu tạm thời)"))
    print(f"  Trong đó: work = {len(works):,} | author = {authors_n:,}\n")

    print(f"  {'Trường':<22}{'Trước':>12}{'Sau':>12}{'AI bổ sung':>14}")
    print("  " + "-" * 58)
    for f in FIELDS:
        b, a, ai = before[f], after[f], ai_add[f]
        print(f"  {f:<22}{b/n*100:>10.1f}%{a/n*100:>11.1f}%{ai:>12,}")

    # ── Phân bố thể loại (toàn corpus, trên work) ──
    g = collections.Counter()
    have_genre = 0
    for r in works:
        gv = (r.get("genre") or "").strip()
        if gv:
            have_genre += 1
            g[gv] += 1
    cov = have_genre / len(works) * 100 if works else 0
    print(f"\n  Độ phủ thể loại (trên {len(works):,} tác phẩm): {have_genre:,} ({cov:.1f}%)")
    print(f"  Top {args.top} thể loại:")
    for name, c in g.most_common(args.top):
        print(f"     {c:>6,}  {name}")

    # ── LaTeX sẵn để dán (định dạng số kiểu VN: thập phân dấu phẩy, nghìn dấu chấm) ──
    def pct(x: float) -> str:
        return f"{x:.1f}".replace(".", "{,}")        # 82.1 -> 82{,}1

    def num(x: int) -> str:
        return f"{x:,}".replace(",", ".")            # 1234 -> 1.234

    print("\n" + "=" * 68)
    print("  LATEX — DÁN THẲNG VÀO BÁO CÁO")
    print("=" * 68)
    print(r"""
\begin{table}[H]
\centering
\caption{Tỷ lệ điền đầy siêu dữ liệu trước và sau bước làm giàu bằng AI}
\label{tab:fillrate}
\renewcommand{\arraystretch}{1.3}
\begin{tabular}{p{4.8cm} r r r}
\toprule
\textbf{Trường} & \textbf{Trước} & \textbf{Sau} & \textbf{AI bổ sung (dòng)} \\
\midrule""")
    for f in FIELDS:
        print(f"{LABEL[f]} & ${pct(before[f]/n*100)}\\%$ & ${pct(after[f]/n*100)}\\%$ & {num(ai_add[f])} \\\\")
    print(r"""\bottomrule
\end{tabular}
\end{table}""")

    print(r"""
\begin{table}[H]
\centering
\caption{Các thể loại phổ biến nhất trên toàn bộ corpus (nhãn do AI sinh/bổ sung)}
\label{tab:genre-dist}
\renewcommand{\arraystretch}{1.3}
\begin{tabular}{l r}
\toprule
\textbf{Thể loại} & \textbf{Số tác phẩm} \\
\midrule""")
    for name, c in g.most_common(args.top):
        safe = name.replace("&", "\\&")
        print(f"{safe} & {num(c)} \\\\")
    print(r"""\bottomrule
\end{tabular}
\end{table}""")


if __name__ == "__main__":
    main()
