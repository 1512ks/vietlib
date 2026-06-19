"""
query_chroma.py - Kịch bản kiểm thử việc tìm kiếm ngữ nghĩa với ChromaDB.
"""
import sys
from pathlib import Path
import json

# Cho phep import cac module trong thu muc nguon
sys.path.insert(0, str(Path(__file__).parent))

from vector_store.chroma_client import ChromaManager
from chunking.embedder import Embedder

def main():
    print("Khởi tạo Embedder để biến câu hỏi thành Vector...")
    # Phai dung dung Embedder model nhu luc build Database.
    embedder = Embedder(model_name=Embedder.FAST_MODEL)
    
    print("Kết nối ChromaDB Database...")
    db = ChromaManager(collection_name="vn_literature_gbooks")
    
    # 1. Dinh nghia cau hoi 
    query = "Tuyển tập truyện ngắn của tác giả Nam Cao viết về cái nghèo"
    print(f"\n[?] Câu hỏi: '{query}'")
    
    # 2. Embedding cau hoi
    q_vec = embedder.embed_query(query)
    
    # 3. Tra cuu Vector
    print(f"[*] Đang tra cứu Vector Database lấy top 3 kết quả...\n")
    results = db.query(
        query_embeddings=[q_vec.tolist()],
        n_results=3
    )
    
    # 4. Hien thi ket qua tra cuu
    distances = results["distances"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    
    for i in range(len(distances)):
        score = distances[i]
        meta = metas[i]
        doc = docs[i]
        
        # Vi luu voi `cosine`, Chroma tra ra distance. Similarity se lien quan den 1 - distance.
        title = meta.get("title", "Unknown")
        author = meta.get("author", "Unknown")
        
        print(f"--- Top {i+1} : Score = {score:.4f} ---")
        print(f"Tác giả: {author}\nTác phẩm: {title}")
        print(f"Trích đoạn: {doc[:150]}...")
        print("-" * 50)
        
if __name__ == "__main__":
    main()
