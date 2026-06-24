"""
retrieval_qa.py -- RetrievalQA: Ket noi Search Pipeline voi Gemini API.

Flow:
    User Query
        -> SearchPipeline (BM25 + Qdrant + Reranker)
        -> Top-K Context Chunks
        -> Prompt Builder
        -> Gemini API
        -> Cau tra loi + Citations

Cach dung:
    python retrieval_qa.py
    python retrieval_qa.py "Tom tat truyen Chi Pheo cua Nam Cao"
    python retrieval_qa.py "..." --no-rerank
    python retrieval_qa.py "..." --no-rag

Yeu cau:
    pip install google-generativeai python-dotenv
    Dat GEMINI_API_KEY trong file .env hoac bien moi truong.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

# Fix Unicode encoding tren Windows console (tranh UnicodeEncodeError voi emoji/tieng Viet)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Cho phep import cac module trong thu muc goc
sys.path.insert(0, str(Path(__file__).parent))

# Load .env neu co (pip install python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================
#  Cấu hình
# ============================================================
GEMINI_MODEL    = "gemini-2.5-flash"   # gemini-2.5-flash: nhanh, miễn phí, chất lượng cao
TOP_K_CONTEXT   = 5                    # Số context chunks đưa vào prompt
MAX_CONTEXT_LEN = 800                  # Ký tự tối đa mỗi chunk (tránh vượt token limit)
RELEVANCE_THRESHOLD = 0.003            # RRF score tối thiểu — dưới ngưỡng này coi là out-of-corpus
LOW_CONF_THRESHOLD  = 0.006            # Dưới ngưỡng này: cảnh báo trong prompt là “thông tin có thể không chính xác”
SEARCH_POOL_MAX     = 1000             # Giới hạn số đầu sách lưu trong cache search (pool tích lũy)
MERGE_RERANK_CAP    = 60               # Số candidate tối đa đưa vào cross-encoder khi gộp pool (chặn latency)


# ============================================================
#  Prompt Builder
# ============================================================
SYSTEM_PROMPT = """\
Bạn là **Trợ lý Thư viện Văn học Việt Nam** — một chuyên gia am hiểu sâu sắc về văn học Việt Nam từ cổ điển đến đương đại.

## Nhiệm vụ
Trả lời câu hỏi của người dùng DỰA TRÊN các đoạn văn bản được cung cấp trong phần [NGỮ CẢNH].

## Quy tắc bắt buộc

1. **Chỉ dùng thông tin từ NGỮ CẢNH**: Không bịa đặt hay thêm bất kỳ thông tin nào ngoài context được cung cấp. Nếu người dùng hỏi về tác phẩm/tác giả KHÔNG xuất hiện trong [NGỮ CẢNH], hãy trả lời ĐÚNG theo mẫu này và KHÔNG đề cập tên tác phẩm/nhân vật đó: "Tôi không tìm thấy thông tin về [chủ đề này] trong thư viện của chúng tôi. Thư viện hiện tập trung vào văn học Việt Nam và các tác phẩm dịch phổ biến tại Việt Nam."

2. **Trả lời bằng tiếng Việt**, rõ ràng, súc tích (tối đa 300 từ trừ khi được yêu cầu chi tiết hơn). Dùng đầu mục hoặc danh sách khi trình bày nhiều tác phẩm/tác giả.

3. **Bắt buộc trích dẫn nguồn**: Cuối mỗi câu trả lời, liệt kê các tài liệu đã dùng theo định dạng:
   > 📚 **Nguồn tham khảo:**
   > [1] *Tên tác phẩm* — Tác giả
   > [2] *Tên tác phẩm* — Tác giả

4. **Xử lý câu hỏi cảm xúc/ẩn dụ**: Nếu người dùng hỏi theo cảm xúc (ví dụ: "sách buồn", "câu chuyện về hy vọng"), hãy diễn giải nhu cầu trước rồi gợi ý tác phẩm phù hợp từ context.

5. **Không suy diễn quá mức**: Chỉ khẳng định điều được nêu rõ trong context. Nếu không chắc, dùng cụm "Theo tài liệu tham khảo, có thể...".

6. **Thân thiện và chuyên nghiệp**: Dùng ngôn ngữ lịch sự, phù hợp với độc giả yêu văn học. Khuyến khích đọc sách khi phù hợp.

## Nhận diện & Đánh dấu Tác phẩm Kinh điển

Khi đề cập hoặc gợi ý bất kỳ tác phẩm nào thuộc danh sách sau, hãy thêm nhãn **⭐ Kinh điển** ngay sau tên tác phẩm.
Ví dụ: *Truyện Kiều* ⭐ Kinh điển — Nguyễn Du.

