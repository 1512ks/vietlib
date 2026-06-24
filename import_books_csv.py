"""
import_books_csv.py -- PHA 3: Nhập metadata đã làm giàu (CSV) ngược vào file JSON gốc.

Đọc data/books_metadata_enriched.csv, với mỗi dòng cập nhật các file JSON liệt kê ở
cột `source_paths`. Nguyên tắc: CHỈ điền trường đang TRỐNG trong JSON (fill-empty),
không đè dữ liệu sẵn có.

Mặc định CHẠY THỬ (dry-run) — chỉ in thay đổi, KHÔNG ghi. Phải thêm --apply để ghi thật.

    .venv/Scripts/python.exe -X utf8 import_books_csv.py            # xem trước
    .venv/Scripts/python.exe -X utf8 import_books_csv.py --apply    # ghi thật
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IN_CSV = "data/books_metadata_enriched.csv"
# Cột CSV -> khoá JSON (trùng tên, viết tường minh cho rõ)
FIELD_MAP = {
    "author": "author", "publication_year": "publication_year", "genre": "genre",
    "publisher": "publisher", "page_count": "page_count", "isbn": "isbn",
    "cover_url": "cover_url",
}


def is_empty(v) -> bool:
    return v in (None, "", [], 0, "0") or (isinstance(v, str) and not v.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=IN_CSV)
    ap.add_argument("--apply", action="store_true", help="Ghi thật (mặc định chỉ dry-run)")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not Path(args.inp).exists():
        print(f"❌ Chưa có {args.inp}. Hãy chạy Pha 2 (enrich) trước.")
        return

    rows = list(csv.DictReader(open(args.inp, encoding="utf-8-sig")))
    mode = "GHI THẬT" if args.apply else "DRY-RUN (không ghi)"
    print("=" * 60)
    print(f"  PHA 3 — IMPORT NGƯỢC VÀO JSON  [{mode}]")
    print("=" * 60)

    files_touched = 0
    fields_written = 0
    field_counter = {k: 0 for k in FIELD_MAP}
    rows_processed = 0

    for row in rows:
        # Chỉ xử lý dòng AI có điền gì đó
        enriched_vals = {csv_k: (row.get(csv_k) or "").strip()
                         for csv_k in FIELD_MAP if (row.get(csv_k) or "").strip()}
        if not enriched_vals:
            continue
        rows_processed += 1

        for path_str in (row.get("source_paths") or "").split(";"):
            path_str = path_str.strip()
            if not path_str:
                continue
            p = Path(path_str)
            if not p.exists():
                continue
            try:
                data = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue

            changed = []
            for csv_k, val in enriched_vals.items():
                jkey = FIELD_MAP[csv_k]
                if is_empty(data.get(jkey)):
                    if args.apply:
                        data[jkey] = val
                    changed.append(jkey)
                    field_counter[csv_k] += 1
                    fields_written += 1

            if changed:
                files_touched += 1
                if args.apply:
                    json.dump(data, open(p, "w", encoding="utf-8"),
                              ensure_ascii=False, indent=2)
                if files_touched <= 15:   # in vài ví dụ đầu
                    print(f"  {p.name}: +{changed}")

        if args.limit and rows_processed >= args.limit:
            break

    print("\n  ── TỔNG KẾT ──")
    print(f"    Dòng có dữ liệu làm giàu : {rows_processed:,}")
    print(f"    File JSON sẽ cập nhật    : {files_touched:,}")
    print(f"    Tổng trường ghi          : {fields_written:,}")
    for k, c in field_counter.items():
        if c:
            print(f"      · {k:18s}: {c:,}")
    if not args.apply:
        print("\n  ⚠️  Đây là DRY-RUN. Thêm --apply để ghi thật (nên `git status` kiểm tra sau đó).")


if __name__ == "__main__":
    main()
