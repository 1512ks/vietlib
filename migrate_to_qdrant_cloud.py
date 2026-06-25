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

def migrate(fresh=False):
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
    # check_compatibility=False: bỏ lệnh gọi kiểm tra phiên bản lúc init (hay treo trên mạng chậm)
    cloud_client = QdrantClient(url=url, api_key=api_key, timeout=120, check_compatibility=False)

    # 3. Chuẩn bị collection.
    #   --fresh: xoá + tạo lại (nạp sạch tuyệt đối).
    #   Mặc định: nếu đã có thì GIỮ để RESUME (bỏ qua điểm đã nạp) — tránh nạp lại từ đầu khi bị ngắt.
    exists = cloud_client.collection_exists(COLLECTION_NAME)
    if fresh and exists:
        logger.info(f"[--fresh] Xoá collection cũ '{COLLECTION_NAME}'...")
        cloud_client.delete_collection(COLLECTION_NAME)
        exists = False
    if not exists:
        logger.info(f"Tạo mới collection '{COLLECTION_NAME}' trên Cloud...")
        cloud_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )

    # Resume: lấy danh sách id đã có trên Cloud để bỏ qua (không nạp lại)
    existing_ids = set()
    if exists:
        off = None
        while True:
            recs, off = cloud_client.scroll(COLLECTION_NAME, limit=2000, offset=off,
                                            with_payload=False, with_vectors=False)
            existing_ids.update(r.id for r in recs)
            if off is None:
                break
        logger.info(f"Resume: Cloud đã có {len(existing_ids):,} điểm → sẽ bỏ qua các điểm này.")

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

        # Chuyển đổi Record sang PointStruct (bỏ qua điểm đã có trên Cloud khi resume)
        points = [
            PointStruct(id=record.id, vector=record.vector, payload=record.payload)
            for record in records if record.id not in existing_ids
        ]

        if not points:
            processed_count += len(records)
            if next_page_offset is None:
                break
            continue

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
    import argparse
    ap = argparse.ArgumentParser(description="Migrate Qdrant Local -> Cloud (resume được).")
    ap.add_argument("--fresh", action="store_true",
                    help="Xoá + tạo lại collection trên Cloud (nạp sạch). Mặc định: resume.")
    args = ap.parse_args()
    migrate(fresh=args.fresh)
