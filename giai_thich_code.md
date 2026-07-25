# BẢN ĐỒ CODE & GIẢI THÍCH TỪNG FILE

> Dùng khi hội đồng yêu cầu mở code. Giải thích theo **luồng xử lý**, không theo alphabet.
> Mọi file đều có docstring tiếng Việt ở dòng đầu — quên thì mở ra đọc rồi diễn giải.

---

## 0. BẢN ĐỒ KIẾN TRÚC (đọc/vẽ khi được hỏi tổng quan)

### Kiến trúc runtime (khi người dùng hỏi 1 câu)

```
                        ┌─────────────────────────────┐
   Người dùng ────────► │  app.py  (Streamlit UI)     │
                        │  - khung chat, sidebar       │
                        │  - @st.cache_resource(engine)│
                        └──────────────┬──────────────┘
                                       │ gọi RetrievalQA.ask()
                                       ▼
        ┌──────────────────────────────────────────────────────┐
        │           retrieval_qa.py  (LỚP ĐIỀU PHỐI RAG)        │
        │  1. contextualize_query()  → viết lại câu nối tiếp     │
        │  2. fit_memory()           → quản ngân sách token      │
        │  3. retrieve()  ───────────┐                           │
        │  4. kiểm ngưỡng chống ảo tưởng (RRF < 0.003 → từ chối) │
        │  5. build_prompt() + GeminiClient.generate_stream()   │
        └───────────────────────────┬──────────────────────────┘
                                     │ (3) truy hồi
                                     ▼
        ┌──────────────────────────────────────────────────────┐
        │          search/search_pipeline.py  (NHẠC TRƯỞNG)     │
        │                                                        │
        │   BM25Retriever ─┐                                     │
        │  (bm25_index.pkl)│                                     │
        │                  ├─► reciprocal_rank_fusion (RRF k=60) │
        │   Vector search ─┘            │                        │
        │   (Embedder → Qdrant)         ▼                        │
        │                     CrossEncoderReranker (top-K)       │
        └───────┬───────────────────────────────┬──────────────┘
                │                                │
                ▼                                ▼
   chunking/embedder.py                vector_store/qdrant_client_app.py
   (câu hỏi → vector 384d)             (Qdrant Cloud / local, HNSW cosine)
                                                 │
                                                 ▼
                                    Gemini API (sinh câu trả lời + trích dẫn)
```

### Pipeline dữ liệu (offline, chạy một lần để dựng kho)

```
crawler/ ──► preprocess*.py ──► chunking/chunker.py ──► enrich_metadata_ai.py
(thu thập)    (làm sạch)          (phân mảnh)            (làm giàu năm/thể loại)
                                                              │
                                                              ▼
                                      build_knowledge_base.py (gộp + dedup + embed)
                                                              │
                            ┌─────────────────────────────────┼──────────────────┐
                            ▼                                  ▼                  ▼
                     data/bm25_index.pkl              Qdrant (local)     migrate_to_qdrant_cloud.py
                                                                          (→ Qdrant Cloud)
```

---

## NHÓM 1 — ỨNG DỤNG CHẠY TRỰC TUYẾN (dùng khi demo)

