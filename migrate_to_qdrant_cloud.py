"""
migrate_to_qdrant_cloud.py - Di chuyển dữ liệu từ Qdrant Local sang Qdrant Cloud.
"""
import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

# Cấu hình
COLLECTION_NAME = "vn_literature"
VECTOR_SIZE = 384
DB_DIR = Path(__file__).parent / "data" / "vector_db"

def migrate():
    # 1. Kết nối Local
    logger.info(f"Đang kết nối tới Local DB tại: {DB_DIR}")
    local_client = QdrantClient(path=str(DB_DIR))
    
    # 2. Kết nối Cloud
    url = os.environ.get("QDRANT_URL")
    api_key = os.environ.get("QDRANT_API_KEY")
    
    if not url or not api_key:
        logger.error("Thiếu QDRANT_URL hoặc QDRANT_API_KEY trong file .env!")
        return

    logger.info(f"Đang kết nối tới Qdrant Cloud tại: {url}")
    cloud_client = QdrantClient(url=url, api_key=api_key, timeout=120)

    # 3. Nạp SẠCH: xoá collection cũ trên Cloud (nếu có) rồi tạo lại.
    #    Cần thiết vì chunk_id đã đổi sau dedup → upsert thường sẽ để lại điểm cũ lẫn lộn.
    if cloud_client.collection_exists(COLLECTION_NAME):
        logger.info(f"Xoá collection cũ '{COLLECTION_NAME}' trên Cloud để nạp sạch...")
        cloud_client.delete_collection(COLLECTION_NAME)
    logger.info(f"Tạo mới collection '{COLLECTION_NAME}' trên Cloud...")
    cloud_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )

    # 4. Lấy tổng số điểm để theo dõi tiến độ
    total_points = local_client.count(COLLECTION_NAME).count
    logger.info(f"Bắt đầu migrate {total_points} điểm...")

    # 5. Scroll và Upsert theo lô (batch nhỏ để tránh WriteTimeout trên kết nối chậm)
    batch_size = 100
    next_page_offset = None
    processed_count = 0
    start_time = time.time()

    while True:
        # Đọc dữ liệu từ Local
        records, next_page_offset = local_client.scroll(
            collection_name=COLLECTION_NAME,
            limit=batch_size,
            offset=next_page_offset,
            with_payload=True,
            with_vectors=True
        )

        if not records:
            break

        # Chuyển đổi Record sang PointStruct
        points = [
            PointStruct(
                id=record.id,
                vector=record.vector,
                payload=record.payload
            ) for record in records
        ]

        # Đẩy lên Cloud — retry với backoff khi WriteTimeout / lỗi mạng tạm thời
        for attempt in range(5):
            try:
                cloud_client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
                break
            except Exception as e:
                if attempt == 4:
                    logger.error(f"Upsert thất bại sau 5 lần tại điểm {processed_count}: {e}")
                    raise
                logger.warning(f"Upsert lỗi (thử lại {attempt+1}/5): {str(e)[:80]}")
                time.sleep(2 ** attempt * 2)

        processed_count += len(points)
        
        # In tiến độ mỗi 5000 điểm
        if processed_count % 5000 == 0 or next_page_offset is None:
            elapsed = time.time() - start_time
            speed = processed_count / elapsed if elapsed > 0 else 0
            percent = (processed_count / total_points) * 100 if total_points > 0 else 100
            logger.info(f"Tiến độ: {processed_count}/{total_points} ({percent:.1f}%) | Tốc độ: {speed:.1f} pts/s")

        if next_page_offset is None:
            break

    print(f"\n✅ Đã hoàn thành migrate {processed_count} điểm lên Qdrant Cloud!")
    logger.info(f"Tổng thời gian: {time.time() - start_time:.1f} giây.")

if __name__ == "__main__":
    migrate()
