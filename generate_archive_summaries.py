"""
generate_archive_summaries.py  (v3 - ổn định, không lỗi 404/429)
══════════════════════════════════════════════════════════════════
Dùng Gemini API để tạo tóm tắt cho toàn bộ archive_compact.

Các fix so với phiên bản cũ:
  ✅ Dùng google-genai (package mới, tránh lỗi 404)
  ✅ Single-thread, tuần tự (tránh 429 và tránh ghi file bị cắt cụt)
  ✅ Đúng model name: gemini-2.5-flash (đã kiểm tra)
  ✅ needs_summary() bắt cả trường hợp summary bị cắt (< 50 ký tự)
  ✅ Backoff tự động khi gặp 429: chờ 65 giây rồi thử lại
  ✅ Resume hoàn toàn: bỏ qua file đã có summary đầy đủ

Cách chạy:
  .\.venv\Scripts\python.exe generate_archive_summaries.py
  .\.venv\Scripts\python.exe generate_archive_summaries.py --limit 10
  .\.venv\Scripts\python.exe generate_archive_summaries.py --dry-run
"""

import sys, os, json, time, logging, argparse
from pathlib import Path
from datetime import datetime

# ── Fix encoding Windows ────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Config ──────────────────────────────────────────────────────
COMPACT_DIR  = Path("data/processed/archive_compact")
LOG_FILE     = Path("data/generate_summaries_v3.log")

GEMINI_MODEL     = "gemini-2.5-flash-lite"  # Rẻ hơn 4x gemini-2.5-flash, hoạt động trơn tru
MIN_SUMMARY_LEN  = 150                 # Summary ngắn hơn = coi là cắt cụt, tóm tắt lại
CONTENT_EXCERPT  = 3000                 # chars đầu đưa vào prompt
RETRY_MAX        = 4                    # số lần retry khi lỗi tạm thời
BACKOFF_429      = 65                   # giây chờ khi bị 429 (quota reset sau 60s)
BACKOFF_OTHER    = 10                   # giây chờ khi lỗi khác

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
#  Điều kiện cần tóm tắt lại
# ══════════════════════════════════════════════════════════════════
def needs_summary(doc: dict) -> bool:
    """
    True nếu file cần được tóm tắt (hoặc tóm tắt lại).
    - Chưa có ai_summary → True
    - ai_summary quá ngắn (bị cắt cụt lúc ghi) → True
    - Chưa có genre (format cũ, cần tóm tắt lại với prompt mới) → True
    - ai_summary đầy đủ và có genre → False
    """
    summary = doc.get("ai_summary", "")
    genre   = doc.get("genre", "")
    if not summary or len(summary.strip()) < MIN_SUMMARY_LEN:
        return True
    if not genre:  # Format cũ chưa có genre → tóm tắt lại
        return True
    return False


# ══════════════════════════════════════════════════════════════════
#  Gemini Client (dùng google-genai mới)
# ══════════════════════════════════════════════════════════════════
PROMPT_TEMPLATE = """\
Hãy phân tích và viết tóm tắt cho tác phẩm văn học sau.
Trả lời ĐÚNG THEO định dạng bên dưới, không thêm bất cứ thứ gì khác:

Thể loại: [ví dụ: Tiểu thuyết lịch sử / Truyện ngắn / Thơ / Kiếm hiệp / Trinh thám / Cổ tích / Hồi ký / v.v.]
Đối tượng: [ví dụ: Người lớn / Thiếu nhi / Thanh thiếu niên / Mọi lứa tuổi]
Tóm tắt: [3-5 câu mô tả nội dung chính, nhân vật, bối cảnh của tác phẩm]

Tên tác phẩm: {title}
Tác giả: {author}
Trích đoạn nội dung:
\"\"\"
{excerpt}
\"\"\""""


