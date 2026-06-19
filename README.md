# Chatbot Thư viện Điện tử Tiếng Việt (RAG)

Hệ thống chatbot hỏi–đáp văn học Việt Nam bằng tiếng Việt, sử dụng kiến trúc
**Retrieval-Augmented Generation (RAG)** với tìm kiếm lai hợp (BM25 + tìm kiếm
ngữ nghĩa), tái xếp hạng Cross-Encoder và mô hình sinh Gemini.

> Đồ án tốt nghiệp — Khoa Toán–Tin, Đại học Bách khoa Hà Nội.

## Kiến trúc

```
Người dùng → Streamlit UI → RetrievalQA
                               ├─ SearchPipeline: BM25 ∥ Vector → RRF → Cross-Encoder
                               ├─ Qdrant (vector store, HNSW)
                               └─ Gemini API (sinh câu trả lời + trích dẫn)
```

## Công nghệ

- **Giao diện & ứng dụng:** Streamlit (ứng dụng nguyên khối)
- **Truy hồi:** BM25 (`rank-bm25`) + Dense Retrieval (`sentence-transformers`,
  `paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều) hợp nhất bằng RRF (k=60)
- **Tái xếp hạng:** Cross-Encoder `ms-marco-MiniLM-L-6-v2`
- **Vector DB:** Qdrant (local hoặc Qdrant Cloud, độ đo cosine, chỉ mục HNSW)
- **Sinh câu trả lời:** Google Gemini (`gemini-2.5-flash`)

## Chạy cục bộ

```bash
pip install -r requirements.txt
```

Tạo file `.env` (KHÔNG commit):

```
GEMINI_API_KEY=AIza...
# Bỏ trống QDRANT_URL để dùng vector DB cục bộ trong data/vector_db
QDRANT_URL=
QDRANT_API_KEY=
```

Chạy ứng dụng:

```bash
streamlit run app.py
```

## Triển khai (Streamlit Community Cloud)

1. **Qdrant Cloud:** tạo cluster free, lấy `QDRANT_URL` + `QDRANT_API_KEY`, đặt
   vào `.env` rồi nạp dữ liệu lên cloud:
   ```bash
   python migrate_to_qdrant_cloud.py
   ```
2. **Streamlit Cloud:** New app → chọn repo + `app.py` → khai báo Secrets:
   ```toml
   GEMINI_API_KEY = "AIza..."
   QDRANT_URL     = "https://...qdrant.io"
   QDRANT_API_KEY = "..."
   ```
3. Deploy → nhận link `https://<app>.streamlit.app`.

## Cấu trúc thư mục

| Đường dẫn | Vai trò |
|---|---|
| `app.py` | Giao diện Streamlit |
| `retrieval_qa.py` | Lớp điều phối RAG (truy hồi + Gemini + chống ảo tưởng) |
| `search/` | BM25, hybrid search, RRF, Cross-Encoder reranker |
| `chunking/` | Mô hình nhúng (embedder) và phân mảnh |
| `vector_store/` | Kết nối Qdrant |
| `data/bm25_index.pkl` | Chỉ mục BM25 dựng sẵn |
| `build_knowledge_base.py` | Dựng lại kho tri thức (embed + nạp Qdrant + BM25) |
| `migrate_to_qdrant_cloud.py` | Sao chép vector DB cục bộ → Qdrant Cloud |