| File | Ý nghĩa chi tiết |
|------|------------------|
| **`app.py`** (~1000 dòng) | **Giao diện Streamlit**. Vẽ khung chat, sidebar (chọn chế độ truy hồi, bật/tắt rerank, Top-K, bộ nhớ, thanh ngân sách token), thẻ nguồn, xuất JSON, toàn bộ CSS theme. Dùng `@st.cache_resource` để **chỉ nạp model 1 lần** (embedder+reranker nặng). **Không chứa logic RAG** — chỉ gọi `RetrievalQA.ask()` rồi hiển thị. |
| **`retrieval_qa.py`** (~48KB) | **Trái tim hệ thống — lớp điều phối RAG.** Hai lớp: `GeminiClient` (bọc API Gemini: `generate`, `generate_stream`, có `_safe_text` chống response rỗng) và `RetrievalQA` (điều phối toàn luồng). Method chính: `build()` (factory), `contextualize_query()` (viết lại câu nối tiếp), `fit_memory()`/`summarize_history()` (bộ nhớ + ngân sách 20.000 token, tự tóm tắt ở 75%), `retrieve()`, `ask()` (hàm chính: viết lại → truy hồi → kiểm ngưỡng chống ảo tưởng → dựng prompt → gọi Gemini), `peek_cache`/`store_cache` (cache câu trả lời), `ask_no_rag()` (trả lời không RAG để so sánh). |
| **`question_suggester.py`** | **`QuestionSuggester`** — sau mỗi câu trả lời, gọi Gemini sinh 1–5 câu hỏi gợi ý tiếp theo dựa trên (câu hỏi + ngữ cảnh + câu trả lời). Tính năng UX trong sidebar. |
| **`utils/download_utils.py`** | Tự **tải `bm25_index.pkl` / vector DB từ link** khi triển khai Cloud (máy chủ không có sẵn file lớn, không đưa vào git). Chỉ tải khi file chưa tồn tại. |

### Gói `search/` — truy hồi (nhóm quan trọng nhất khi giải thích thuật toán)

| File | Ý nghĩa chi tiết |
|------|------------------|
| **`search/search_pipeline.py`** | **Nhạc trưởng truy hồi.** Lớp `SearchPipeline` + `PipelineConfig`: nhận query → chạy BM25 + Vector → hợp nhất RRF → Cross-Encoder rerank → trả top-K. Đây là file ghép mọi thành phần truy hồi. |
| **`search/bm25_retriever.py`** | **`BM25Retriever`** — tìm kiếm **từ khóa** (thư viện `rank-bm25`), có `_tokenize_vi()` tách từ tiếng Việt. Chỉ mục dựng sẵn lưu ở `data/bm25_index.pkl` (26MB). Mạnh với tên riêng/tên tác phẩm. |
| **`search/hybrid_search.py`** | Hàm **`reciprocal_rank_fusion()`** — hợp nhất 2 danh sách theo công thức RRF: điểm = Σ 1/(k+hạng), **k=60**. Lớp `HybridSearch` chạy BM25 + vector song song rồi trộn. Không cần chuẩn hóa điểm giữa 2 thang khác nhau. |
| **`search/reranker.py`** | **`CrossEncoderReranker`** — nạp `ms-marco-MiniLM-L-6-v2`, chấm điểm lại từng cặp (câu hỏi, đoạn) trong top kết quả. Chính xác hơn Bi-Encoder nhưng chậm → chỉ áp cho top nhỏ. |
| **`search/evaluator.py`** | Tính **Precision@K, Recall@K, MRR** (`QueryMetrics`, `EvaluationReport`, `Evaluator`). Cơ sở số liệu Chương 5. |
| **`search/test_queries.py`** | **Bộ 30 câu hỏi có nhãn** (FACTUAL/AUTHOR/SEMANTIC) + từ khóa đáp án, để auto-đánh giá. |

### Gói `chunking/` & `vector_store/`

| File | Ý nghĩa chi tiết |
|------|------------------|
| **`chunking/embedder.py`** | **`Embedder`** — bọc sentence-transformers, biến văn bản → **vector 384 chiều**. Model thực dùng: `paraphrase-multilingual-MiniLM-L12-v2` (`FAST_MODEL`). Dùng cả lúc index (offline) lẫn truy vấn (online). Có `NumpyRetriever` (tìm cosine đơn giản, dùng thử nghiệm). |
| **`chunking/chunker.py`** | **`Chunker`** + `TextChunk` — các chiến lược **phân mảnh** văn bản (theo đoạn/câu/cửa sổ trượt, có overlap). `compare_strategies()` để chọn chiến lược qua thực nghiệm. |
| **`chunking/experiment.py`** | Thực nghiệm so sánh các chiến lược chunking — cơ sở chọn tham số hiện tại. |
| **`vector_store/qdrant_client_app.py`** | **`QdrantManager`** — kết nối Qdrant. Nếu `.env` có `QDRANT_URL` → Qdrant Cloud; nếu trống → DB local `data/vector_db`. Collection `vn_literature`, **cosine, chỉ mục HNSW**. Thể hiện "một code chạy cả local lẫn cloud". |
| **`vector_store/chroma_client.py`** | Kết nối **ChromaDB** — vector DB của **phiên bản đầu**, sau chuyển sang Qdrant. Giữ lại làm bằng chứng thực nghiệm công nghệ. |

