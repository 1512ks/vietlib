"""
build_knowledge_base.py - Metadata Injection & Document Merging
Nạp dữ liệu vào Qdrant & BM25 với cấu trúc mới: 1 Tác phẩm = 1 Chunk.
"""
import sys
import json
import time
import logging
import uuid
import os
from pathlib import Path

# Setup import path
sys.path.insert(0, str(Path(__file__).parent))

from chunking.chunker import TextChunk
from chunking.embedder import Embedder
from vector_store.qdrant_client_app import QdrantManager
from search.bm25_retriever import BM25Retriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/processed")
BATCH_SIZE = 50  # Giảm xuống 50 vì payload (Text + Meta) khá nặng
COLLECTION_NAME = "vn_literature"
BM25_CACHE_PATH = Path("data/bm25_index.pkl")

# Các thư mục con cần nạp (loại bỏ concept vì chứa lịch sử/quân sự không liên quan văn học)
INCLUDE_SUBDIRS = {"author", "work", "gbooks", "archive_compact"}


def _pick(sources: dict, *keys) -> str:
    """Lấy giá trị non-empty đầu tiên của một trường qua tất cả các nguồn của 1 thực thể."""
    for src in sources.values():
        for k in keys:
            v = src.get(k)
            if isinstance(v, list):
                v = v[0] if v else ""
            if v not in (None, "", []):
                return str(v).strip()
    return ""

