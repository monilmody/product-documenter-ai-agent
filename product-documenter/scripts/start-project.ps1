Write-Host "🚀 Starting Product Documenter AI System..." -ForegroundColor Cyan

# Start API Server in new window
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; python api_server.py`""

Start-Sleep -Seconds 3

# Start Dashboard in new window  
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; streamlit run monitor_dashboard.py`""

Write-Host "`n✅ System started!" -ForegroundColor Green
Write-Host "API Server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Dashboard: http://localhost:8501" -ForegroundColor Cyan
Write-Host "`nReady for work! 🎯" -ForegroundColor White