---

## NHÓM 2 — XÂY KHO TRI THỨC (script offline, chạy một lần)

| File | Ý nghĩa chi tiết |
|------|------------------|
| **`build_knowledge_base.py`** | **Script tổng dựng kho.** `get_merged_documents()` gộp tài liệu mọi nguồn, **khử trùng lặp** (chuẩn hóa tiêu đề, gộp tên tác giả đảo), tiêm metadata (năm/thể loại/NXB) vào từng chunk, embed rồi nạp Qdrant + dựng BM25 index. Kết quả: **11.759 chunk**. `reset_databases()` xóa làm lại. |
| **`preprocess.py`** | **Tiền xử lý dữ liệu Wikipedia thô** → `data/processed/`: bỏ markup (`clean_content`), phân loại bản ghi (`classify_type`), lọc thể loại (`filter_categories`), dựng tóm tắt (`rebuild_summary`). |
| **`preprocess_archive.py`, `preprocess_archive_compact.py`** | Tiền xử lý cho nguồn **archive** (vnthuquan) — file .txt "Tên - Tác giả". |
| **`preprocess_gbooks.py`** | Tiền xử lý cho nguồn **Google Books**. |
| **`generate_archive_summaries.py`** | Sinh **tóm tắt** cho tác phẩm dài bằng Gemini (phục vụ chunk mức tóm tắt). |
| **`process_embeddings.py`** | Tính embedding hàng loạt cho các chunk (bước embed tách riêng). |
| **`load_to_qdrant.py`, `load_to_chroma.py`** | Nạp vector + payload vào Qdrant / Chroma. |
| **`migrate_to_qdrant_cloud.py`** | **Sao chép DB local → Qdrant Cloud** — có resume (bỏ qua điểm đã nạp) + retry backoff (free tier hay timeout). Hàm `migrate(fresh=False)`. |
| **`crawler/`** (16 file) | **Bộ thu thập dữ liệu.** `vnthuquan_crawler.py` + `wiki_crawler*.py` + `gbooks_crawler.py` cào từng nguồn; `extractor.py` bóc nội dung; `storage*.py` lưu; `models*.py` định nghĩa cấu trúc; `config*.py` cấu hình; `main*.py` điểm chạy. Kết quả → `data/archive`, `data/raw`. |

---

## NHÓM 3 — LÀM GIÀU & KIỂM ĐỊNH DỮ LIỆU

| File | Ý nghĩa chi tiết |
|------|------------------|
| **`enrich_metadata_ai.py`** | **Làm giàu metadata bằng Gemini + Google Search Grounding** — điền năm/thể loại/NXB còn thiếu. Có giới hạn quota/ngày, resume khi lỗi, `build_prompt`/`parse_json`/`enrich_one`. |
| **`enrich_offline.py`** | Làm giàu từ **Wikidata** (offline) — chỉ điền ô trống, không ghi đè. |
| **`audit_coverage.py`** | Đối chiếu kho với danh mục tác phẩm kinh điển → **độ phủ ~89%** (`data/coverage_audit.json`). |
| **`report_stats.py`** | Sinh **bảng thống kê** (fill-rate trước/sau enrich, phân bố thể loại) dạng LaTeX cho báo cáo. |
| **`export_books_csv.py` / `import_books_csv.py`** | Xuất metadata ra CSV để rà tay, rồi nhập lại. |
| **`export_excel.py`** | Xuất dữ liệu ra Excel để kiểm tra. |
| **`check_data_quality.py`, `check_gbooks_stats.py`** | Kiểm tra chất lượng dữ liệu / thống kê nguồn Google Books. |
| **`clean_annotations.py`, `fix_and_update_glossary.py`, `fix_pyrefly.py`** | Script **dọn dẹp/sửa một lần** trong quá trình làm — "công cụ tiện ích, không thuộc hệ thống chạy". |