def get_merged_documents() -> list[TextChunk]:
    """
    Quét các thư mục, gộp các nguồn dữ liệu chung của một tác phẩm/tác giả
    và tạo ra 1 TextChunk duy nhất (đã inject metadata) cho mỗi item.
    """
    logger.info("Scanning for JSON files...")

    all_files = []
    for subdir in INCLUDE_SUBDIRS:
        d = DATA_DIR / subdir
        if d.exists():
            found = list(d.glob("*.json"))
            all_files.extend(found)
            logger.info(f"  {subdir:20s}: {len(found):6,} files")
        else:
            logger.warning(f"  {subdir:20s}: MISSING (skipped)")

    # Loại bỏ file meta
    all_files = [f for f in all_files if "meta" not in f.name]
    logger.info(f"Total found: {len(all_files):,} files. Merging by title+author...")

    import re as _re

    def _norm_title(t: str) -> str:
        """Chuẩn hoá tiêu đề để gộp: lowercase, bỏ đuôi '(tiểu thuyết)'..., gọn khoảng trắng."""
        t = t.lower().strip()
        t = _re.sub(r"\s*\([^)]*\)\s*$", "", t)
        return _re.sub(r"\s+", " ", t).strip()

    def _author_str(data: dict) -> str:
        a = data.get("author", "") or data.get("authors", "")
        if isinstance(a, list):
            a = a[0] if a else ""
        return str(a).strip()

    # ── Pass 1: gom theo (norm_title, author) ──
    unique_docs = {}
    for f in all_files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            title = (data.get("title") or data.get("name") or "").strip()
            if not title:
                continue

            author = _author_str(data)
            nt = _norm_title(title)
            # Khoá tác giả = token tên đã sắp xếp → gộp được tên bị đảo thứ tự
            # (vd Google Books trả "Trọng Phụng Vũ" cho "Vũ Trọng Phụng").
            akey = " ".join(sorted(author.lower().split()))
            key = f"{nt} | {akey}"

            if key not in unique_docs:
                unique_docs[key] = {
                    "title": title, "author": author,
                    "norm_title": nt, "sources": {}, "paths": [],
                }

            # Xác định source gốc
            source = data.get("source", "unknown")
            if "archive" in f.parent.name:
                source = "archive_compact"
            elif "gbooks" in f.parent.name:
                source = "gbooks"
            elif "wikipedia" in data.get("url", "") or "author" in f.parent.name or "work" in f.parent.name or "concept" in f.parent.name:
                source = "wikipedia"

            unique_docs[key]["sources"][source] = data
            unique_docs[key]["paths"].append(str(f))

        except Exception:
            continue

    n_pass1 = len(unique_docs)

    # ── Pass 2: gộp nhóm author-RỖNG vào nhóm CÓ tác giả cùng tiêu đề (chỉ khi DUY NHẤT,
    #            để tránh gộp nhầm hai tác phẩm trùng tên khác tác giả) ──
    authored_by_title = {}
    for k, dd in unique_docs.items():
        if dd["author"]:
            authored_by_title.setdefault(dd["norm_title"], []).append(k)

    merged = 0
    for k in list(unique_docs.keys()):
        dd = unique_docs.get(k)
        if not dd or dd["author"]:
            continue
        cands = authored_by_title.get(dd["norm_title"], [])
        if len(cands) == 1:
            tgt = unique_docs[cands[0]]
            for s, dat in dd["sources"].items():
                tgt["sources"].setdefault(s, dat)   # không ghi đè nguồn đã có của nhóm đích
            tgt["paths"].extend(dd["paths"])
            del unique_docs[k]
            merged += 1

    logger.info(f"After grouping: pass1={n_pass1:,} → gộp {merged:,} nhóm author-rỗng → "
                f"{len(unique_docs):,} unique entities.")

    # Tạo TextChunk với Metadata Injection
    final_chunks = []
    
    for key, doc_data in unique_docs.items():
        sources = doc_data["sources"]
        title = doc_data["title"]
        author = doc_data["author"]
        # Hiển thị: ưu tiên tên từ wikipedia/archive (đúng thứ tự VN) hơn gbooks (hay đảo)
        for s in ("wikipedia", "archive_compact", "gbooks"):
            if s in sources:
                a = _author_str(sources[s])
                if a:
                    author = a
                    break
        
        summary = ""
        genres = []
        year = ""
        word_count = ""
        ai_summary = ""
        publisher = ""
        genre_val = ""

        # Merge data từ các nguồn
        if "wikipedia" in sources:
            w = sources["wikipedia"]
            # Ưu tiên lấy description (đoạn mở đầu), nếu không có thì lấy content cắt ngắn
            summary = w.get("description", "") or w.get("content", "")

        if "gbooks" in sources:
            gb = sources["gbooks"]
            if not summary:
                summary = gb.get("description", "")
            genres = gb.get("categories", gb.get("genres", []))
            year = gb.get("publishedDate", "")

        if "archive_compact" in sources:
            ac = sources["archive_compact"]
            ai_summary = ac.get("ai_summary", "")
            word_count = ac.get("word_count", "")
            if not summary:
                # Dùng ai_summary nếu có, nếu không thì dùng 'content' (chứa Trích đoạn mở đầu)
                summary = ai_summary or ac.get("content", "")

        # === Ưu tiên siêu dữ liệu ĐÃ LÀM GIÀU (đọc từ MỌI nguồn sau bước import) ===
        enriched_year = _pick(sources, "publication_year")
        if enriched_year:
            year = enriched_year                      # năm làm giàu > publishedDate (reprint)
        publisher = _pick(sources, "publisher")
        genre_val = _pick(sources, "genre")
        if not genres and genre_val:
            genres = [genre_val]
                
        # Dọn dẹp summary
        summary = summary.strip()
        if not summary:
            continue  # Bỏ qua nếu hoàn toàn không có nội dung gì

        # === METADATA INJECTION ===
        parts = [f"[Tiêu đề: {title}]"]
        if author: parts.append(f"[Tác giả: {author}]")
        if year: parts.append(f"[Năm xuất bản: {year}]")
        
        # Ép kiểu genres về dạng list chuỗi
        if genres:
            if isinstance(genres, list):
                genres_str = ", ".join([str(g) for g in genres])
            else:
                genres_str = str(genres)
            parts.append(f"[Thể loại: {genres_str}]")
            
        if publisher: parts.append(f"[Nhà xuất bản: {publisher}]")
        if word_count: parts.append(f"[Độ dài tác phẩm: ~{word_count} từ]")
        
        chunk_text = " | ".join(parts) + "\n\n"
        
        if ai_summary and ai_summary not in summary:
            chunk_text += f"Tóm tắt AI: {ai_summary}\n\n"
            
        chunk_text += f"Nội dung chi tiết:\n{summary}"
        
        # Cắt bớt nếu nội dung quá dài (chỉ giữ lại 3000 ký tự cho context/summary)
        # Vì ta đã thống nhất "loại bỏ chunk chi tiết truyện", 3000 kí tự là đủ cho bối cảnh.
        if len(chunk_text) > 3000:
            chunk_text = chunk_text[:3000] + "..."
            
        chunk_id = str(uuid.uuid5(uuid.NAMESPACE_OID, key))
        
        chunk = TextChunk(
            chunk_id=chunk_id,
            doc_id=chunk_id,
            text=chunk_text,
            start_word=0,
            end_word=len(chunk_text.split()),
            word_count=len(chunk_text.split()),
            char_count=len(chunk_text),
            strategy="metadata_injection",
            metadata={
                "title": title,
                "author": author,
                "year": year,
                "genre": genre_val or (genres[0] if genres else ""),
                "publisher": publisher,
                "source": ", ".join(sources.keys())
            }
        )
        final_chunks.append(chunk)

    logger.info(f"Generated {len(final_chunks):,} rich document chunks.")
    return final_chunks


