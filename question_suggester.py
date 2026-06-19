"""
question_suggester.py -- Sinh câu hỏi gợi ý liên quan dựa trên query + context + answer.

Cách dùng:
    from question_suggester import QuestionSuggester

    suggester = QuestionSuggester(gemini_client)
    suggestions = suggester.suggest(
        query="Cho tôi biết về Nguyễn Du",
        contexts=[{"title": "Truyện Kiều", "author": "Nguyễn Du", ...}],
        answer="Nguyễn Du là...",
        n=3,
    )
    # → ["Truyện Kiều có bao nhiêu câu thơ?", "Nguyễn Du sinh ra ở đâu?", ...]
"""

from __future__ import annotations

import json
import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

# ============================================================
#  Prompt template
# ============================================================
_SUGGEST_PROMPT_TEMPLATE = """\
Bạn là trợ lý thư viện văn học. Người dùng vừa hỏi:

**Câu hỏi:** {query}

**Các tài liệu liên quan được tìm thấy:**
{context_summary}

**Câu trả lời đã cung cấp:**
{answer_snippet}

---
Hãy đề xuất {n} câu hỏi tiếp theo mà người dùng có thể muốn hỏi để khám phá sâu hơn.
Các câu hỏi cần:
- Đa dạng về góc độ (ví dụ: tìm hiểu thêm về tác giả, so sánh tác phẩm, khám phá thể loại tương tự, giai đoạn lịch sử, nội dung/cốt truyện...)
- Tự nhiên, phù hợp với người yêu văn học Việt Nam
- Ngắn gọn (tối đa 20 từ mỗi câu)
- Bằng tiếng Việt

Chỉ trả về danh sách JSON theo đúng định dạng sau (không thêm bất kỳ văn bản nào khác):
["Câu hỏi 1", "Câu hỏi 2", "Câu hỏi 3"]
"""


# ============================================================
#  QuestionSuggester
# ============================================================
class QuestionSuggester:
    """
    Sinh câu hỏi gợi ý liên quan sau mỗi lượt hội thoại.

    Sử dụng GeminiClient từ retrieval_qa.py để tái dùng kết nối API.
    """

    DEFAULT_N = 3

    def __init__(self, gemini_client):
        """
        Args:
            gemini_client: Instance của GeminiClient (từ retrieval_qa.py)
        """
        self.gemini = gemini_client

    # ----------------------------------------------------------
    #  Public API
    # ----------------------------------------------------------
    def suggest(
        self,
        query: str,
        contexts: List[dict],
        answer: str,
        n: int = DEFAULT_N,
    ) -> List[str]:
        """
        Sinh danh sách câu hỏi gợi ý.

        Args:
            query    : Câu hỏi gốc của người dùng
            contexts : List[dict] các context chunk (key: title, author, text)
            answer   : Câu trả lời chatbot đã tạo ra
            n        : Số câu hỏi gợi ý muốn sinh (mặc định 3)

        Returns:
            List[str] các câu hỏi gợi ý, hoặc [] nếu lỗi
        """
        try:
            context_summary = self._build_context_summary(contexts)
            answer_snippet = answer[:300] + "..." if len(answer) > 300 else answer

            prompt = _SUGGEST_PROMPT_TEMPLATE.format(
                query=query,
                context_summary=context_summary,
                answer_snippet=answer_snippet,
                n=n,
            )

            raw = self.gemini.generate(prompt, temperature=0.7)
            suggestions = self._parse_json_list(raw)

            # Lọc và giới hạn số lượng
            suggestions = [s.strip() for s in suggestions if s.strip()][:n]
            logger.info(f"[QuestionSuggester] Sinh được {len(suggestions)} gợi ý cho: '{query[:40]}'")
            return suggestions

        except Exception as e:
            logger.warning(f"[QuestionSuggester] Lỗi khi sinh gợi ý: {e}")
            return self._fallback_suggestions(query, contexts, n)

    # ----------------------------------------------------------
    #  Helpers
    # ----------------------------------------------------------
    @staticmethod
    def _build_context_summary(contexts: List[dict]) -> str:
        """Tóm tắt danh sách context thành chuỗi ngắn gọn."""
        if not contexts:
            return "(Không có tài liệu liên quan)"
        lines = []
        for ctx in contexts[:5]:  # Tối đa 5 tài liệu
            title  = ctx.get("title",  "Không rõ")
            author = ctx.get("author", "Không rõ")
            lines.append(f"- {title} ({author})")
        return "\n".join(lines)

    @staticmethod
    def _parse_json_list(raw: str) -> List[str]:
        """Parse JSON list từ response của Gemini, xử lý nhiều trường hợp output."""
        # Thử parse trực tiếp
        try:
            result = json.loads(raw.strip())
            if isinstance(result, list):
                return [str(x) for x in result]
        except json.JSONDecodeError:
            pass

        # Tìm JSON array trong văn bản
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                if isinstance(result, list):
                    return [str(x) for x in result]
            except json.JSONDecodeError:
                pass

        # Fallback: tách từng dòng có dấu ngoặc kép hoặc gạch đầu dòng
        lines = []
        for line in raw.splitlines():
            line = line.strip().lstrip("-•*0123456789.") .strip().strip('"').strip("'")
            if len(line) > 5:
                lines.append(line)
        return lines

    @staticmethod
    def _fallback_suggestions(query: str, contexts: List[dict], n: int) -> List[str]:
        """Gợi ý mặc định khi Gemini thất bại."""
        suggestions = []
        if contexts:
            title  = contexts[0].get("title",  "tác phẩm này")
            author = contexts[0].get("author", "tác giả này")
            suggestions = [
                f"Tóm tắt nội dung của '{title}'?",
                f"Tác giả {author} còn viết những tác phẩm nào khác?",
                f"Những tác phẩm tương tự '{title}' là gì?",
                f"Ý nghĩa và giá trị của '{title}' trong văn học Việt Nam?",
                f"Giai đoạn sáng tác của {author} là khi nào?",
            ]
        else:
            suggestions = [
                "Các tác phẩm văn học Việt Nam nổi tiếng nhất là gì?",
                "Những tác giả văn học Việt Nam tiêu biểu?",
                "Văn học Việt Nam giai đoạn 1930–1945 có những đặc điểm gì?",
            ]
        return suggestions[:n]
