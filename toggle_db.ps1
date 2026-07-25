# ============================================================
#  toggle_db.ps1 - Chuyen nhanh Qdrant Cloud <-> DB Local
#  Dung khi mang CHET HAN giua demo (loi getaddrinfo).
#  Go:  .\toggle_db.ps1   -> tu dong dao trang thai, roi RESTART app.
# ============================================================
Set-Location $PSScriptRoot
$path = ".env"
$lines = Get-Content $path -Encoding UTF8

$isLocal = $lines | Where-Object { $_ -match '^\s*#\s*QDRANT_URL\s*=' }

$out = foreach ($ln in $lines) {
    if ($isLocal) {
        # Dang LOCAL -> bo comment de ve CLOUD
        if ($ln -match '^\s*#\s*(QDRANT_URL\s*=.*)$') { $Matches[1] }
        elseif ($ln -match '^\s*#\s*(QDRANT_API_KEY\s*=.*)$') { $Matches[1] }
        else { $ln }
    } else {
        # Dang CLOUD -> them comment de ve LOCAL
        if ($ln -match '^\s*QDRANT_URL\s*=') { "# $ln" }
        elseif ($ln -match '^\s*QDRANT_API_KEY\s*=') { "# $ln" }
        else { $ln }
    }
}
$out | Set-Content $path -Encoding UTF8

if ($isLocal) {
    Write-Host "`n>> DA CHUYEN VE: QDRANT CLOUD (can mang)" -ForegroundColor Cyan
} else {
    Write-Host "`n>> DA CHUYEN VE: DB LOCAL (offline, chi Gemini can mang)" -ForegroundColor Green
}
Write-Host ">> BAT BUOC: dong app dang chay (Ctrl+C) roi chay lai: streamlit run app.py" -ForegroundColor Yellow
Write-Host "   (App cache model nen phai restart moi nhan cau hinh moi ~35s)`n"
