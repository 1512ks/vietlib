"""
add_collection_prices.py -- Hoàn thiện lớp thương mại: với tác phẩm KHÔNG bán rời
(thơ lẻ, truyện ngắn lẻ), tìm TUYỂN TẬP/CUỐN SÁCH chứa nó đang bán trên Tiki + giá.

Thêm cột 'ban_thuong_mai' (ấn bản thương mại):
  - Tác phẩm đã có giá bán riêng  -> "Bản lẻ (bán riêng)"
  - Tác phẩm chưa có giá          -> tên tuyển tập chứa nó + giá tuyển tập

Chạy: .venv/Scripts/python.exe sample_model/eval/add_collection_prices.py
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
    tools=[types.Tool(google_search=types.GoogleSearch())], temperature=0.0)

PRICE_RE = re.compile(r"(\d{1,3}(?:[.,]\d{3})+)")


def parse_price(text: str):
    m = PRICE_RE.search(text)
    return int(m.group(1).replace(".", "").replace(",", "")) if m else None


def find_collection(title, author):
    q = (f'Tác phẩm "{title}" của {author} thường được in trong cuốn sách hoặc '
         f'tuyển tập nào đang bán trên Tiki.vn? Trả về ĐÚNG định dạng một dòng: '
         f'TẬP: <tên cuốn sách> | GIÁ: <giá VND phổ biến nhất, chỉ con số>. '
         f'Nếu không rõ giá ghi "GIÁ: không rõ".')
    try:
        r = client.models.generate_content(model="gemini-2.5-flash", contents=q, config=cfg)
        txt = (r.text or "").strip()
        mt = re.search(r"TẬP:\s*(.+?)\s*(?:\||GIÁ:|$)", txt)
        coll = mt.group(1).strip().strip('".') if mt else ""
        price = parse_price(txt.split("GIÁ:")[-1]) if "GIÁ:" in txt else parse_price(txt)
        src = ""
        try:
            for c in r.candidates[0].grounding_metadata.grounding_chunks or []:
                if c.web and c.web.uri:
                    src = c.web.uri; break
        except Exception:
            pass
        return coll, price, src
    except Exception as e:
        print("   LỖI:", e)
        return "", None, ""


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    fields = list(rows[0].keys())
    if "ban_thuong_mai" not in fields:
        fields = fields + ["ban_thuong_mai"]

    for i, row in enumerate(rows, 1):
        if row.get("gia_tham_khao_vnd"):
            row["ban_thuong_mai"] = "Bản lẻ (bán riêng)"
            continue
        title, author = row["ten_tac_pham"], row["tac_gia"]
        coll, price, src = find_collection(title, author)
        row["ban_thuong_mai"] = coll or ""
        if price:
            row["gia_tham_khao_vnd"] = price
            row["nguon_gia"] = src or row.get("nguon_gia", "")
        if coll:
            row["tiki_link"] = "https://tiki.vn/search?q=" + urllib.parse.quote(coll)
        print(f"[{i:02d}] {title[:26]:<26} -> tập: {(coll or 'không rõ')[:38]:<38} | {price if price else 'không rõ'} đ")
        time.sleep(0.4)

    with open(SRC, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader(); w.writerows(rows)

    got = sum(1 for r in rows if r["gia_tham_khao_vnd"])
    print(f"\nHoàn tất: {got}/{len(rows)} tác phẩm nay đã có giá (bản lẻ hoặc tuyển tập).")


if __name__ == "__main__":
    main()
