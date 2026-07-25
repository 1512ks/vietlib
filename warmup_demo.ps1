# ============================================================
#  warmup_demo.ps1 - Chay SANG DEMO truoc buoi bao ve ~30 phut
#  Mo PowerShell trong thu muc DATN roi go:  .\warmup_demo.ps1
# ============================================================
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "`n=== [1/3] Kiem tra ha tang (Qdrant Cloud + Gemini) ===" -ForegroundColor Cyan
& .venv\Scripts\python.exe -X utf8 -c @"
import os
from dotenv import load_dotenv
load_dotenv()
from qdrant_client import QdrantClient
c = QdrantClient(url=os.environ['QDRANT_URL'], api_key=os.environ['QDRANT_API_KEY'], timeout=20)
info = c.get_collection('vn_literature')
print(f'    Qdrant Cloud: {info.points_count} diem, status={info.status}')
import google.generativeai as genai
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
m = genai.GenerativeModel('gemini-2.5-flash')
print('    Gemini:', m.generate_content('Tra loi 1 tu: OK').text.strip()[:20])
print('    >> HA TANG SAN SANG')
"@

Write-Host "`n=== [2/3] Bat app Streamlit (nap model, warm cache) ===" -ForegroundColor Cyan
Write-Host "    Cho ~35 giay cho lan nap model dau tien..." -ForegroundColor Yellow
Start-Process -FilePath ".venv\Scripts\streamlit.exe" -ArgumentList "run app.py"

Write-Host "`n=== [3/3] Cho app len va mo trinh duyet ===" -ForegroundColor Cyan
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 3
    try {
        $r = Invoke-WebRequest -Uri http://localhost:8501 -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch {}
}
if ($ok) {
    Write-Host "    App da san sang: http://localhost:8501" -ForegroundColor Green
    Start-Process "http://localhost:8501"
    Write-Host "`n>> GO 1 CAU WARM-UP (vd: 'So do noi ve gi?') roi de yen. San sang bao ve!" -ForegroundColor Green
} else {
    Write-Host "    App chua len sau 90s - kiem tra thu cong: streamlit run app.py" -ForegroundColor Red
}

Write-Host "`n--- NHAC NHO ---" -ForegroundColor Magenta
Write-Host "  * Bat 4G du phong (Gemini + Qdrant Cloud can mang)"
Write-Host "  * Neu mat mang: chay .\toggle_db.ps1 de chuyen sang DB local roi khoi dong lai app"
Write-Host "  * Dong tab/editor dang mo file .env va secrets.toml va APIKEYS (for testing).tex"
Write-Host "  * Mo san: demo_script.md, bo_cau_hoi_demo.md, giai_thich_code.md, DATN_so_lieu_that.pdf"
Write-Host "  * Gap loi getaddrinfo giua demo: DUNG bam retry -> tat han app roi bat lai"
