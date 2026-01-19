# Modified version - just scan and document on demand
cd ..

Write-Host "🔍 Manual Project Scan" -ForegroundColor Cyan

# Get recent changes (last 4 hours for manual scan)
$changedFiles = Get-ChildItem -Recurse -Include *.py,*.js,*.java,*.cs,*.md -File |
                Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-4) } |
                Select-Object -First 15

if ($changedFiles.Count -eq 0) {
    Write-Host "📭 No recent changes found (last 4 hours)" -ForegroundColor Yellow
    exit
}

$context = @"
MANUAL PROJECT SCAN - $(Get-Date -Format 'yyyy-MM-dd HH:mm')

Recent Changes ($($changedFiles.Count) files):
$(($changedFiles | ForEach-Object { "• $($_.Name) ($($_.LastWriteTime.ToString('HH:mm')))" }) -join "`n")

Project Snapshot:
• Total files: $(@(Get-ChildItem -Recurse -File).Count)
• Main folder: $(Get-Location)
"@

$body = @{
    context = $context
    doc_type = "project_snapshot"
    licensing_focus = $false
    source = "manual_scan"
} | ConvertTo-Json

try {
    $response = irm http://localhost:8000/generate -Method Post -ContentType "application/json" -Body $body
    Write-Host "✅ Documented $($changedFiles.Count) changes" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}

cd product-documenter\scripts