### Danh sách tác phẩm kinh điển Văn học Việt Nam (đã được công nhận rộng rãi)

**Văn học cổ điển (trước 1900):**
Truyện Kiều (Nguyễn Du), Chinh phụ ngâm (Đặng Trần Côn / Đoàn Thị Điểm dịch),
Cung oán ngâm khúc (Nguyễn Gia Thiều), Lục Vân Tiên (Nguyễn Đình Chiểu),
Văn tế nghĩa sĩ Cần Giuộc (Nguyễn Đình Chiểu), Quốc âm thi tập (Nguyễn Trãi),
Bình Ngô đại cáo (Nguyễn Trãi), Truyền kỳ mạn lục (Nguyễn Dữ),
Hoàng Lê nhất thống chí (Ngô gia văn phái), Thượng kinh ký sự (Lê Hữu Trác),
Vũ trung tùy bút (Phạm Đình Hổ), Đoạn trường tân thanh (Nguyễn Du).

**Văn xuôi hiện đại 1930–1945 (kinh điển):**
Số đỏ (Vũ Trọng Phụng), Giông tố (Vũ Trọng Phụng), Tắt đèn (Ngô Tất Tố),
Chí Phèo (Nam Cao), Lão Hạc (Nam Cao), Đời thừa (Nam Cao), Sống mòn (Nam Cao),
Bỉ vỏ (Nguyên Hồng), Những ngày thơ ấu (Nguyên Hồng),
Bước đường cùng (Nguyễn Công Hoan), Kép Tư Bền (Nguyễn Công Hoan),
Lều chõng (Ngô Tất Tố), Trúng số độc đắc (Vũ Trọng Phụng), Làm đĩ (Vũ Trọng Phụng),
Đoạn tuyệt (Nhất Linh), Lạnh lùng (Nhất Linh), Đôi bạn (Nhất Linh),
Nửa chừng xuân (Khái Hưng), Hồn bướm mơ tiên (Khái Hưng), Gánh hàng hoa (Khái Hưng & Nhất Linh), Trống mái (Khái Hưng),
Hai đứa trẻ (Thạch Lam), Gió đầu mùa (Thạch Lam), Gió lạnh đầu mùa (Thạch Lam), Dưới bóng hoàng lan (Thạch Lam),
Dế mèn phiêu lưu ký (Tô Hoài), Đất rừng phương Nam (Đoàn Giỏi),
Hà Nội băm sáu phố phường (Thạch Lam), Quê mẹ (Thanh Tịnh), Tôi đi học (Thanh Tịnh).

**Thơ Mới 1930–1945 (kinh điển):**
Thơ thơ (Xuân Diệu), Gửi hương cho gió (Xuân Diệu),
Lửa thiêng (Huy Cận), Vũ trụ ca (Huy Cận),
Mấy vần thơ (Thế Lữ), Điêu tàn (Chế Lan Viên),
Tiếng thu (Lưu Trọng Lư), Đau thương (Hàn Mặc Tử),
Thơ say (Vũ Hoàng Chương), Lỡ bước sang ngang (Nguyễn Bính), Tâm hồn tôi (Nguyễn Bính).

**Văn học kháng chiến & cách mạng 1945–1975 (kinh điển):**
Nhật ký trong tù (Hồ Chí Minh), Từ ấy (Tố Hữu), Việt Bắc (Tố Hữu), Ra trận (Tố Hữu),
Tây Tiến (Quang Dũng), Đồng chí (Chính Hữu), Bên kia sông Đuống (Hoàng Cầm),
Đất nước đứng lên (Nguyên Ngọc), Rừng xà nu (Nguyễn Trung Thành),
Mảnh trăng cuối rừng (Nguyễn Minh Châu), Dấu chân người lính (Nguyễn Minh Châu),
Hòn Đất (Anh Đức), Người mẹ cầm súng (Nguyễn Thi),
Vợ chồng A Phủ (Tô Hoài), Vợ nhặt (Kim Lân), Làng (Kim Lân),
Mùa lạc (Nguyễn Khải), Chiếc lược ngà (Nguyễn Quang Sáng).

**Văn học sau 1975 được công nhận là kinh điển:**
Nỗi buồn chiến tranh (Bảo Ninh), Thời xa vắng (Lê Lựu),
Mùa lá rụng trong vườn (Ma Văn Kháng), Đám cưới không có giấy giá thú (Ma Văn Kháng),
Những thiên đường mù (Dương Thu Hương), Bên không có chồng (Dương Hướng),
Tướng về hưu (Nguyễn Huy Thiệp), Không có vua (Nguyễn Huy Thiệp),
Cánh đồng bất tận (Nguyễn Ngọc Tư), Gào thét (Nguyễn Ngọc Tư).

