"""
check_data_quality.py -- Kiểm tra chất lượng data hiện tại
"""
import json
from pathlib import Path

BASE = Path("data/processed")

# ---- Wikipedia data ----
print("=== WIKIPEDIA DATA (data/processed/) ===")
total_wiki = 0
for type_dir in ["author", "work", "concept"]:
    d = BASE / type_dir
    if not d.exists():
        print(f"  {type_dir}: MISSING")
        continue
    files = list(d.glob("page_*.json"))
    too_short = [f for f in files if f.stat().st_size < 500]
    samples_empty_content = 0
    for f in files[:50]:
        data = json.loads(f.read_text(encoding="utf-8"))
        if not data.get("content", ""):
            samples_empty_content += 1
    print(f"  {type_dir:10s}: {len(files):4d} files | too_short(<500B): {len(too_short)} | empty_content(sample50): {samples_empty_content}")
    total_wiki += len(files)
print(f"  TOTAL WIKI   : {total_wiki}")

# ---- Gbooks data ----
print()
print("=== GBOOKS DATA (data/processed/gbooks/) ===")
gbooks_dir = BASE / "gbooks"
if gbooks_dir.exists():
    files = list(gbooks_dir.glob("gbooks_*.json"))
    total = len(files)
    no_desc = 0
    has_desc = 0
    desc_lens = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            desc = data.get("description", "") or data.get("content", "") or ""
            if desc and len(desc) >= 50:
                has_desc += 1
                desc_lens.append(len(desc))
            else:
                no_desc += 1
        except Exception:
            no_desc += 1
    avg_desc = sum(desc_lens) / len(desc_lens) if desc_lens else 0
    print(f"  Total gbooks : {total}")
    print(f"  Has desc(>=50): {has_desc} ({has_desc/total*100:.1f}%)")
    print(f"  No desc      : {no_desc} ({no_desc/total*100:.1f}%)")
    print(f"  Avg desc len : {avg_desc:.0f} chars")

    # sample 1 file co desc
    print()
    print("  -- Sample file WITH description --")
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        desc = data.get("description", "") or data.get("content", "") or ""
        if desc and len(desc) >= 100:
            print(f"  File: {f.name}")
            print(f"  Keys: {list(data.keys())}")
            print(f"  Title: {data.get('title','')}")
            print(f"  Desc ({len(desc)} chars): {desc[:200]}")
            break

    # sample 1 file KHONG co desc
    print()
    print("  -- Sample file WITHOUT description --")
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        desc = data.get("description", "") or data.get("content", "") or ""
        if not desc or len(desc) < 50:
            print(f"  File: {f.name}")
            print(f"  Keys: {list(data.keys())}")
            print(f"  Title: {data.get('title','')}")
            print(f"  Desc: {repr(desc[:100]) if desc else 'EMPTY'}")
            break
else:
    print("  gbooks/ directory: MISSING")

# ---- BM25 index ----
print()
print("=== BM25 INDEX ===")
bm25_path = Path("data/bm25_index.pkl")
if bm25_path.exists():
    size_mb = bm25_path.stat().st_size / 1024 / 1024
    print(f"  bm25_index.pkl: EXISTS ({size_mb:.1f} MB)")
else:
    print("  bm25_index.pkl: MISSING")
