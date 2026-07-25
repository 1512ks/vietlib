"""
Script to clean parenthetical annotations from DATN.tex
- Output results to UTF-8 file instead of console
"""
import re
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('DATN.tex', 'r', encoding='utf-8') as f:
    content = f.read()

removed_terms = []
changes = []

lines = content.split('\n')
new_lines = []

def is_skip_line(line):
    skip_patterns = [r'\\bibitem', r'^\s*%', r'\\begin\{thebibliography\}', r'\\end\{thebibliography\}']
    for pat in skip_patterns:
        if re.search(pat, line):
            return True
    return False

# ============================================================
# PATTERNS TO REMOVE
# ============================================================
# P1: (\textit{Long English Name} -- ABBREV)  e.g. (\textit{Large Language Model} -- LLM)
PAT1 = re.compile(r'\s*\(\\textit\{([^}]+)\}\s*[-\u2013]+\s*([A-Z0-9/]+)\)')
# P2: (\textit{English term}) no abbreviation
PAT2 = re.compile(r'\s*\(\\textit\{([^}]+)\}\)')
# P3: (English Name -- ABBREV) no textit wrapper
PAT3 = re.compile(r'\s*\(([A-Z][A-Za-z\s,\-/]+)\s*[-\u2013]+\s*([A-Z][A-Z0-9/]+)\)')
# P4: specific single English technical terms in parens
ENGLISH_TERMS = [
    'hallucination', 'Fine-tuning', 'fine-tuning', 'grounding', 'provenance',
    'resume', 'quota', 'cold start', 'streaming', 'monolithic', 'payload',
    'normalize', 'keyword matching', 'pattern matching', 'self-attention',
    'deep learning', 'pre-trained language models', 'word segmentation',
    'low-resource language', 'agentic search', 'Smart Citations', 'Semantic Reader',
    'metadata injection', 'metadata-injection', 'fixed-size with overlap',
    'sliding window', 'sentence-aware', 'healthcheck', 'animated gradient',
    'glassmorphism', 'Lottie', 'Golden Dataset', 'audience', 'genre', 'summary',
    'author', 'work', 'concept', 'archive', 'catastrophic forgetting', 'endpoint',
    'knowledge cutoff', 'retrieve', 'hybrid search', 'dense retrieval',
    'semantic search', 'functional requirements', 'non-functional requirements',
]
terms_pattern = '|'.join(re.escape(t) for t in ENGLISH_TERMS)
PAT4 = re.compile(r'\s*\((' + terms_pattern + r')\)')

# Mapping: english term -> Vietnamese meaning (for glossary)
VI_MEANING = {
    'hallucination': 'ảo tưởng',
    'Fine-tuning': 'tinh chỉnh mô hình',
    'grounding': 'đặt nền tảng tri thức',
    'provenance': 'nguồn gốc thông tin',
    'resume': 'tiếp tục từ điểm dừng',
    'quota': 'hạn mức',
    'cold start': 'khởi động lạnh',
    'streaming': 'phản hồi theo luồng',
    'monolithic': 'ứng dụng nguyên khối',
    'payload': 'tải trọng dữ liệu',
    'normalize': 'chuẩn hóa độ dài đơn vị',
    'keyword matching': 'đối khớp từ khóa',
    'pattern matching': 'so khớp mẫu',
    'self-attention': 'tự chú ý',
    'deep learning': 'học sâu',
    'pre-trained language models': 'mô hình ngôn ngữ tiền huấn luyện',
    'word segmentation': 'tách từ',
    'low-resource language': 'ngôn ngữ ít tài nguyên',
    'agentic search': 'tìm kiếm có tính tác nhân',
    'Smart Citations': 'trích dẫn thông minh',
    'Semantic Reader': 'công cụ đọc ngữ nghĩa',
    'metadata injection': 'chèn siêu dữ liệu',
    'fixed-size with overlap': 'chia kích thước cố định có chồng lấp',
    'sliding window': 'cửa sổ trượt',
    'sentence-aware': 'tôn trọng ranh giới câu',
    'healthcheck': 'kiểm tra sức khỏe',
    'animated gradient': 'nền chuyển sắc động',
    'glassmorphism': 'kiểu kính mờ',
    'Lottie': 'hoạt ảnh Lottie',
    'Golden Dataset': 'bộ truy vấn kiểm thử chuẩn',
    'catastrophic forgetting': 'quên thảm họa',
    'endpoint': 'điểm truy cập',
    'knowledge cutoff': 'thời điểm đóng băng tri thức',
    'retrieve': 'truy hồi',
    'hybrid search': 'tìm kiếm lai hợp',
    'dense retrieval': 'truy hồi dày đặc',
    'semantic search': 'tìm kiếm ngữ nghĩa',
    'functional requirements': 'yêu cầu chức năng',
    'non-functional requirements': 'yêu cầu phi chức năng',
}

for i, line in enumerate(lines):
    original = line
    
    if is_skip_line(line):
        new_lines.append(line)
        continue
    
    new_line = line

    # Apply P1
    def repl1(m):
        removed_terms.append({'line': i+1, 'english': m.group(1).strip(), 'abbrev': m.group(2), 'full': m.group(0)})
        return ''
    # Apply P2
    def repl2(m):
        removed_terms.append({'line': i+1, 'english': m.group(1).strip(), 'abbrev': '', 'full': m.group(0)})
        return ''
    # Apply P3
    def repl3(m):
        removed_terms.append({'line': i+1, 'english': m.group(1).strip(), 'abbrev': m.group(2), 'full': m.group(0)})
        return ''
    # Apply P4
    def repl4(m):
        removed_terms.append({'line': i+1, 'english': m.group(1).strip(), 'abbrev': '', 'full': m.group(0)})
        return ''

    new_line = PAT1.sub(repl1, new_line)
    new_line = PAT2.sub(repl2, new_line)
    new_line = PAT3.sub(repl3, new_line)
    new_line = PAT4.sub(repl4, new_line)
    
    if new_line != original:
        changes.append({'line': i+1, 'before': original, 'after': new_line})
    
    new_lines.append(new_line)

new_content = '\n'.join(new_lines)

# Write cleaned file
with open('DATN_cleaned.tex', 'w', encoding='utf-8') as f:
    f.write(new_content)

# Write report
with open('annotation_report.txt', 'w', encoding='utf-8') as f:
    f.write(f"Tổng số dòng thay đổi: {len(changes)}\n")
    f.write(f"Tổng số chú thích đã xóa: {len(removed_terms)}\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("CHI TIẾT THAY ĐỔI\n")
    f.write("=" * 60 + "\n\n")
    for c in changes:
        f.write(f"Dòng {c['line']}:\n")
        f.write(f"  TRƯỚC: {c['before'].strip()[:200]}\n")
        f.write(f"  SAU:   {c['after'].strip()[:200]}\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("THUẬT NGỮ CẦN THÊM VÀO BẢNG CHÚ THÍCH\n")
    f.write("=" * 60 + "\n\n")
    
    seen = set()
    unique = []
    for t in removed_terms:
        key = t['english'].strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(t)
    
    for t in sorted(unique, key=lambda x: x['english']):
        vi = VI_MEANING.get(t['english'], '???')
        abbrev = t['abbrev'] if t['abbrev'] else '---'
        f.write(f"  EN: {t['english']:<40} | ABBREV: {abbrev:<10} | VI: {vi}\n")

print(f"Done! {len(changes)} lines changed, {len(removed_terms)} annotations removed.")
print("Files written: DATN_cleaned.tex, annotation_report.txt")