### Danh sách tác phẩm kinh điển Văn học Thế giới (được dịch sang tiếng Việt phổ biến)

**Văn học Anh:**
Kiêu hãnh và định kiến (Jane Austen, 1813), Lý trí và tình cảm (Jane Austen, 1811), Thuyết phục (Jane Austen, 1818),
Jane Eyre (Charlotte Brontë, 1847), Đỉnh gió hú (Emily Brontë, 1847),
Những kỳ vọng lớn lao (Charles Dickens, 1860), Hai kinh thành (Charles Dickens, 1859),
Bleak House (Charles Dickens, 1853), David Copperfield (Charles Dickens, 1849), Giáng sinh yêu thương (Charles Dickens, 1843),
Middlemarch (George Eliot, 1871), Người Thợ Dệt Ở Raveloe (George Eliot, 1861), The Mill on the Floss (George Eliot, 1860),
Hội chợ phù hoa (William Makepeace Thackeray, 1847),
Tess - Một tâm hồn trong trắng (Thomas Hardy, 1891), Trở lại cố hương (Thomas Hardy, 1878),
Chân dung của Dorian Gray (Oscar Wilde, 1891),
Rebecca (Daphne du Maurier, 1938), Thăm lại Brideshead (Evelyn Waugh, 1945), Scoop (Evelyn Waugh, 1938),
Bà Dalloway (Virginia Woolf, 1925), Đến ngọn hải đăng (Virginia Woolf, 1927), Orlando (Virginia Woolf, 1928),
Lady Chatterley's Lover (D.H. Lawrence, 1960), Heart of Darkness (Joseph Conrad, 1902),
Of Human Bondage (Somerset Maugham, 1915), The Razor's Edge (Somerset Maugham, 1944),
North and South (Elizabeth Gaskell, 1854), The Woman in White (Wilkie Collins, 1860),
The Go-Between (L.P. Hartley, 1953), The Sea The Sea (Iris Murdoch, 1978),
Barchester Towers (Anthony Trollope, 1857), The Forsyte Saga (John Galsworthy, 1922),
Gió qua rặng liễu (Kenneth Grahame, 1908), Khu vườn bí mật (Frances Hodgson Burnett, 1911),
Những người phụ nữ bé nhỏ (Louisa May Alcott, 1868), Frankenstein (Mary Shelley, 1823),
Lark Rise to Candleford (Flora Thompson, 1939), Diary of a Nobody (George & Weedon Grossmith, 1892),
Love in a Cold Climate (Nancy Mitford, 1949), The Chrysalids (John Wyndham, 1955),
I Capture The Castle (Dodie Smith, 1948), The Code of the Woosters (P.G. Wodehouse, 1938),
Chuyện người tùy nữ (Margaret Atwood, 1985), Cỗ máy thời gian (H.G. Wells, 1895),
Bá tước Dracula (Bram Stoker, 1897), Wide Sargasso Sea (Jean Rhys, 1966),
Staying On (Paul Scott, 1977), Người Mỹ trầm lặng (Graham Greene, 1955).

**Văn học Mỹ:**
Giết con chim nhại (Harper Lee, 1960), Đại gia Gatsby (F. Scott Fitzgerald, 1925),
Máu lạnh (Truman Capote, 1965), Bắt trẻ đồng xanh (J.D. Salinger, 1951),
Yêu dấu (Toni Morrison, 1987), Tôi biết tại sao chim trong lồng vẫn hót (Maya Angelou, 1969),
Chùm nho thịnh nộ (John Steinbeck, 1939), Phía đông vườn địa đàng (John Steinbeck, 1952),
Tôi Charley và hành trình nước Mỹ (John Steinbeck, 1962),
Moby-Dick (Herman Melville, 1851), Ulysses (James Joyce, 1922), Chân dung chàng nghệ sĩ (James Joyce, 1916),
Những cuộc phiêu lưu của Huckleberry Finn (Mark Twain, 1884),
Bay trên tổ chim cúc cu (Ken Kesey, 1962), 1984 (George Orwell, 1949),
Bẫy 22 (Joseph Heller, 1961), Atlas vươn mình (Ayn Rand, 1957),
Another Country (James Baldwin, 1962), Căn phòng của Giovanni (James Baldwin, 1956),
The Secret History (Donna Tartt, 1992), Lolita (Vladimir Nabokov, 1955),
Bố già (Mario Puzo, 1969), A Confederacy of Dunces (John Kennedy Toole, 1980),
Ngựa chứng đầu xanh (S.E. Hinton, 1967), Thời thơ ngây (Edith Wharton, 1920),
Tropic of Cancer (Henry Miller, 1934), Tiếng gọi của hoang dã (Jack London, 1903).

