from pathlib import Path
import json

data_dir = Path("data/raw_v2/books")
files = list(data_dir.glob("gbooks_*.json"))
print(f"Tổng số file: {len(files):,}")

langs = {}
no_desc = 0
total_words = 0

for f in files:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        lang = d.get("language", "unknown")
        langs[lang] = langs.get(lang, 0) + 1
        total_words += d.get("word_count", 0) or 0
        if not d.get("description") and not d.get("content"):
            no_desc += 1
    except Exception:
        pass

print(f"Tổng word count: {total_words:,}")
print(f"Sách không có mô tả: {no_desc}")
print("Phân bố ngôn ngữ:")
for lang, cnt in sorted(langs.items(), key=lambda x: -x[1]):
    print(f"  {lang}: {cnt:,} ({cnt/max(len(files),1)*100:.1f}%)")

pf = Path("data/gbooks_progress.json")
if pf.exists():
    prog = json.loads(pf.read_text(encoding="utf-8"))
    completed = prog.get("completed_queries", {})
    print(f"\nQueries đã hoàn thành: {len(completed)}")
    total_q = sum(
        v.get("count", 0) if isinstance(v, dict) else 0
        for v in completed.values()
    )
    print(f"Tổng sách thu được (theo progress): {total_q:,}")
else:
    print("\nChưa có file progress.")
