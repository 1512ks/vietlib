"""
download_utils.py -- Tiện ích tải tài nguyên lớn (BM25 Index, Vector DB) từ URL link.
"""

import os
import shutil
import urllib.request
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def download_file(url: str, dest_path: Path) -> bool:
    """
    Tải một file từ URL về dest_path. Hỗ trợ chuyển đổi link Google Drive share sang direct link.
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Chuẩn hóa link Google Drive
    if "drive.google.com" in url and "file/d/" in url:
        try:
            file_id = url.split("file/d/")[1].split("/")[0]
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
            logger.info(f"Đã phát hiện link Google Drive, chuyển đổi sang direct link: {url}")
        except Exception as e:
            logger.warning(f"Không thể phân tích link Google Drive: {e}")
            
    try:
        logger.info(f"Đang tải dữ liệu từ {url}...")
        logger.info(f"Ghi file ra: {dest_path}")
        
        # Thiết lập header User-Agent để tránh bị một số host chặn
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
            
        logger.info(f"Tải thành công! Kích thước file: {dest_path.stat().size_bytes / 1024 / 1024:.2f} MB")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi tải file từ link {url}: {e}")
        return False

def download_and_extract_zip(url: str, extract_dir: Path) -> bool:
    """
    Tải file zip từ URL và giải nén vào thư mục chỉ định.
    """
    extract_dir = Path(extract_dir)
    temp_zip = extract_dir.parent / "temp_download.zip"
    
    if download_file(url, temp_zip):
        try:
            logger.info(f"Đang giải nén {temp_zip} vào {extract_dir}...")
            extract_dir.mkdir(parents=True, exist_ok=True)
            shutil.unpack_archive(temp_zip, extract_dir)
            temp_zip.unlink() # Xóa file zip tạm
            logger.info(f"Giải nén thành công!")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi giải nén file zip: {e}")
            if temp_zip.exists():
                temp_zip.unlink()
            return False
    return False

def check_and_download_resources():
    """
    Kiểm tra và tải tự động các tài nguyên lớn (BM25 Index, Vector DB)
    nếu cấu hình URL có sẵn và file chưa tồn tại cục bộ.
    """
    # 1. Kiểm tra BM25 Index
    bm25_path = Path("data/bm25_index.pkl")
    bm25_url = os.environ.get("BM25_INDEX_URL")
    
    if not bm25_path.exists() and bm25_url:
        logger.info("Không tìm thấy file bm25_index.pkl cục bộ. Tiến hành tải bằng link...")
        download_file(bm25_url, bm25_path)
    elif bm25_path.exists():
        logger.info("File bm25_index.pkl đã tồn tại cục bộ.")
        
    # 2. Kiểm tra Vector DB (chỉ dùng khi không có QDRANT_URL/QDRANT_API_KEY)
    qdrant_url = os.environ.get("QDRANT_URL")
    qdrant_key = os.environ.get("QDRANT_API_KEY")
    
    if not (qdrant_url and qdrant_key):
        # Chế độ chạy offline/local storage
        vector_db_dir = Path("data/vector_db")
        vector_db_url = os.environ.get("VECTOR_DB_URL")
        
        # Kiểm tra xem thư mục database có rỗng hoặc không tồn tại không
        db_empty = not vector_db_dir.exists() or not any(vector_db_dir.iterdir())
        
        if db_empty and vector_db_url:
            logger.info("Chế độ Local DB hoạt động nhưng không có dữ liệu. Tiến hành tải bằng link...")
            download_and_extract_zip(vector_db_url, vector_db_dir)
        elif not db_empty:
            logger.info("Thư mục Vector DB cục bộ đã có sẵn dữ liệu.")