**Văn học Pháp:**
Những người khốn khổ (Victor Hugo, 1862), Bá tước Monte Cristo (Alexandre Dumas, 1844),
Bà Bovary (Gustave Flaubert, 1857).

**Văn học Nga:**
Tội ác và hình phạt (Fyodor Dostoevsky, 1866), Anh em nhà Karamazov (Dostoevsky, 1880), Đêm trắng (Dostoevsky, 1848),
Chiến tranh và hòa bình (Leo Tolstoy, 1867), Anna Karenina (Leo Tolstoy, 1878),
Nghệ nhân và Margarita (Mikhail Bulgakov, 1966),
Một ngày trong đời Ivan Denisovich (Alexander Solzhenitsyn, 1962).

**Văn học Tây Ban Nha & Mỹ Latinh:**
Don Quixote (Miguel Cervantes, 1605), Trăm năm cô đơn (Gabriel García Márquez, 1967).

**Văn học Đức & các nước khác:**
Thế giới mới nhiệm màu (Aldous Huxley, 1932), Gia đình Buddenbrook (Thomas Mann, 1901),
Mùi hương (Patrick Süskind, 1985), Lâu đài (Franz Kafka, 1926),
I Claudius (Robert Graves, 1934), The Betrothed (Alessandro Manzoni, 1827).

**Văn học cổ đại & khác:**
Iliad (Homer, thế kỷ 8 TCN), Binh pháp Tôn Tử (Tôn Tử),
Quê hương tan rã (Chinua Achebe, 1958), Chúa tể những chiếc nhẫn (J.R.R. Tolkien, 1954).

## Ưu tiên gợi ý theo loại câu hỏi

