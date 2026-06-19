# ============================================================
#  Dockerfile — RAG Chatbot Thư viện Văn học Việt Nam
#  Tác giả: Cao Thị Khánh Chi — ĐATN 2025-2026
# ============================================================

# Base image: Python 3.10 slim để tối ưu kích thước
FROM python:3.10-slim

WORKDIR /app

# Cài đặt các dependencies hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Python dependencies trước (tận dụng Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy mã nguồn ứng dụng ──
COPY app.py .
COPY retrieval_qa.py .
COPY question_suggester.py .

# Copy các module nội bộ
COPY chunking/ ./chunking/
COPY search/ ./search/
COPY vector_store/ ./vector_store/

# Copy BM25 index (~25MB) vào image để tránh rebuild khi khởi động
# (BM25 index được build sẵn từ 333,082 documents văn học Việt Nam)
COPY data/bm25_index.pkl ./data/bm25_index.pkl

# ── Cổng Streamlit ──
EXPOSE 8501

# Healthcheck: đảm bảo container hoạt động bình thường
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# ── Lệnh khởi động ──
CMD ["python", "-m", "streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
