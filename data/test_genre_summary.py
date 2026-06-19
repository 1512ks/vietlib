"""
test_genre_summary.py - Thử prompt mới có bổ sung genre + đối tượng độc giả
Chạy: .\.venv\Scripts\python.exe data\test_genre_summary.py
"""
import sys, os, json, glob, random
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=api_key)

PROMPT = """\
Hãy phân tích và viết tóm tắt cho tác phẩm văn học sau. Trả lời ĐÚNG THEO định dạng bên dưới, không thêm bất cứ thứ gì khác:

Thể loại: [ví dụ: Tiểu thuyết hiện thực / Truyện ngắn / Thơ / Kiếm hiệp / Trinh thám / Cổ tích / v.v.]
Đối tượng: [ví dụ: Người lớn / Thiếu nhi / Thanh thiếu niên / Mọi lứa tuổi]
Tóm tắt: [3-5 câu mô tả nội dung chính, nhân vật, bối cảnh của tác phẩm]

---
Tên tác phẩm: {title}
Tác giả: {author}
Trích đoạn:
\"\"\"
{excerpt}
\"\"\"
"""

# Lấy 3 file ngẫu nhiên từ archive để test
files = glob.glob('data/processed/archive/*.json')
sample = random.sample(files, 3)

for i, f in enumerate(sample, 1):
    try:
        doc = json.load(open(f, encoding='utf-8'))
        title = doc.get('title', '')
        author = doc.get('author', '')
        content = doc.get('content', '')[:3000]
        
        print(f"\n{'='*65}")
        print(f"[{i}/3] {title} — {author}")
        print('='*65)
        
        prompt = PROMPT.format(title=title, author=author, excerpt=content)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=512,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        print(response.text.strip())
        
    except Exception as e:
        print(f"Loi: {e}")

print("\n[XONG]")
