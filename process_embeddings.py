"""
process_embeddings.py - Chạy chunking (sliding_window) & embedding trên TOÀN BỘ dữ liệu gbooks.
"""
import sys
import time
from pathlib import Path
import json

# Setup import path
sys.path.insert(0, str(Path(__file__).parent))

from chunking.chunker import Chunker
from chunking.embedder import Embedder, NumpyRetriever

DATA_DIR = Path("data/processed/gbooks")
OUT_DIR = Path("data/embeddings")

def main():
    print("=" * 60)
    print(" BẮT ĐẦU CHUNKING & EMBEDDING TOÀN BỘ GBOOKS")
    print("=" * 60)

    # 1. Load data
    files = list(DATA_DIR.glob("*.json"))
    docs = []
    for f in files:
        try:
            docs.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"Lỗi đọc {f.name}: {e}")
            
    print(f"Đã load {len(docs)} tài liệu từ {DATA_DIR}")

    # 2. Chunking
    # Chien luoc tot nhat: sliding_window, chunk_size=200, stride=100 (overlap 50%)
    chunker = Chunker(strategy="sliding_window", chunk_size=200, stride=100)
    all_chunks = []
    
    for doc in docs:
        text = doc.get("content", "") or doc.get("summary", "")
        if not text:
            continue
            
        doc_id = doc.get("id", "unknown_id")
        meta = {
            "title": doc.get("title", ""),
            "author": doc.get("author", ""),
            "source": doc.get("source", ""),
            "genre": doc.get("genre", ""),
        }
        
        chunks = chunker.chunk(text, doc_id=doc_id, metadata=meta)
        all_chunks.extend(chunks)
        
    print(f"Đã tạo {len(all_chunks):,} chunks. (Sliding Window, size=200, stride=100)")

    # 3. Embedding
    print("\nKhởi tạo Embedder...")
    # Dùng fast model để sinh embedding đủ nhanh nghiệm trên CPU
    embedder = Embedder(model_name=Embedder.FAST_MODEL)
    retriever = NumpyRetriever(embedder)
    
    # Chia nhỏ chunk array để thấy progress bar nếu quá nhiều (tùy chọn)
    t0 = time.time()
    retriever.add_chunks(all_chunks)
    elapsed = time.time() - t0
    
    print(f"\nThời gian embed: {elapsed:.1f}s ({len(all_chunks)/max(elapsed, 1):.0f} chunks/s)")

    # 4. Save
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "gbooks_sliding_window_index"
    retriever.save(out_path)
    
    print("=" * 60)
    print(f"HOÀN TẤT! Toàn bộ file đã được lưu tại {out_path}_vecs.npy")

if __name__ == "__main__":
    main()
