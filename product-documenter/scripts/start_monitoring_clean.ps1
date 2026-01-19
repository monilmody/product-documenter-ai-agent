# product-documenter/scripts/start_monitoring.ps1
# LEAN MONITORING SYSTEM - MANUAL CONTROL

Write-Host "STARTING PROJECT MONITORING" -ForegroundColor Cyan
Write-Host "=" * 50

# 1. Start API Server (MUST BE RUNNING)
Write-Host "`n[1] Starting API Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; python api_server.py`"" -WindowStyle Minimized

Write-Host "   Waiting for API to start..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# 2. Test API connection
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 3
    Write-Host "   OK API Server: http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "   ERROR API failed to start" -ForegroundColor Red
    exit 1
}

Write-Host "`n[2] Choose monitoring mode:" -ForegroundColor Yellow
Write-Host "   1. Full monitoring (Git + File changes)" -ForegroundColor Gray
Write-Host "   2. Git commits only" -ForegroundColor Gray
Write-Host "   3. File changes only" -ForegroundColor Gray
Write-Host "   4. Start Dashboard only" -ForegroundColor Gray

$choice = Read-Host "`nEnter choice (1-4)"

if ($choice -eq "1") {
    # Full monitoring
    Write-Host "`nStarting FULL monitoring..." -ForegroundColor Cyan
    
    # Git monitor (catches missed commits)
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; python git_monitor.py`"" -WindowStyle Minimized
    
    # File monitor (real-time changes)
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; python parent_project_monitor.py`"" -WindowStyle Minimized
    
    # Dashboard
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; streamlit run monitor_dashboard.py`""
    
    Write-Host "   OK Git monitor: Running (hourly scans)" -ForegroundColor Green
    Write-Host "   OK File monitor: Running (real-time)" -ForegroundColor Green
    Write-Host "   OK Dashboard: http://localhost:8501" -ForegroundColor Green
}
elseif ($choice -eq "2") {
    # Git only
    Write-Host "`nStarting GIT monitoring only..." -ForegroundColor Cyan
    
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; python git_monitor.py`"" -WindowStyle Minimized
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; streamlit run monitor_dashboard.py`""
    
    Write-Host "   OK Git monitor: Running (hourly scans)" -ForegroundColor Green
    Write-Host "   OK Dashboard: http://localhost:8501" -ForegroundColor Green
    Write-Host "   WARNING File monitoring: DISABLED" -ForegroundColor Yellow
}
elseif ($choice -eq "3") {
    # File changes only
    Write-Host "`nStarting FILE monitoring only..." -ForegroundColor Cyan
    
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; python parent_project_monitor.py`"" -WindowStyle Minimized
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; streamlit run monitor_dashboard.py`""
    
    Write-Host "   OK File monitor: Running (real-time)" -ForegroundColor Green
    Write-Host "   OK Dashboard: http://localhost:8501" -ForegroundColor Green
    Write-Host "   WARNING Git monitoring: DISABLED" -ForegroundColor Yellow
}
elseif ($choice -eq "4") {
    # Dashboard only
    Write-Host "`nStarting DASHBOARD only..." -ForegroundColor Cyan
    
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; streamlit run monitor_dashboard.py`""
    
    Write-Host "   OK Dashboard: http://localhost:8501" -ForegroundColor Green
    Write-Host "   WARNING Monitoring: DISABLED (manual mode)" -ForegroundColor Yellow
}
else {
    Write-Host "   ERROR Invalid choice. Exiting." -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "=" * 50
Write-Host "OK SYSTEM READY" -ForegroundColor Green
Write-Host "=" * 50

Write-Host "`nHOW TO USE:" -ForegroundColor Cyan
Write-Host "??? Git commits auto-document via hook" -ForegroundColor Gray
Write-Host "??? Manual documentation: Use API or scripts" -ForegroundColor Gray
Write-Host "??? Check dashboard for progress" -ForegroundColor Gray
Write-Host "??? Close windows to stop monitoring" -ForegroundColor Gray

Write-Host "`nAvailable scripts:" -ForegroundColor Cyan
Write-Host "  ??? .\document_main_project.ps1     - Scan and document main project" -ForegroundColor Gray
Write-Host "  ??? .\submit_review.ps1             - Submit reviewed documents" -ForegroundColor Gray
Write-Host "  ??? .\check_status.ps1              - Quick system check" -ForegroundColor Gray

pause
