import os
import json
import logging
from pathlib import Path
from datetime import datetime
import uuid

# Configuration
BASE_DIR = Path(__file__).parent
ARCHIVE_DIR = BASE_DIR / "data" / "archive" / "output"
OUT_DIR = BASE_DIR / "data" / "processed" / "archive"
LOG_FILE = BASE_DIR / "data" / "preprocess_archive.log"

def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )

logger = logging.getLogger(__name__)

def process_archive():
    if not ARCHIVE_DIR.exists():
        logger.error(f"Directory {ARCHIVE_DIR} does not exist.")
        return
        
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = list(ARCHIVE_DIR.glob("*.txt"))
    logger.info(f"Found {len(files)} files in {ARCHIVE_DIR}")
    
    processed_count = 0
    error_count = 0
    skipped_count = 0
    
    for file_path in files:
        try:
            filename = file_path.stem
            
            # Parse file format: "Title - Author"
            if " - " in filename:
                parts = filename.rsplit(" - ", 1)
                title = parts[0].strip()
                author = parts[1].strip()
            else:
                title = filename.strip()
                author = "Khuyết Danh"
                
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
                
            if not content or len(content) < 50:
                skipped_count += 1
                continue
                
            summary = content[:500] + "..." if len(content) > 500 else content
            
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"archive-{title}-{author}"))
            
            record = {
                "id": doc_id,
                "title": title,
                "author": author,
                "type": "work",
                "source": "archive",
                "summary": summary,
                "content": content,
                "language": "vi",
                "word_count": len(content.split()),
                "char_count": len(content),
                "processed_at": datetime.now().isoformat()
            }
            
            out_file = OUT_DIR / f"{doc_id}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
                
            processed_count += 1
            if processed_count % 1000 == 0:
                logger.info(f"Processed {processed_count} files...")
                
        except Exception as e:
            logger.warning(f"Error processing {file_path.name}: {e}")
            error_count += 1
            
    logger.info("="*50)
    logger.info(f"DONE PROCESSING ARCHIVE DATA")
    logger.info(f"Processed: {processed_count} files")
    logger.info(f"Skipped (too short): {skipped_count} files")
    logger.info(f"Errors: {error_count} files")
    logger.info("="*50)
    
if __name__ == "__main__":
    setup_logging()
    process_archive()
