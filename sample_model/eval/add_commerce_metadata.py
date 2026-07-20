"""
add_commerce_metadata.py -- Bổ sung lớp siêu dữ liệu thương mại cho sample model.

Với mỗi tác phẩm trong metadata.csv:
  - Dùng Gemini grounded search (Google Search) tìm GIÁ THAM KHẢO trên Tiki.
  - Tạo tiki_link = URL tìm kiếm Tiki (LUÔN hợp lệ, không bịa link sản phẩm).
  - Lưu 1 nguồn grounding để truy vết.

LƯU Ý TRUNG THỰC: giá là "AI-searched, tham khảo" — có thể lệch thời điểm; cần verify thủ công trước khi công bố.

Chạy:  .venv/Scripts/python.exe sample_model/eval/add_commerce_metadata.py
"""
import os, re, csv, sys, time, urllib.parse
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
from google import genai
from google.genai import types

SRC = Path("sample_model/corpus/metadata.csv")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
cfg = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=0.0,
)

PRICE_RE = re.compile(r"(\d{1,3}(?:[.,]\d{3})+)")


def parse_price(text: str):
    """Lấy con số giá đầu tiên dạng 37.000 / 150,000 -> int VND."""
    m = PRICE_RE.search(text)
    if not m:
        return None
    return int(m.group(1).replace(".", "").replace(",", ""))


def search_price(title: str, author: str):
    q = (f'Giá bán phổ biến hiện tại (VND) của cuốn sách "{title}" của {author} '
         f'trên Tiki.vn là bao nhiêu? Trả lời ngắn gọn con số giá. Nếu không tìm thấy, trả lời "không rõ".')
    try:
        r = client.models.generate_content(model="gemini-2.5-flash", contents=q, config=cfg)
        price = parse_price(r.text or "")
        src = ""
        try:
            for c in r.candidates[0].grounding_metadata.grounding_chunks or []:
                if c.web and c.web.uri:
                    src = c.web.uri
                    break
        except Exception:
            pass
        return price, src
    except Exception as e:
        print("   LỖI:", e)
        return None, ""


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    out_fields = list(rows[0].keys()) + ["gia_tham_khao_vnd", "tiki_link", "nguon_gia"]

    for i, row in enumerate(rows, 1):
        title, author = row["ten_tac_pham"], row["tac_gia"]
        price, src = search_price(title, author)
        row["gia_tham_khao_vnd"] = price if price else ""
        row["tiki_link"] = "https://tiki.vn/search?q=" + urllib.parse.quote(f"{title} {author}")
        row["nguon_gia"] = src
        print(f"[{i:02d}/{len(rows)}] {title[:34]:<34} -> {price if price else 'không rõ'} đ")
        time.sleep(0.4)  # nhẹ nhàng với rate limit

    with open(SRC, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

    got = sum(1 for r in rows if r["gia_tham_khao_vnd"])
    print(f"\nXong: {got}/{len(rows)} tác phẩm có giá. Đã ghi -> {SRC}")


if __name__ == "__main__":
    main()
