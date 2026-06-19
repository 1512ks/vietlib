"""
load_to_chroma.py - Đọc file vector .npy và meta .json đưa vào ChromaDB.
"""
import sys
from pathlib import Path
import json
import logging
import time

import numpy as np

# Cho phep import cac module trong thu muc nguon
sys.path.insert(0, str(Path(__file__).parent))
from vector_store.chroma_client import ChromaManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

VECS_FILE = Path("data/embeddings/gbooks_sliding_window_index_vecs.npy")
META_FILE = Path("data/embeddings/gbooks_sliding_window_index_meta.json")

def main():
    if not VECS_FILE.exists() or not META_FILE.exists():
        logger.error("Không tìm thấy dữ liệu embedding. Vui lòng kiểm tra lại kết quả chạy phần trước!")
        return
        
    logger.info("Đang load file Numpy Embeddings và Json Metadata...")
    # Load Numpy Array: shape se la (N, D) - N la luong chunks, D la chieu vector
    embeddings_np = np.load(VECS_FILE)
    
    # Load List Meta Json: gom {chunk_id, doc_id, text, metadata, ...}
    with open(META_FILE, "r", encoding="utf-8") as f:
        meta_data = json.load(f)
        
    if len(embeddings_np) != len(meta_data):
        logger.error("Số lượng Vector và Meta không khớp nhau!")
        return
        
    logger.info(f"Tổng số chunks: {len(meta_data)} (chiều vector: {embeddings_np.shape[1]})")
    
    # Chuyen doi du lieu sang dinh dang ChromaDB yeu cau
    ids = []
    embeddings = []
    metadatas = []
    documents = []
    
    for i, meta in enumerate(meta_data):
        chunk_id = meta.get("chunk_id")
        text = meta.get("text", "")
        # Dua cac meta cua document ra ben ngoai
        custom_metadata = meta.get("metadata", {})
        
        # ChromaDB yêu cầu metadata values không được là None/Dict phức tạp. Chỉ được lưu float, int, str.
        clean_metadata = {
            "source_doc_id": meta.get("doc_id", ""),
            "title": str(custom_metadata.get("title", "")),
            "author": str(custom_metadata.get("author", "")),
            "word_count": meta.get("word_count", 0),
        }
        
        ids.append(chunk_id)
        # Chuyển array 1 chiều sang python float list
        embeddings.append(embeddings_np[i].tolist())
        metadatas.append(clean_metadata)
        documents.append(text)
        
    logger.info("Đang kết nối qua ChromaManager...")
    DB = ChromaManager(collection_name="vn_literature_gbooks")
    
    # Upsert data vào ChromaDB
    t0 = time.time()
    logger.info("Bắt đầu Insert vào Database...")
    DB.batch_upsert(ids, embeddings, metadatas, documents, batch_size=500)
    
    logger.info(f"Hoàn thành trong việc Insert Database sau {time.time()-t0:.2f} giây.")

if __name__ == "__main__":
    main()
