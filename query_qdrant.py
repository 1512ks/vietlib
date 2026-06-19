"""
query_qdrant.py - Kịch bản kiểm thử việc tìm kiếm ngữ nghĩa với QdrantDB.
"""
import sys
from pathlib import Path

# Cho phep import cac module trong thu muc nguon
sys.path.insert(0, str(Path(__file__).parent))

from vector_store.qdrant_client_app import QdrantManager
from chunking.embedder import Embedder

def main():
    print("Khởi tạo Embedder để biến câu hỏi thành Vector...")
    embedder = Embedder(model_name=Embedder.FAST_MODEL)
    
    print("Kết nối QdrantDB Database...")
    db = QdrantManager(collection_name="vn_literature_gbooks")
    
    # 1. Dinh nghia cau hoi 
    query = "Tuyển tập truyện ngắn của tác giả Nam Cao viết về cái nghèo"
    print(f"\n[?] Câu hỏi: '{query}'")
    
    # 2. Embedding cau hoi
    q_vec = embedder.embed_query(query)
    
    # 3. Tra cuu Vector
    print(f"[*] Đang tra cứu Vector Database lấy top 3 kết quả...\n")
    results = db.query(
        query_vector=q_vec.tolist(),
        limit=3
    )
    
    # 4. Hien thi ket qua tra cuu
    for i, res in enumerate(results):
        score = res.score
        payload = res.payload
        
        # Lay thong tin Meta
        title = payload.get("title", "Unknown")
        author = payload.get("author", "Unknown")
        doc = payload.get("text", "")
        
        print(f"--- Top {i+1} : Score = {score:.4f} ---")
        print(f"Tác giả: {author}\nTác phẩm: {title}")
        print(f"Trích đoạn: {doc[:200]}...")
        print("-" * 50)
        
if __name__ == "__main__":
    main()
