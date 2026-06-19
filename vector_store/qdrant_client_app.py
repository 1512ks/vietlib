"""
qdrant_client_app.py - Quản lý tương tác với Qdrant (Local in-memory hoặc file).
"""
import os
import logging
from pathlib import Path

# Thu muc luu tru database cuc bo
DB_DIR = Path(__file__).parent.parent / "data" / "vector_db"

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

class QdrantManager:
    def __init__(self, collection_name: str = "vn_literature", vector_size: int = 384):
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Kiem tra cau hinh Cloud tu moi truong
        url = os.environ.get("QDRANT_URL")
        api_key = os.environ.get("QDRANT_API_KEY")
        
        if url and api_key:
            logger.info(f"Kết nối tới Qdrant Cloud tại: {url}")
            self.client = QdrantClient(url=url, api_key=api_key)
        else:
            # Mac dinh dung Local storage
            DB_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Kết nối tới Qdrant Local tại: {DB_DIR}")
            self.client = QdrantClient(path=str(DB_DIR))
            
        # Tao Collection neu chua ton tai
        if not self.client.collection_exists(collection_name=self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Đã tạo mới Collection '{self.collection_name}' (vector_size={self.vector_size}).")
        else:
            count = self.client.count(collection_name=self.collection_name).count
            logger.info(f"Đã kết nối Collection '{self.collection_name}'. Tổng documents: {count}")

    def batch_upsert(self, ids: list[str], embeddings: list[list[float]], payload: list[dict], batch_size: int = 500):
        """
        Thêm hoặc Cập nhật theo lô (batch) các vector và tài liệu vào Qdrant.
        """
        total = len(ids)
        for i in range(0, total, batch_size):
            end = min(i + batch_size, total)
            
            points = [
                PointStruct(id=ids[j], vector=embeddings[j], payload=payload[j]) 
                for j in range(i, end)
            ]
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Đã upsert được {end}/{total} chunks.")
            
    def query(self, query_vector: list[float], limit: int = 5):
        """
        Truy vấn database.
        """
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
        ).points
        return results