---

## NHÓM 4 — ĐÁNH GIÁ & CÔNG CỤ DÒNG LỆNH

| File | Ý nghĩa chi tiết |
|------|------------------|
| **`evaluate_search.py`** | **Chạy đánh giá đầy đủ** 4 chế độ (bm25/vector/hybrid/hybrid+rerank) trên 30 câu, in bảng so sánh → `data/evaluation_results/`. Số liệu Chương 5 (**P@1 hybrid 83,3%, MRR 0,887**) lấy từ đây. |
| **`run_search.py`** | Công cụ **thử truy hồi nhanh** trên dòng lệnh khi phát triển (không dùng trong app). |
| **`query_qdrant.py`, `query_chroma.py`** | Truy vấn nhanh Qdrant/Chroma để kiểm tra DB. |

---

## KỊCH BẢN 60 GIÂY: "Giải thích luồng code khi tôi gõ một câu hỏi"

Đọc thuộc — câu khả năng cao nhất:

1. "`app.py` nhận câu hỏi, gọi `RetrievalQA.ask()` trong `retrieval_qa.py`."
2. "`ask()` gọi `contextualize_query()` — nếu bật bộ nhớ, câu hỏi được viết lại đầy đủ dựa trên lịch sử; `fit_memory()` quản ngân sách token."
3. "Sau đó `SearchPipeline` (`search/search_pipeline.py`): câu hỏi được `Embedder` mã hóa thành vector 384 chiều tìm trong **Qdrant**, đồng thời `BM25Retriever` tìm theo từ khóa; hai danh sách trộn bằng `reciprocal_rank_fusion()` (k=60), rồi `CrossEncoderReranker` sắp lại top."
4. "Về `ask()`: nếu điểm cao nhất < ngưỡng 0.003 → **từ chối**; ngược lại 5 đoạn tốt nhất vào prompt cùng quy tắc 'chỉ dùng ngữ cảnh', gọi `GeminiClient.generate_stream()` sinh câu trả lời kèm trích dẫn, hiển thị dần."

---

## MẸO ỨNG XỬ

- Bị chỉ file **ChromaDB cũ** (`load_to_chroma.py`, `query_chroma.py`, `vector_store/chroma_client.py`) → "phiên bản đầu dùng Chroma, sau chuyển Qdrant vì payload filter tốt hơn + có bản cloud free + HNSW ổn định. Em giữ code cũ làm bằng chứng thực nghiệm." → biến file thừa thành **điểm cộng**.
- Bị chỉ script **rác** (`check_*.py`, `fix_*.py`) → "script tiện ích một lần để tái lập kết quả", không xin lỗi.
- Bị bắt mở `retrieval_qa.py` (file to nhất): cuộn thẳng tới `def ask()` (~dòng 745) và 2 hằng số `RELEVANCE_THRESHOLD`/`LOW_CONF_THRESHOLD` (~dòng 63) — 2 chỗ "đắt" nhất.
- Bị hỏi có **2 model embedder** (`intfloat/multilingual-e5-base` vs MiniLM) → "e5-base là default class nhưng **KHÔNG dùng**; `RetrievalQA.build()` ghi đè bằng `FAST_MODEL` = MiniLM 384 chiều. Em chọn MiniLM vì nhẹ/nhanh, đủ chất lượng (P@1 83%)."