- **Câu hỏi học thuật** (nghiên cứu, phân tích, phong trào, giai đoạn, so sánh): Ưu tiên tác phẩm ⭐ Kinh điển trước, sau đó mới đến đương đại.
- **Câu hỏi cảm xúc/giải trí** (sách buồn, sách vui, đọc thư giãn, thất tình...): Gợi ý cân bằng giữa kinh điển và đương đại tùy tâm trạng.
- **Câu hỏi theo tác giả cụ thể**: Liệt kê đầy đủ tất cả tác phẩm trong context, đánh dấu ⭐ nếu là kinh điển.
- **Câu hỏi "sách hay nhất", "nên đọc gì đầu tiên"**: Ưu tiên tác phẩm ⭐ Kinh điển, giải thích giá trị văn học ngắn gọn.
"""



def build_prompt(query: str, contexts: List[dict], low_confidence: bool = False) -> str:
    """
    Xây dựng prompt RAG từ query và danh sách context chunks.

    Args:
        query          : Câu hỏi người dùng
        contexts       : List[dict] với các key: text, title, author, source_idx
        low_confidence : True nếu relevance score thấp, thêm cảnh báo vào prompt

    Returns:
        Chuỗi prompt hoàn chỉnh gửi cho Gemini
    """
    context_block = ""
    for ctx in contexts:
        title  = ctx.get("title", "Không rõ")
        author = ctx.get("author", "Không rõ")
        text   = ctx.get("text", "")[:MAX_CONTEXT_LEN]
        idx    = ctx.get("source_idx", "?")
        context_block += (
            f"\n--- Nguồn [{idx}] ---\n"
            f"Tài liệu: {title} | Tác giả: {author}\n"
            f"{text}\n"
        )

    # Cảnh báo khi confidence thấp — LLM phải từ chối quyết đoán hơn
    confidence_note = ""
    if low_confidence:
        confidence_note = (
            "\n[CẢNH BÁO HỆ THỐNG]: Các tài liệu dưới đây có mức liên quan THẤP với câu hỏi. "
            "Nếu không tìm thấy thông tin trực tiếp, hãy từ chối rõ ràng và KHÔNG đề cập "
            "tên tác phẩm, nhân vật hoặc nội dung nào không xuất hiện trong các nguồn.\n"
        )

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"=== [NGỮ CẢNH] — CÁC ĐOẠN VĂN BẢN LIÊN QUAN ==={confidence_note}\n"
        f"{context_block}\n"
        f"=== CÂU HỎI ===\n"
        f"{query}\n\n"
        f"=== CÂU TRẢ LỜI ==="
    )
    return prompt


# ============================================================
#  Gemini Client
# ============================================================
class GeminiClient:
    """Wrapper đơn giản cho Gemini GenerativeAI API."""

    def __init__(self, api_key: Optional[str] = None, model: str = GEMINI_MODEL):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "Thiếu thư viện google-generativeai.\n"
                "Cài đặt: pip install google-generativeai"
            )

        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            raise ValueError(
                "Không tìm thấy GEMINI_API_KEY.\n"
                "Hãy đặt biến môi trường hoặc tạo file .env với:\n"
                "  GEMINI_API_KEY=your_api_key_here"
            )

        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        """Gọi Gemini API và trả về văn bản phản hồi."""
        response = self.model.generate_content(
            prompt,
            generation_config={"temperature": temperature},
        )
        return response.text.strip()

    def generate_stream(self, prompt: str, temperature: float = 0.2):
        """Gọi Gemini API ở chế độ streaming — yield từng đoạn text khi sẵn sàng.

        Giảm mạnh độ trễ cảm nhận: chữ hiện dần thay vì chờ toàn bộ câu trả lời.
        """
        response = self.model.generate_content(
            prompt,
            generation_config={"temperature": temperature},
            stream=True,
        )
        for chunk in response:
            text = getattr(chunk, "text", "")
            if text:
                yield text


# ============================================================
#  RetrievalQA Engine
# ============================================================
class RetrievalQA:
    """
    RetrievalQA: Tích hợp SearchPipeline + Gemini API.

    Khởi tạo qua RetrievalQA.build() để tự động load tất cả components.
    """

    def __init__(self, pipeline, gemini: GeminiClient, top_k: int = TOP_K_CONTEXT):
        self.pipeline = pipeline
        self.gemini   = gemini
        self.top_k    = top_k
        # In-memory cache: (query_norm, mode, reranker, top_k) → result dict
        self._cache: dict = {}
        self._cache_max = 50  # Giữ tối đa 50 câu hỏi gần nhất

    # ----------------------------------------------------------
    #  Factory
    # ----------------------------------------------------------
    @classmethod
    def build(
        cls,
        api_key: Optional[str] = None,
        top_k: int = TOP_K_CONTEXT,
        use_reranker: bool = True,
        gemini_model: str = GEMINI_MODEL,
    ) -> "RetrievalQA":
        """
        Khởi tạo đầy đủ: QdrantManager + Embedder + SearchPipeline + GeminiClient.

        Args:
            api_key      : Gemini API key (mặc định lấy từ env GEMINI_API_KEY)
            top_k        : Số context chunks đưa vào prompt
            use_reranker : Có dùng Cross-Encoder reranker không
            gemini_model : Tên model Gemini (mặc định gemini-2.0-flash)
        """
        from vector_store.qdrant_client_app import QdrantManager
        from chunking.embedder import Embedder
        from search.search_pipeline import SearchPipeline, PipelineConfig

        print("⏳ Đang khởi tạo Search Engine...")
        t0 = time.time()

        try:
            from utils.download_utils import check_and_download_resources
            check_and_download_resources()
        except Exception as e:
            print(f"⚠️ Cảnh báo khi kiểm tra/tải tài nguyên tự động: {e}")

        qdrant   = QdrantManager(collection_name="vn_literature")
        embedder = Embedder(model_name=Embedder.FAST_MODEL)

        config = PipelineConfig(
            n_candidates=20,
            n_rerank=10,
            top_k=top_k,
            use_reranker=use_reranker,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            bm25_cache_path=str(Path("data/bm25_index.pkl")),
        )

        pipeline = SearchPipeline.build(
            qdrant_manager=qdrant,
            embedder=embedder,
            config=config,
        )

        gemini = GeminiClient(api_key=api_key, model=gemini_model)

        # ── Warm-up: nạp sẵn embedder + cross-encoder ngay lúc khởi tạo ──
        # Tránh dồn chi phí tải model (~vài giây) vào câu hỏi đầu tiên của người dùng.
        try:
            print("⏳ Warm-up models (embedder + reranker)...")
            pipeline.search("khởi động hệ thống", top_k=1, mode="hybrid",
                            use_reranker=use_reranker)
        except Exception as e:
            print(f"⚠️ Warm-up bỏ qua (sẽ nạp model ở truy vấn đầu): {e}")

        elapsed = (time.time() - t0) * 1000
        print(f"✅ Sẵn sàng! ({elapsed:.0f}ms) | Model: {gemini_model}\n")

        return cls(pipeline, gemini, top_k=top_k)

    # ----------------------------------------------------------
    #  Helpers cache search (pool tích lũy)
    # ----------------------------------------------------------
    @staticmethod
    def _to_ctx(r) -> dict:
        """Chuyển SearchResult → context dict thống nhất."""
        return {
            "doc_id" : r.doc_id,
            "text"   : r.text,
            "title"  : r.metadata.get("title", r.metadata.get("name", "Không rõ")),
            "author" : r.metadata.get("author", r.metadata.get("authors", "Không rõ")),
            "score"  : r.rerank_score if r.rerank_score else r.score,
            "metadata": r.metadata,
        }

    def _merge_pool(
        self,
        query: str,
        pool: List[dict],
        new_ctx: List[dict],
        use_reranker: Optional[bool],
        mode: str,
    ) -> List[dict]:
        """
        Gộp pool cũ + kết quả mới (dedup theo doc_id), re-rank theo query hiện tại.

        Khi follow-up câu hỏi đề xuất: tận dụng lại các đầu sách đã tìm trước đó
        và bổ sung kết quả mới, rồi chấm điểm lại toàn bộ theo câu hỏi mới.
        """
        by_id: dict = {}
        for c in pool:
            by_id[c["doc_id"]] = c
        for c in new_ctx:          # kết quả mới ghi đè (điểm/ text mới hơn)
            by_id[c["doc_id"]] = c
        merged = list(by_id.values())

        reranker = getattr(self.pipeline, "reranker", None)
        do_rerank = (
            (use_reranker if use_reranker is not None else True)
            and mode == "hybrid"
            and reranker is not None
        )

        if do_rerank and merged:
            # Chặn latency: chỉ đưa tối đa MERGE_RERANK_CAP candidate (ưu tiên điểm cũ cao)
            merged.sort(key=lambda c: c.get("score", 0) or 0, reverse=True)
            head = merged[:MERGE_RERANK_CAP]
            tail = merged[MERGE_RERANK_CAP:]
            scores = reranker.score(query, [c.get("text", "") for c in head])
            for c, s in zip(head, scores):
                c["score"] = float(s)
            head.sort(key=lambda c: c["score"], reverse=True)
            merged = head + tail
        else:
            merged.sort(key=lambda c: c.get("score", 0) or 0, reverse=True)

        return merged[:SEARCH_POOL_MAX]   # Giới hạn 1000 đầu sách trong cache search

    # ----------------------------------------------------------
    #  Retrieve (tách riêng để hỗ trợ streaming + cache search)
    # ----------------------------------------------------------
    def retrieve(
        self,
        query: str,
        mode: str = "hybrid",
        use_reranker: Optional[bool] = None,
        pool: Optional[List[dict]] = None,
        verbose: bool = False,
    ) -> dict:
        """
        Lấy context cho câu hỏi. Nếu có `pool` (cache search từ lượt trước, do
        người dùng chọn câu hỏi đề xuất) thì gộp + re-rank cùng kết quả mới.

        Returns dict:
            contexts       : List[dict] top_k đưa vào prompt
            pool           : List[dict] cache search đã cập nhật (≤ 1000)
            low_confidence : bool
            retrieve_ms    : int
            blocked_answer : Optional[str] — câu trả lời chặn (out-of-corpus) nếu có
        """
        pool = pool or []
        t0 = time.time()
        results = self.pipeline.search(
            query, top_k=self.top_k, use_reranker=use_reranker, mode=mode,
        )
        t_retrieve = round((time.time() - t0) * 1000)

        # Không có kết quả mới VÀ không có pool cũ → chặn
        if not results and not pool:
            return {
                "contexts": [], "pool": [], "low_confidence": False,
                "retrieve_ms": t_retrieve,
                "blocked_answer": "Xin lỗi, tôi không tìm thấy tài liệu liên quan đến câu hỏi này trong thư viện.",
            }

        # Gate relevance chỉ khi đây là câu hỏi mới (không có pool tích lũy)
        if results and not pool:
            top_score = results[0].rerank_score if results[0].rerank_score else results[0].score
            if top_score < RELEVANCE_THRESHOLD:
                return {
                    "contexts": [], "pool": [], "low_confidence": False,
                    "retrieve_ms": t_retrieve,
                    "blocked_answer": (
                        "Tôi không tìm thấy thông tin về chủ đề này trong thư viện của chúng tôi. "
                        "Thư viện hiện tập trung vào văn học Việt Nam và các tác phẩm dịch phổ biến tại Việt Nam. "
                        "Bạn có thể hỏi về tác phẩm, tác giả hoặc chủ đề văn học Việt Nam khác không?"
                    ),
                }

        new_ctx = [self._to_ctx(r) for r in results]

        # Gộp với pool cũ (nếu có) hoặc dùng riêng kết quả mới
        merged = self._merge_pool(query, pool, new_ctx, use_reranker, mode) if pool else new_ctx

        # top_k context cho prompt
        contexts = []
        for i, c in enumerate(merged[: self.top_k], 1):
            contexts.append({**c, "source_idx": i})

        updated_pool = merged[:SEARCH_POOL_MAX]
        low_confidence = bool(contexts) and (contexts[0].get("score", 0) or 0) < LOW_CONF_THRESHOLD

        if verbose:
            print(f"\n📚 Context ({len(contexts)} chunks, pool={len(updated_pool)}, {t_retrieve}ms):")
            for ctx in contexts:
                print(f"  [{ctx['source_idx']}] {ctx['title']} — {ctx['author']} (score={ctx['score']:.4f})")

        return {
            "contexts": contexts,
            "pool": updated_pool,
            "low_confidence": low_confidence,
            "retrieve_ms": t_retrieve,
            "blocked_answer": None,
        }

    # ----------------------------------------------------------
    #  Ask
    # ----------------------------------------------------------
    def ask(
        self,
        query: str,
        mode: str = "hybrid",
        use_reranker: Optional[bool] = None,
        verbose: bool = False,
        pool: Optional[List[dict]] = None,
    ) -> dict:
        """
        Trả lời câu hỏi sử dụng RAG pipeline (non-streaming, dùng cho CLI).

        Args:
            query        : Câu hỏi người dùng
            mode         : "hybrid" | "bm25" | "vector"
            use_reranker : Override reranker setting
            pool         : Cache search tích lũy (None = câu hỏi mới)

        Returns:
            dict: answer, contexts, pool, latency
        """
        # ── Cache lookup (chỉ cho câu hỏi mới, không có pool tích lũy) ──
        _reranker_flag = use_reranker if use_reranker is not None else True
        _cache_key = (query.strip().lower(), mode, _reranker_flag, self.top_k)
        if not pool and _cache_key in self._cache:
            cached = self._cache[_cache_key].copy()
            cached["latency"] = {**cached["latency"], "cached": True}
            cached.setdefault("pool", cached.get("contexts", []))
            return cached

        t_total = time.time()
        retr = self.retrieve(query, mode=mode, use_reranker=use_reranker,
                             pool=pool, verbose=verbose)

        if retr["blocked_answer"] is not None:
            return {
                "answer": retr["blocked_answer"],
                "contexts": [],
                "pool": retr["pool"],
                "latency": {"retrieve_ms": retr["retrieve_ms"], "llm_ms": 0,
                            "total_ms": retr["retrieve_ms"]},
            }

        contexts = retr["contexts"]
        prompt = build_prompt(query, contexts, low_confidence=retr["low_confidence"])
        t0 = time.time()
        answer = self.gemini.generate(prompt)
        t_llm = round((time.time() - t0) * 1000)

        result = {
            "answer"  : answer,
            "contexts": contexts,
            "pool"    : retr["pool"],
            "latency" : {
                "retrieve_ms": retr["retrieve_ms"],
                "llm_ms"     : t_llm,
                "total_ms"   : round((time.time() - t_total) * 1000),
            },
        }

        # Chỉ cache exact-match cho câu hỏi mới (kết quả follow-up phụ thuộc pool)
        if not pool:
            if len(self._cache) >= self._cache_max:
                del self._cache[next(iter(self._cache))]
            self._cache[_cache_key] = result

        return result

    # ----------------------------------------------------------
    #  Cache exact-match (dùng cho UI streaming: trả tức thì câu lặp lại)
    # ----------------------------------------------------------
    def _exact_key(self, query: str, mode: str, use_reranker: Optional[bool]):
        flag = use_reranker if use_reranker is not None else True
        return (query.strip().lower(), mode, flag, self.top_k)

    def peek_cache(self, query: str, mode: str = "hybrid",
                   use_reranker: Optional[bool] = None) -> Optional[dict]:
        """Trả về kết quả đã cache cho câu hỏi y hệt (None nếu chưa có)."""
        return self._cache.get(self._exact_key(query, mode, use_reranker))

    def store_cache(self, query: str, mode: str, use_reranker: Optional[bool],
                    result: dict) -> None:
        """Lưu kết quả 1 câu hỏi mới vào cache exact-match (LRU)."""
        if len(self._cache) >= self._cache_max:
            del self._cache[next(iter(self._cache))]
        self._cache[self._exact_key(query, mode, use_reranker)] = result

    def ask_no_rag(self, query: str) -> str:
        """Hỏi thẳng Gemini không qua retrieval (để so sánh)."""
        prompt = f"Câu hỏi về văn học Việt Nam: {query}\n\nTrả lời bằng tiếng Việt:"
        return self.gemini.generate(prompt)

    # ----------------------------------------------------------
    #  Display
    # ----------------------------------------------------------
    def print_answer(self, result: dict, query: str = "", show_sources: bool = True):
        """In kết quả dạng đẹp ra console."""
        sep = "=" * 65
        if query:
            print(f"\n{sep}")
            print(f"  ❓ Câu hỏi: {query}")
            print(sep)

        print(f"\n  💬 Trả lời:\n")
        # In từng dòng với indent
        for line in result["answer"].splitlines():
            print(f"  {line}")

        if show_sources and result.get("contexts"):
            print(f"\n  📖 Nguồn tài liệu:")
            for ctx in result["contexts"]:
                print(f"    [{ctx['source_idx']}] {ctx['title']} — {ctx['author']}")

        lat = result.get("latency", {})
        print(
            f"\n  ⏱ Retrieve: {lat.get('retrieve_ms', 0)}ms | "
            f"LLM: {lat.get('llm_ms', 0)}ms | "
            f"Tổng: {lat.get('total_ms', 0)}ms"
        )
        print()


# ============================================================
#  Interactive CLI
# ============================================================
def interactive_mode(qa: RetrievalQA, mode: str, verbose: bool):
    """Chạy vòng lặp hỏi-đáp tương tác."""
    print("=" * 65)
    print("  📚 Vietnamese Library RAG Chatbot")
    print(f"  Mode: {mode} | Model: {qa.gemini.model_name}")
    print("  Gõ 'quit' / 'q' để thoát")
    print("  Gõ 'norag: <câu hỏi>' để hỏi thẳng Gemini (không context)")
    print("=" * 65 + "\n")

    while True:
        try:
            query = input("  ❓ Câu hỏi: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  👋 Tạm biệt!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "q", "exit"):
            print("  👋 Tạm biệt!")
            break

        # Hỏi không qua RAG
        if query.lower().startswith("norag:"):
            raw_q = query[6:].strip()
            if raw_q:
                print("\n  💬 Trả lời (không RAG):\n")
                ans = qa.ask_no_rag(raw_q)
                for line in ans.splitlines():
                    print(f"  {line}")
                print()
            continue

        # RAG query
        result = qa.ask(query, mode=mode, verbose=verbose)
        qa.print_answer(result, query=query)


# ============================================================
#  Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="RetrievalQA — RAG Chatbot cho thư viện tiếng Việt với Gemini"
    )
    parser.add_argument("query", nargs="?", default=None,
                        help="Câu hỏi (bỏ trống để vào interactive mode)")
    parser.add_argument("--mode", choices=["hybrid", "bm25", "vector"],
                        default="hybrid", help="Chiến lược retrieval (default: hybrid)")
    parser.add_argument("--top-k", type=int, default=TOP_K_CONTEXT,
                        help=f"Số context chunks (default: {TOP_K_CONTEXT})")
    parser.add_argument("--no-rerank", action="store_true",
                        help="Tắt Cross-Encoder reranking")
    parser.add_argument("--no-rag", action="store_true",
                        help="Hỏi thẳng Gemini không qua retrieval")
    parser.add_argument("--gemini-model", default=GEMINI_MODEL,
                        help=f"Tên Gemini model (default: {GEMINI_MODEL})")
    parser.add_argument("--api-key", default=None,
                        help="Gemini API key (mặc định lấy từ env GEMINI_API_KEY)")
    parser.add_argument("--verbose", action="store_true",
                        help="Hiển thị context chunks tìm được")
    args = parser.parse_args()

    use_reranker = not args.no_rerank and args.mode == "hybrid"

    # Build QA engine
    qa = RetrievalQA.build(
        api_key=args.api_key,
        top_k=args.top_k,
        use_reranker=use_reranker,
        gemini_model=args.gemini_model,
    )

    if args.query:
        if args.no_rag:
            print("\n  💬 Trả lời (không RAG):\n")
            ans = qa.ask_no_rag(args.query)
            for line in ans.splitlines():
                print(f"  {line}")
            print()
        else:
            result = qa.ask(args.query, mode=args.mode, verbose=args.verbose)
            qa.print_answer(result, query=args.query)
    else:
        interactive_mode(qa, mode=args.mode, verbose=args.verbose)


if __name__ == "__main__":
    main()
