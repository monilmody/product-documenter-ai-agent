Write-Host "📊 SYSTEM STATUS" -ForegroundColor Cyan
Write-Host "=" * 40

# Check API
try {
    $health = irm http://localhost:8000/health -TimeoutSec 2
    Write-Host "✅ API Server: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ API Server: OFFLINE" -ForegroundColor Red
}

# Check docs folder
$review = (Get-ChildItem "docs\review" -Filter *.md -ErrorAction SilentlyContinue).Count
$approved = (Get-ChildItem "docs\licensing_ready" -Filter *.md -Recurse -ErrorAction SilentlyContinue).Count

Write-Host "📁 Documents:" -ForegroundColor Cyan
Write-Host "  • Pending review: $review" -ForegroundColor $(if ($review -gt 0) {"Yellow"} else {"Gray"})
Write-Host "  • Approved: $approved" -ForegroundColor Gray

# Quick cost check
try {
    $costs = irm "http://localhost:8000/costs?days=1" -TimeoutSec 3
    Write-Host "💰 Today's cost: $$($costs.total_cost)" -ForegroundColor Gray
} catch {
    Write-Host "💰 Cost data: Unavailable" -ForegroundColor Gray
}

Write-Host "`n🔗 Dashboard: http://localhost:8501" -ForegroundColor Cyan
Write-Host "🔗 API: http://localhost:8000" -ForegroundColor Cyan