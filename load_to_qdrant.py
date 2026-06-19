"""
load_to_qdrant.py - Đọc file vector .npy và meta .json đưa vào QdrantDB.
"""
import sys
from pathlib import Path
import json
import logging
import time
import uuid
import numpy as np

# Cho phep import cac module trong thu muc nguon
sys.path.insert(0, str(Path(__file__).parent))
from vector_store.qdrant_client_app import QdrantManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

VECS_FILE = Path("data/embeddings/gbooks_sliding_window_index_vecs.npy")
META_FILE = Path("data/embeddings/gbooks_sliding_window_index_meta.json")

def main():
    if not VECS_FILE.exists() or not META_FILE.exists():
        logger.error("Không tìm thấy dữ liệu embedding. Vui lòng kiểm tra lại kết quả chạy phần trước!")
        return
        
    logger.info("Đang load file Numpy Embeddings và Json Metadata...")
    embeddings_np = np.load(VECS_FILE)
    
    with open(META_FILE, "r", encoding="utf-8") as f:
        meta_data = json.load(f)
        
    if len(embeddings_np) != len(meta_data):
        logger.error("Số lượng Vector và Meta không khớp nhau!")
        return
        
    vector_size = embeddings_np.shape[1]
    logger.info(f"Tổng số chunks: {len(meta_data)} (chiều vector: {vector_size})")
    
    ids = []
    embeddings = []
    payloads = []
    
    for i, meta in enumerate(meta_data):
        # Qdrant yeu cau ID phai la UUID hoac UInt64
        # Chung ta dung UUID tu chuoi chunk_id
        chunk_id = meta.get("chunk_id")
        hash_id = str(uuid.uuid5(uuid.NAMESPACE_OID, chunk_id))
        
        text = meta.get("text", "")
        custom_metadata = meta.get("metadata", {})
        
        payload = {
            "chunk_id": chunk_id,
            "text": text,
            "source_doc_id": meta.get("doc_id", ""),
            "title": str(custom_metadata.get("title", "")),
            "author": str(custom_metadata.get("author", "")),
            "word_count": meta.get("word_count", 0),
        }
        
        ids.append(hash_id)
        embeddings.append(embeddings_np[i].tolist())
        payloads.append(payload)
        
    logger.info("Đang kết nối qua QdrantManager...")
    DB = QdrantManager(collection_name="vn_literature_gbooks", vector_size=vector_size)
    
    t0 = time.time()
    logger.info("Bắt đầu Insert vào Database Qdrant...")
    DB.batch_upsert(ids, embeddings, payloads, batch_size=500)
    
    logger.info(f"Hoàn thành việc Insert Database sau {time.time()-t0:.2f} giây.")

if __name__ == "__main__":
    main()
