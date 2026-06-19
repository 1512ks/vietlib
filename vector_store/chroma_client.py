"""
chroma_client.py - Quản lý tương tác với ChromaDB.
"""

from pathlib import Path
import logging
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

# Thu muc luu tru database cuc bo
DB_DIR = Path(__file__).parent.parent / "data" / "vector_db"

class ChromaManager:
    def __init__(self, collection_name: str = "vn_literature_gbooks"):
        # Dam bao thu muc luu tru co ton tai
        DB_DIR.mkdir(parents=True, exist_ok=True)
        
        # Khoi tao PersistentClient cho phep luu database vao thu muc
        self.client = chromadb.PersistentClient(path=str(DB_DIR))
        self.collection_name = collection_name
        
        try:
            # Lay (hoac tao neu chua co) bang Collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"} # sử dụng Cosine Similarity cho embeddings
            )
            logger.info(f"Đã kết nối Collection '{self.collection_name}'. Tổng documents: {self.collection.count()}")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Collection: {e}")
            raise e

    def batch_upsert(self, ids: list[str], embeddings: list[list[float]], metadatas: list[dict], documents: list[str], batch_size: int = 500):
        """
        Thêm hoặc Cập nhật theo lô (batch) các vector và tài liệu vào Chroma.
        Upsert giúp tránh lỗi duplicate ID.
        """
        total = len(ids)
        for i in range(0, total, batch_size):
            end = min(i + batch_size, total)
            self.collection.upsert(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                metadatas=metadatas[i:end],
                documents=documents[i:end]
            )
            logger.info(f"Đã upsert được {end}/{total} chunks.")
            
    def query(self, query_embeddings: list[list[float]], n_results: int = 5) -> dict:
        """
        Truy vấn database bằng list các vector.
        """
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        return results
