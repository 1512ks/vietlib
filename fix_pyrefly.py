import os
import unicodedata

def remove_vietnamese_accents(s):
    s = s.replace('Đ', 'D').replace('đ', 'd').replace('--', '--')
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')

for root, _, files in os.walk('.'):
    if '.venv' in root or '.git' in root: continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
            except Exception:
                continue
            
            changed = False
            for i in range(min(50, len(lines))):
                old_line = lines[i]
                if '--' in old_line:
                    lines[i] = old_line.replace('--', '--')
                    changed = True
                    old_line = lines[i]
                    
                if old_line.strip().startswith('\"\"\"') or old_line.strip().startswith('#'):
                    try:
                        old_line.encode('ascii')
                    except UnicodeEncodeError:
                        lines[i] = remove_vietnamese_accents(old_line)
                        changed = True

            if changed:
                with open(path, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                print(f'Fixed encoding for Pyrefly in {path}')
