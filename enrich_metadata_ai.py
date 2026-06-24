"""
enrich_metadata_ai.py -- PHA 2: Làm giàu metadata sách bằng Gemini + Google Search Grounding.

Đọc data/books_metadata_raw.csv, với mỗi cuốn còn thiếu trường thì gọi Gemini
(gemini-2.5-flash, có grounding tìm kiếm thật) để điền — CHỈ điền ô trống, không đè
dữ liệu đang có. Ghi ra data/books_metadata_enriched.csv, có checkpoint để resume.

Chạy:
    .venv/Scripts/python.exe -X utf8 enrich_metadata_ai.py --limit 5     # dry-run thử 5 cuốn
    .venv/Scripts/python.exe -X utf8 enrich_metadata_ai.py               # chạy toàn bộ (resume được)

Yêu cầu: GEMINI_API_KEY trong .env. Job dài → cứ Ctrl+C, chạy lại sẽ tiếp tục.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

IN_CSV  = "data/books_metadata_raw.csv"
OUT_CSV = "data/books_metadata_enriched.csv"

# Trường được phép làm giàu (KHÔNG đụng summary — đã 98.5% đầy, theo nguyên tắc fill-empty)
ENRICH_FIELDS = ["author", "publication_year", "genre", "publisher", "page_count"]
DELAY = 0.5          # giây giữa các lần gọi
MAX_RETRY = 3


def build_prompt(title: str, author: str, summary: str, missing: list[str]) -> str:
    field_desc = {
        "author": "tên tác giả (đúng thứ tự tiếng Việt, KHÔNG đảo họ-tên)",
        "publication_year": "năm XUẤT BẢN/SÁNG TÁC LẦN ĐẦU (KHÔNG phải năm tái bản), chỉ 4 chữ số",
        "genre": "thể loại văn học chuẩn (Tiểu thuyết, Truyện ngắn, Thơ, Kịch, Hồi ký, Tản văn...)",
        "publisher": "nhà xuất bản của ấn bản đầu/phổ biến",
        "page_count": "số trang (số nguyên)",
    }
    want = "\n".join(f'  - "{f}": {field_desc[f]}' for f in missing)
    return (
        "Bạn là trợ lý thư mục học. Hãy TÌM KIẾM thông tin THỰC về cuốn sách dưới đây "
        "và trả về JSON.\n\n"
        f"Tên sách: {title}\n"
        f"Tác giả: {author or '(chưa rõ — hãy tra cứu)'}\n"
        f"Tóm tắt tham khảo: {summary[:300]}\n\n"
        "Trả về DUY NHẤT một object JSON với các khoá sau (bỏ trống chuỗi \"\" nếu KHÔNG "
        "chắc chắn — TUYỆT ĐỐI không bịa số/URL):\n"
        f"{want}\n\n"
        'Ví dụ: {"publication_year": "1941", "genre": "Truyện ngắn"}\n'
        "CHỈ in JSON, không giải thích, không markdown."
    )


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_json(text: str) -> dict:
    m = _JSON_RE.search(text or "")
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


def make_model():
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    tool = genai.protos.Tool(google_search=genai.protos.Tool.GoogleSearch())
    return genai.GenerativeModel("gemini-2.5-flash", tools=[tool])


def enrich_one(model, row: dict) -> tuple[dict, list[str]]:
    """Trả về (row đã cập nhật, danh sách field AI điền)."""
    missing = [f for f in ENRICH_FIELDS if not (row.get(f) or "").strip()]
    if not missing:
        return row, []
    prompt = build_prompt(row["title"], row.get("author", ""), row.get("summary", ""), missing)
    for attempt in range(MAX_RETRY):
        try:
            resp = model.generate_content(prompt, request_options={"timeout": 90})
            data = parse_json(resp.text)
            filled = []
            for f in missing:
                v = str(data.get(f, "") or "").strip()
                if v and v.lower() not in ("none", "n/a", "null", "không rõ", "chưa rõ"):
                    if f == "publication_year":   # chỉ nhận 4 chữ số hợp lệ
                        mm = re.search(r"\b(1[5-9]\d\d|20[0-2]\d)\b", v)
                        if not mm:
                            continue
                        v = mm.group(0)
                    row[f] = v
                    filled.append(f)
            return row, filled
        except Exception as e:
            if attempt == MAX_RETRY - 1:
                print(f"    ⚠️ lỗi sau {MAX_RETRY} lần: {str(e)[:80]}")
                return row, []
            time.sleep(2 ** attempt * 2)   # backoff cho rate-limit
    return row, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=IN_CSV)
    ap.add_argument("--out", default=OUT_CSV)
    ap.add_argument("--limit", type=int, default=0, help="Chỉ xử lý N cuốn đầu cần làm giàu (dry-run)")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.inp, encoding="utf-8-sig")))
    cols = list(rows[0].keys())
    if "ai_filled" not in cols:
        cols.append("ai_filled")

    # Resume: id đã có trong output thì bỏ qua
    done_ids = set()
    out_path = Path(args.out)
    if out_path.exists():
        for r in csv.DictReader(open(out_path, encoding="utf-8-sig")):
            done_ids.add(r["id"])
        print(f"  Resume: đã có {len(done_ids):,} dòng trong {out_path.name}")

    model = make_model()
    fout = open(out_path, "a", encoding="utf-8-sig", newline="")
    w = csv.DictWriter(fout, fieldnames=cols)
    if not done_ids:
        w.writeheader()

    processed = enriched = api_calls = 0
    try:
        for row in rows:
            if row["id"] in done_ids:
                continue
            # Bỏ qua trang người (tác giả) — không enrich như sách
            if (row.get("entity_type") or "work") == "author":
                row["ai_filled"] = ""
                w.writerow(row); fout.flush()
                continue
            need = [f for f in ENRICH_FIELDS if not (row.get(f) or "").strip()]
            if not need:
                row["ai_filled"] = ""
                w.writerow(row); fout.flush()
                continue

            api_calls += 1
            try:
                row, filled = enrich_one(model, row)
            except Exception as e:   # bất kỳ lỗi lạ nào → bỏ qua cuốn này, KHÔNG sập job
                print(f"  [{processed+1}] {row['title'][:40]:40s} ← ⚠️ bỏ qua ({str(e)[:50]})")
                row["ai_filled"] = ""
                w.writerow(row); fout.flush()
                processed += 1
                continue
            row["ai_filled"] = ",".join(filled)
            w.writerow(row); fout.flush()
            processed += 1
            if filled:
                enriched += 1
                print(f"  [{processed}] {row['title'][:40]:40s} ← {filled}")
            else:
                print(f"  [{processed}] {row['title'][:40]:40s} ← (không tra được)")
            time.sleep(DELAY)

            if args.limit and api_calls >= args.limit:
                print(f"\n  ⏹ Dừng dry-run ở {args.limit} cuốn.")
                break
    except KeyboardInterrupt:
        print(f"\n  ⏸ Đã dừng (Ctrl+C). Đã lưu {processed} cuốn. "
              f"Chạy lại đúng lệnh này để TIẾP TỤC từ chỗ dừng.")
    finally:
        fout.close()
    print(f"\n  ✅ Xử lý {processed} cuốn | điền được {enriched} | ghi → {out_path}")


if __name__ == "__main__":
    main()
