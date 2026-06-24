"""
export_books_csv.py -- PHA 1: Xuất toàn bộ sách ra CSV chuẩn hoá (để enrich bằng AI).

Quét data/processed/{work, gbooks, archive_compact}, gộp các bản ghi trùng theo
khoá (title, author) — GIỐNG hệt logic build_knowledge_base.py — rồi xuất ra
data/books_metadata_raw.csv. Cột `source_paths` giữ đường dẫn mọi file gốc để Pha 3
import ngược lại.

Chạy:
    .venv/Scripts/python.exe -X utf8 export_books_csv.py
    .venv/Scripts/python.exe -X utf8 export_books_csv.py --out data/books_metadata_raw.csv

Không gọi API, không cần mạng.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = Path("data/processed")
INCLUDE_SUBDIRS = ["work", "gbooks", "archive_compact"]   # sách (bỏ author/concept)

# Thứ tự cột CSV (khớp schema trong database_plan.md)
COLUMNS = [
    "id", "title", "entity_type", "author", "publication_year", "genre", "publisher",
    "page_count", "isbn", "cover_url", "summary", "source", "source_paths",
]

# Dấu hiệu trang là NGƯỜI (tác giả) chứ không phải tác phẩm → để Pha 2 bỏ qua
_PERSON_CAT = ("nhà văn", "nhà thơ", "nhà viết kịch", "nhà soạn kịch", "tác giả",
               "nhà báo", "dịch giả")
_PERSON_SUMMARY = ("là nhà ", "là một nhà ", "là nhà thơ", "là nhà văn", "là cố nhà")


def classify_entity(data: dict) -> str:
    """'author' nếu trang nói về một con người; ngược lại 'work'."""
    cats = " ".join(data.get("categories", []) or []).lower()
    summ = (data.get("summary", "") or "")[:160].lower()
    if any(k in cats for k in _PERSON_CAT) or any(k in summ for k in _PERSON_SUMMARY):
        return "author"
    return "work"
# Các cột tính fill-rate (source/source_paths/id luôn có nên bỏ qua)
FILLABLE = ["author", "publication_year", "genre", "publisher",
            "page_count", "isbn", "cover_url", "summary"]
SUMMARY_MIN = 50   # summary ngắn hơn mức này coi như "trống" khi tính fill-rate


def _first(*vals) -> str:
    """Trả giá trị chuỗi không rỗng đầu tiên."""
    for v in vals:
        if isinstance(v, list):
            v = v[0] if v else ""
        if v not in (None, "", []):
            return str(v).strip()
    return ""


def detect_source(path: Path, data: dict) -> str:
    p = path.parent.name
    if "archive" in p:
        return "archive_compact"
    if "gbooks" in p:
        return "gbooks"
    if "work" in p:
        return "wikipedia"
    return data.get("source", "unknown")


def collect() -> dict:
    """Gộp tất cả file JSON theo khoá (title|author) -> dict bản ghi hợp nhất."""
    files = []
    for sub in INCLUDE_SUBDIRS:
        d = DATA_DIR / sub
        if d.exists():
            found = [f for f in d.glob("*.json") if "meta" not in f.name]
            files.extend(found)
            print(f"  {sub:18s}: {len(found):6,} files")
        else:
            print(f"  {sub:18s}: MISSING")

    merged: dict = {}
    for f in files:
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        title = _first(data.get("title"), data.get("name"))
        if not title:
            continue
        author = _first(data.get("author"), data.get("authors"))
        key = f"{title.lower()} | {author.lower()}"
        src = detect_source(f, data)

        rec = merged.setdefault(key, {
            "title": title, "author": author, "entity_type": "work",
            "publication_year": "", "genre": "",
            "publisher": "", "page_count": "", "isbn": "", "cover_url": "",
            "summary": "", "sources": set(), "paths": [],
        })
        rec["sources"].add(src)
        rec["paths"].append(str(f).replace("\\", "/"))
        # Trang người (từ work/) → đánh dấu author để Pha 2 bỏ qua
        if classify_entity(data) == "author":
            rec["entity_type"] = "author"

        # Điền field theo ưu tiên non-empty (gbooks giàu nhất; archive có ai_summary)
        if not rec["author"]:
            rec["author"] = author
        rec["publication_year"] = rec["publication_year"] or _first(data.get("publication_year"))
        rec["genre"]     = rec["genre"]     or _first(data.get("genre"), data.get("genres"))
        rec["publisher"] = rec["publisher"] or _first(data.get("publisher"))
        rec["isbn"]      = rec["isbn"]      or _first(data.get("isbn"), data.get("isbn_list"))
        rec["cover_url"] = rec["cover_url"] or _first(data.get("cover_url"))
        pc = data.get("page_count")
        if not rec["page_count"] and pc:
            rec["page_count"] = str(pc)
        # summary: ưu tiên cái dài hơn; ai_summary của archive cũng tính
        for cand in (data.get("summary"), data.get("ai_summary"), data.get("description")):
            cand = (cand or "").strip()
            if len(cand) > len(rec["summary"]):
                rec["summary"] = cand
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/books_metadata_raw.csv")
    args = ap.parse_args()

    print("=" * 60)
    print("  PHA 1 — EXPORT SÁCH RA CSV")
    print("=" * 60)
    merged = collect()
    print(f"\n  Gộp xong: {len(merged):,} đầu sách độc nhất.\n")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    fill = {c: 0 for c in FILLABLE}
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for rec in merged.values():
            row = {
                "id": str(uuid.uuid5(uuid.NAMESPACE_OID,
                                     f"{rec['title'].lower()} | {rec['author'].lower()}")),
                "title": rec["title"], "entity_type": rec["entity_type"],
                "author": rec["author"],
                "publication_year": rec["publication_year"], "genre": rec["genre"],
                "publisher": rec["publisher"], "page_count": rec["page_count"],
                "isbn": rec["isbn"], "cover_url": rec["cover_url"],
                "summary": rec["summary"],
                "source": ", ".join(sorted(rec["sources"])),
                "source_paths": ";".join(rec["paths"]),
            }
            w.writerow(row)
            n += 1
            for c in FILLABLE:
                v = row[c]
                if c == "summary":
                    if len(v) >= SUMMARY_MIN:
                        fill[c] += 1
                elif v:
                    fill[c] += 1

    print(f"  💾 Đã ghi {n:,} dòng → {out}\n")
    print("  ── FILL-RATE (tỉ lệ ô có dữ liệu) ──")
    for c in FILLABLE:
        pct = fill[c] / n * 100 if n else 0
        bar = "█" * int(pct / 5)
        print(f"    {c:18s}: {fill[c]:6,}/{n:,} ({pct:5.1f}%) {bar}")
    print(f"\n  → Ô trống/cụt sẽ được Pha 2 (Gemini) làm giàu. Cột source_paths giữ {n:,} mapping để Pha 3 import ngược.")


if __name__ == "__main__":
    main()