class GeminiClient:
    def __init__(self, api_key: str, model: str = GEMINI_MODEL):
        try:
            from google import genai
            from google.genai import types
            self._genai = genai
            self._types = types
            self._client = genai.Client(api_key=api_key)
            self._model  = model
            log.info(f"Khởi tạo Gemini (google-genai) | Model: {model}")
        except ImportError:
            raise ImportError(
                "Thiếu package google-genai.\n"
                "Cài đặt: pip install google-genai"
            )

    def summarize(self, title: str, author: str, content: str) -> dict:
        """Trả về dict gồm: genre, audience, summary"""
        excerpt = self._extract_excerpt(content)
        prompt  = PROMPT_TEMPLATE.format(
            title=title,
            author=author or "Khuyết danh",
            excerpt=excerpt,
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=512,
                thinking_config=self._types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return self._parse_response(response.text.strip())

    @staticmethod
    def _parse_response(text: str) -> dict:
        """Parse response có định dạng 'Thể loại: ... / Đối tượng: ... / Tóm tắt: ...'"""
        result = {"genre": "", "audience": "", "summary": ""}
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("Thể loại:"):
                result["genre"] = line.split(":", 1)[1].strip()
            elif line.startswith("Đối tượng:"):
                result["audience"] = line.split(":", 1)[1].strip()
            elif line.startswith("Tóm tắt:"):
                result["summary"] = line.split(":", 1)[1].strip()
        # Fallback: nếu không parse được format, dùng toàn bộ text làm summary
        if not result["summary"] and text:
            result["summary"] = text
        return result

    @staticmethod
    def _extract_excerpt(content: str) -> str:
        lines = content.split("\n")
        body, header_done = [], False
        for line in lines:
            line = line.strip()
            if not line:
                if header_done:
                    body.append("")
                continue
            if len(line) >= 60:
                header_done = True
            if header_done:
                body.append(line)
            if sum(len(l) for l in body) >= CONTENT_EXCERPT:
                break
        excerpt = "\n".join(body).strip()
        return excerpt[:CONTENT_EXCERPT] if excerpt else content[:CONTENT_EXCERPT]


# ══════════════════════════════════════════════════════════════════
#  Tạo nội dung Book Card mới (sau khi có AI summary)
# ══════════════════════════════════════════════════════════════════
def make_book_card(title: str, author: str, word_count: int,
                   summary: str, genre: str = "", audience: str = "") -> str:
    def pages(wc):
        if wc <= 0: return "không rõ"
        p = wc // 250
        if p < 10:  return f"~{p} trang (truyện ngắn/thơ)"
        if p < 100: return f"~{p} trang (truyện vừa)"
        return f"~{p} trang (tiểu thuyết)"

    lines = [
        f"Tác phẩm: {title}",
        f"Tác giả: {author or 'Khuyết danh'}",
    ]
    if genre:    lines.append(f"Thể loại: {genre}")
    if audience: lines.append(f"Đối tượng: {audience}")
    lines += [
        f"Độ dài: {word_count:,} từ ({pages(word_count)})",
        f"Ngôn ngữ: Tiếng Việt",
        f"Nguồn: Kho lưu trữ văn học (archive)",
        f"Tóm tắt: {summary}",
    ]
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
#  Xử lý 1 file (single-thread, tuần tự)
# ══════════════════════════════════════════════════════════════════
def process_file(f: Path, client: GeminiClient, dry_run: bool) -> str:
    """
    Xử lý 1 file archive_compact.
    Returns: "done" | "skip" | "error:<msg>"
    """
    try:
        doc = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        return f"error:parse:{e}"

    if not needs_summary(doc):
        return "skip"

    title  = doc.get("title", "")
    author = doc.get("author", "Khuyết danh")
    wc     = doc.get("word_count", 0)

    if dry_run:
        log.info(f"[DRY RUN] {title[:50]}")
        return "skip"

    # Đọc nội dung gốc từ archive (để có full text làm excerpt)
    orig_content = ""
    orig_file = Path("data/processed/archive") / f.name
    if orig_file.exists():
        try:
            orig_doc = json.loads(orig_file.read_text(encoding="utf-8"))
            orig_content = orig_doc.get("content", "")
        except Exception:
            pass
    if not orig_content:
        orig_content = doc.get("content", "")

    # Gọi API với retry + backoff
    result = None
    for attempt in range(1, RETRY_MAX + 1):
        try:
            result = client.summarize(title, author, orig_content)
            # Kiểm tra kết quả không bị cắt
            summary = result.get("summary", "")
            if not summary or len(summary.strip()) < MIN_SUMMARY_LEN:
                raise ValueError(f"Summary quá ngắn: '{summary[:60]}'")
            break
        except Exception as e:
            err = str(e)
            is_429 = "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err
            is_404 = "404" in err or "not found" in err.lower()

            if is_404:
                return f"error:404_model_not_found"

            wait = BACKOFF_429 if is_429 else BACKOFF_OTHER
            log.warning(
                f"  Attempt {attempt}/{RETRY_MAX} thất bại | "
                f"{'[429 quota]' if is_429 else '[lỗi khác]'} | "
                f"Chờ {wait}s... | {err[:80]}"
            )
            if attempt < RETRY_MAX:
                time.sleep(wait)
            else:
                return f"error:max_retries"

    if not result:
        return "error:empty"

    summary  = result.get("summary", "")
    genre    = result.get("genre", "")
    audience = result.get("audience", "")

    # Cập nhật file
    doc["content"]    = make_book_card(title, author, wc, summary, genre, audience)
    doc["char_count"] = len(doc["content"])
    doc["ai_summary"] = summary
    doc["genre"]      = genre
    doc["audience"]   = audience
    doc["summary_generated_at"] = datetime.now().isoformat()

    try:
        f.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        return f"error:write:{e}"

    return "done"


# ══════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit",   type=int, default=0, help="Giới hạn số file xử lý")
    parser.add_argument("--model",   default=GEMINI_MODEL)
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and not args.dry_run:
        log.error("Không tìm thấy GEMINI_API_KEY!")
        sys.exit(1)

    if not COMPACT_DIR.exists():
        log.error(f"Không tìm thấy thư mục: {COMPACT_DIR}")
        sys.exit(1)

    # Quét và phân loại file
    all_files   = sorted(COMPACT_DIR.glob("*.json"))
    pending     = []
    skip_count  = 0

    for f in all_files:
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
            if needs_summary(doc):
                pending.append(f)
            else:
                skip_count += 1
        except Exception:
            pending.append(f)  # File lỗi cũng xử lý lại

    log.info(f"Tổng: {len(all_files):,} | Đã đầy đủ: {skip_count:,} | Cần xử lý: {len(pending):,}")

    if args.limit > 0:
        pending = pending[:args.limit]
        log.info(f"Giới hạn: {len(pending)} file")

    if not pending:
        log.info("Không còn file nào cần xử lý!")
        return

    client = GeminiClient(api_key, model=args.model) if not args.dry_run else None

    stats  = {"done": 0, "skip": 0, "error": 0}
    t0     = time.time()

    log.info("=" * 60)
    log.info(f"BẮT ĐẦU (single-thread, tuần tự) | {len(pending)} files")
    log.info("=" * 60)

    for i, f in enumerate(pending, 1):
        result = process_file(f, client, dry_run=args.dry_run)

        if result == "done":
            stats["done"] += 1
            # Log mỗi 20 file hoặc file đầu tiên
            if stats["done"] == 1 or stats["done"] % 20 == 0:
                elapsed  = time.time() - t0
                rate     = stats["done"] / elapsed if elapsed > 0 else 0
                eta_sec  = (len(pending) - i) / rate if rate > 0 else 0
                eta_str  = f"{eta_sec/3600:.1f}h" if eta_sec > 3600 else f"{eta_sec/60:.0f}min"
                log.info(f"[{i}/{len(pending)}] Done={stats['done']} | "
                         f"Err={stats['error']} | ETA={eta_str}")
        elif result == "skip":
            stats["skip"] += 1
        elif result == "error:404_model_not_found":
            log.error("Lỗi 404: Model không tồn tại! Kiểm tra lại tên model.")
            break
        else:
            stats["error"] += 1
            log.warning(f"[{i}] Lỗi: {f.name[:30]} → {result}")

    elapsed = time.time() - t0
    log.info("=" * 60)
    log.info(f"HOÀN THÀNH trong {elapsed/60:.1f} phút")
    log.info(f"  Tóm tắt mới: {stats['done']:,}")
    log.info(f"  Bỏ qua:      {stats['skip']:,}")
    log.info(f"  Lỗi:         {stats['error']:,}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