def reset_databases():
    """Xoá sạch collection trên Qdrant và file BM25 cũ"""
    logger.info("Resetting databases...")
    # Qdrant LOCAL mode: delete_collection KHÔNG xoá sạch trên đĩa → xoá thẳng thư mục
    # để tránh tích điểm rác giữa các lần rebuild. (Cloud thì thư mục này không tồn tại.)
    try:
        import shutil
        from vector_store.qdrant_client_app import DB_DIR
        if DB_DIR.exists():
            shutil.rmtree(DB_DIR, ignore_errors=True)
            logger.info(f"Đã xoá thư mục Qdrant local: {DB_DIR}")
    except Exception as e:
        logger.warning(f"Không xoá được thư mục Qdrant local: {e}")
    try:
        db = QdrantManager(collection_name=COLLECTION_NAME, vector_size=384)
        db.client.delete_collection(COLLECTION_NAME)
        logger.info(f"Đã xoá collection {COLLECTION_NAME} trên Qdrant.")
    except Exception as e:
        logger.warning(f"Không thể xoá Qdrant collection (có thể chưa tồn tại): {e}")

    if BM25_CACHE_PATH.exists():
        os.remove(BM25_CACHE_PATH)
        logger.info("Đã xoá BM25 cache cũ.")


def main():
    logger.info("=" * 60)
    logger.info(" BẮT ĐẦU REBUILD KNOWLEDGE BASE (METADATA INJECTION)")
    logger.info("=" * 60)

    # 1. Reset Database
    reset_databases()
    
    # Khởi tạo lại Qdrant (sẽ tự động tạo mới collection vì đã bị xoá)
    db = QdrantManager(collection_name=COLLECTION_NAME, vector_size=384)

    # 2. Extract & Merge Data
    chunks = get_merged_documents()
    total_chunks = len(chunks)
    
    if total_chunks == 0:
        logger.error("Không tìm thấy dữ liệu nào để nạp!")
        return

    # 3. Init Embedder
    logger.info("Khởi tạo Embedder...")
    embedder = Embedder(model_name=Embedder.FAST_MODEL)
    
    # 4. Batch Processing
    logger.info(f"Tiến hành nạp {total_chunks} tác phẩm/khái niệm lên Qdrant...")
    
    inserted = 0
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i:i+BATCH_SIZE]
        
        t0 = time.time()
        # Embed
        embeddings = embedder.embed_chunks(batch)
        
        # Prepare payload
        ids = [chunk.chunk_id for chunk in batch]
        payloads = [
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "source_doc_id": chunk.doc_id,
                "title": chunk.metadata.get("title", ""),
                "author": chunk.metadata.get("author", ""),
                "year": chunk.metadata.get("year", ""),
                "genre": chunk.metadata.get("genre", ""),
                "publisher": chunk.metadata.get("publisher", ""),
                "source": chunk.metadata.get("source", ""),
            }
            for chunk in batch
        ]
        
        # Insert
        db.batch_upsert(ids, embeddings.tolist(), payloads, batch_size=500)
        
        inserted += len(batch)
        logger.info(f"-> Batch {i//BATCH_SIZE + 1} ({time.time() - t0:.1f}s) | Tổng nạp: {inserted}/{total_chunks}")
        
    logger.info("=" * 60)
    logger.info(f"Đã hoàn thành nạp Qdrant! Tổng số chunks: {inserted}")
    
    # 5. Rebuild BM25
    logger.info("=" * 60)
    logger.info("Bắt đầu Rebuild BM25 Index từ Qdrant...")
    BM25_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    retriever = BM25Retriever.from_qdrant(
        qdrant_manager=db,
        index_cache_path=BM25_CACHE_PATH,
        force_rebuild=True
    )
    
    logger.info(f"KNOWLEDGE BASE ĐÃ SẴN SÀNG! (BM25 size: {retriever.size})")

if __name__ == "__main__":
    main()
