Write-Host "🔧 TEST COMMANDS FOR PRODUCT DOCUMENTER" -ForegroundColor Cyan
Write-Host "=" * 60

Write-Host "`n[1] Check if API server is running:" -ForegroundColor Yellow
Write-Host "   curl http://localhost:8000/health" -ForegroundColor Gray
Write-Host "   OR in PowerShell:" -ForegroundColor Gray
Write-Host "   Invoke-RestMethod http://localhost:8000/health" -ForegroundColor Gray

Write-Host "`n[2] Generate a REAL document with OpenAI (will incur actual cost):" -ForegroundColor Yellow
$body = @{
    context = "User authentication system with JWT tokens and OAuth2"
    doc_type = "technical_spec"
    licensing_focus = $true
    source = "powershell_test"
} | ConvertTo-Json -Compress

Write-Host "   Body:" -ForegroundColor Gray
Write-Host "   $body" -ForegroundColor DarkGray
Write-Host "`n   Command:" -ForegroundColor Gray
Write-Host "   Invoke-RestMethod http://localhost:8000/generate -Method Post -ContentType 'application/json' -Body '$body'" -ForegroundColor Gray

Write-Host "`n[3] Check costs in dashboard:" -ForegroundColor Yellow
Write-Host "   Open browser to: http://localhost:8501" -ForegroundColor Gray
Write-Host "   OR check via API:" -ForegroundColor Gray
Write-Host "   Invoke-RestMethod http://localhost:8000/costs" -ForegroundColor Gray

Write-Host "`n[4] Check review queue:" -ForegroundColor Yellow
Write-Host "   Invoke-RestMethod http://localhost:8000/review-queue" -ForegroundColor Gray
Write-Host "   OR check folder: Get-ChildItem docs\review" -ForegroundColor Gray

Write-Host "`n[5] Submit a review (after editing document):" -ForegroundColor Yellow
$reviewBody = @{
    filepath = "docs\review\technical_spec_1_*.md"  # Use actual filename
    reviewed_content = "# Reviewed Document`n`nThis has been reviewed and updated."
    changes_summary = "Updated technical details and formatting"
    reviewer_name = "John Doe"
    prepare_for_licensing = $true
} | ConvertTo-Json -Compress

Write-Host "   Invoke-RestMethod http://localhost:8000/submit-review -Method Post -ContentType 'application/json' -Body '$reviewBody'" -ForegroundColor Gray

Write-Host "`n[6] Create licensing package:" -ForegroundColor Yellow
$packageBody = @{
    product_name = "Authentication System"
    version = "1.0"
} | ConvertTo-Json -Compress

Write-Host "   Invoke-RestMethod http://localhost:8000/create-licensing-package -Method Post -ContentType 'application/json' -Body '$packageBody'" -ForegroundColor Gray

Write-Host "`n" + "=" * 60
Write-Host "💡 COST ESTIMATES:" -ForegroundColor Green
Write-Host "   GPT-3.5 Turbo: $0.002 per 1,000 tokens" -ForegroundColor Gray
Write-Host "   Average document: 500-1000 tokens ($0.001-$0.002)" -ForegroundColor Gray
Write-Host "   50 documents/month: ~$0.10" -ForegroundColor Gray
Write-Host "   500 documents/month: ~$1.00" -ForegroundColor Gray

Write-Host "`n⚠️  IMPORTANT:" -ForegroundColor Red
Write-Host "   - Actual costs depend on document length" -ForegroundColor DarkRed
Write-Host "   - Monitor costs in dashboard" -ForegroundColor DarkRed
Write-Host "   - Set budget in .env file" -ForegroundColor DarkRed