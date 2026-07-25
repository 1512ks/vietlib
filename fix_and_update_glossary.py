"""
Script 2: 
1. Fix remaining parenthetical issues in DATN_cleaned.tex
2. Update the glossary table with new terms
3. Save as final DATN_final.tex
"""
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('DATN_cleaned.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# MANUAL FIXES for remaining patterns not caught by the script
# These are specific instances that need targeted fixes
# ============================================================

# Fix remaining parenthetical annotations that slipped through
manual_fixes = [
    # In abstract (tóm tắt) - line 304
    ('``ảo tưởng\'\' (hallucination) của các mô hình ngôn ngữ lớn (LLM)',
     '``ảo tưởng\'\' của các mô hình ngôn ngữ lớn (LLM)'),
    ('kiến trúc sinh tăng cường truy vấn (RAG - Retrieval-Augmented Generation)',
     'kiến trúc sinh tăng cường truy vấn'),
    ('phân mảnh văn bản (chunking)',
     'phân mảnh văn bản'),
    ('tìm kiếm hỗn hợp (Hybrid Search)',
     'tìm kiếm hỗn hợp'),
    ('Dense Retrieval, cùng mô hình tái xếp hạng Reranker',
     'truy hồi dày đặc, cùng mô hình tái xếp hạng'),
    # Mục tiêu section - remaining (Hybrid Search) and (RAG)
    ('tìm kiếm lai hợp (Hybrid Search) kết hợp',
     'tìm kiếm lai hợp kết hợp'),
    ('Sinh tăng cường truy vấn (RAG), bao gồm',
     'Sinh tăng cường truy vấn, bao gồm'),
    # Phạm vi section
    ('Tập ngữ liệu (corpus) được thu thập',
     'Tập ngữ liệu được thu thập'),
    # Intro LLM ref
    ('các mô hình ngôn ngữ lớn (LLM) đã mở ra khả năng đọc hiểu',
     'các mô hình ngôn ngữ lớn đã mở ra khả năng đọc hiểu'),
    # Phân tích so sánh section
    ('tinh chỉnh mô hình và sinh tăng cường truy vấn (RAG). Mục này',
     'tinh chỉnh mô hình và sinh tăng cường truy vấn. Mục này'),
    ('\\subsection{Sinh tăng cường truy vấn (RAG)}',
     '\\subsection{Sinh tăng cường truy vấn}'),
    # NLU in Vietnam section
    ('các bộ máy hiểu ngôn ngữ tự nhiên (NLU) tự phát triển',
     'các bộ máy hiểu ngôn ngữ tự nhiên tự phát triển'),
    # Chương 1 table header remaining
    ('phân tích so sánh hai hướng tiếp cận chủ đạo là tinh chỉnh mô hình (Fine-tuning) và sinh tăng cường truy vấn (RAG), từ đó',
     'phân tích so sánh hai hướng tiếp cận chủ đạo là tinh chỉnh mô hình và sinh tăng cường truy vấn, từ đó'),
    # ConvQA in text
    ('hệ thống hỏi đáp mang tính hội thoại (\\textit{Conversational Question Answering} -- ConvQA)',
     'hệ thống hỏi đáp mang tính hội thoại (hỏi đáp hội thoại -- ConvQA)'),
    # Số hóa tài liệu (OCR) - keep OCR as it's already known
    # OCR is an abbreviation already in common use, keep as is
    # keyword in abstract
    ('không nhớ keyword chính xác về sách',
     'không nhớ từ khóa chính xác về sách'),
    # Semantic Search in keywords line - keep as-is in \textbf{Từ khóa}
]

changes_made = 0
for old, new in manual_fixes:
    if old in content:
        content = content.replace(old, new)
        print(f"FIXED: {old[:80]}")
        changes_made += 1
    else:
        print(f"NOT FOUND: {old[:80]}")

print(f"\nManual fixes applied: {changes_made}")

# ============================================================
# UPDATE GLOSSARY TABLE
# Add new terms with Vietnamese meanings
# ============================================================

OLD_GLOSSARY_END = r"""\bottomrule
\end{longtable}
\end{center}


\newpage"""

NEW_GLOSSARY_CONTENT = r"""ANN & Approximate Nearest Neighbor & Tìm kiếm láng giềng gần đúng \\
API & Application Programming Interface & Giao diện lập trình ứng dụng \\
BM25 & Best Matching 25 & Thuật toán xếp hạng từ khóa tìm kiếm \\
ConvQA & Conversational Question Answering & Hỏi đáp hội thoại \\
CRF & Conditional Random Fields & Trường ngẫu nhiên có điều kiện \\
DB & Database & Cơ sở dữ liệu \\
FR & Functional Requirements & Yêu cầu chức năng \\
HNSW & Hierarchical Navigable Small World & Đồ thị thế giới nhỏ điều hướng phân cấp \\
HUST & Hanoi University of Science and Technology & Đại học Bách khoa Hà Nội \\
LLM & Large Language Model & Mô hình ngôn ngữ lớn \\
MRR & Mean Reciprocal Rank & Độ đo thứ hạng nghịch đảo trung bình \\
NFR & Non-Functional Requirements & Yêu cầu phi chức năng \\
NLP & Natural Language Processing & Xử lý ngôn ngữ tự nhiên \\
NLU & Natural Language Understanding & Hiểu ngôn ngữ tự nhiên \\
OCR & Optical Character Recognition & Nhận dạng ký tự quang học \\
RAG & Retrieval-Augmented Generation & Sinh tăng cường truy vấn \\
RRF & Reciprocal Rank Fusion & Thuật toán kết hợp thứ hạng \\
SRS & Software Requirement Specification & Đặc tả yêu cầu phần mềm \\
SSE & Server-Sent Events & Cơ chế truyền dữ liệu dạng luồng từ máy chủ \\
UI/UX & User Interface / User Experience & Giao diện / Trải nghiệm người dùng \\"""

NEW_GLOSSARY_TABLE = (
    r"""\begin{longtable}{p{2.5cm}p{6.5cm}p{5cm}}
\caption{Bảng ký hiệu và chữ viết tắt}\\
\toprule
\textbf{Ký hiệu/Viết tắt} & \textbf{Tên đầy đủ} & \textbf{Tiếng Việt} \\
\midrule
\endfirsthead

\toprule
\textbf{Ký hiệu/Viết tắt} & \textbf{Tên đầy đủ} & \textbf{Tiếng Việt} \\
\midrule
\endhead

"""
    + NEW_GLOSSARY_CONTENT
    + r"""
\bottomrule
\end{longtable}
\end{center}


\newpage"""
)

# Find and replace the old glossary table
old_table_start = r"""\begin{longtable}{p{2.5cm}p{10cm}}
\caption{Bảng ký hiệu và chữ viết tắt}\\"""
old_table_end = r"""\bottomrule
\end{longtable}
\end{center}


\newpage"""

if old_table_start in content:
    # Find the full extent of the old table
    start_idx = content.find(old_table_start)
    end_idx = content.find(old_table_end, start_idx) + len(old_table_end)
    old_table = content[start_idx:end_idx]
    content = content[:start_idx] + NEW_GLOSSARY_TABLE + content[end_idx:]
    print("\nGlossary table updated successfully!")
else:
    print("\nWARNING: Could not find old glossary table!")

# Write final file
with open('DATN_final.tex', 'w', encoding='utf-8') as f:
    f.write(content)

print("Final file written: DATN_final.tex")
