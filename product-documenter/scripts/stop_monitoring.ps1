Write-Host "💥 NUCLEAR OPTION - KILLING EVERYTHING" -ForegroundColor Red
Write-Host "=" * 60

# Kill ALL Python processes (careful if you have other Python apps!)
Write-Host "Killing ALL Python processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Killing: $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Gray
    $_ | Stop-Process -Force
}

# Kill by EXACT process names
$processesToKill = @("python", "pythonw", "python3", "streamlit", "flask", "powershell")
foreach ($proc in $processesToKill) {
    Get-Process $proc -ErrorAction SilentlyContinue | Stop-Process -Force
}

# Use taskkill for stubborn processes (including child processes with /T flag)
Write-Host "`nUsing taskkill for stubborn processes..." -ForegroundColor Yellow
taskkill /F /IM python.exe /T 2>$null
taskkill /F /IM pythonw.exe /T 2>$null
taskkill /F /IM streamlit.exe /T 2>$null
taskkill /F /IM powershell.exe /T 2>$null

# Kill by port (most effective)
Write-Host "`nKilling processes by port..." -ForegroundColor Yellow
$ports = @(8000, 8501, 5000, 3000)
foreach ($port in $ports) {
    try {
        $output = netstat -ano | findstr ":$port" | findstr "LISTENING"
        if ($output) {
            $pid = ($output -split '\s+')[-1]
            taskkill /F /PID $pid 2>$null
            Write-Host "  Killed process on port $port (PID: $pid)" -ForegroundColor Green
        }
    } catch {
        # Ignore errors
    }
}

# Use PowerShell's Stop-Process with more force
Write-Host "`nFinal cleanup with PowerShell..." -ForegroundColor Yellow
Get-Process | Where-Object {
    $_.ProcessName -like "*python*" -or
    $_.ProcessName -like "*streamlit*" -or
    $_.MainWindowTitle -like "*api*" -or
    $_.MainWindowTitle -like "*dashboard*" -or
    $_.MainWindowTitle -like "*monitor*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Check what's still running
Write-Host "`nChecking remaining processes..." -ForegroundColor Cyan
$remaining = @()
$remaining += Get-Process python -ErrorAction SilentlyContinue
$remaining += Get-Process pythonw -ErrorAction SilentlyContinue
$remaining += Get-Process streamlit -ErrorAction SilentlyContinue

if ($remaining.Count -gt 0) {
    Write-Host "⚠️  Still running:" -ForegroundColor Yellow
    $remaining | Select-Object Id, ProcessName, MainWindowTitle | Format-Table -AutoSize
} else {
    Write-Host "✅ All Python/Streamlit processes killed" -ForegroundColor Green
}

# Check ports again
Write-Host "`nFinal port check:" -ForegroundColor Cyan
foreach ($port in @(8000, 8501)) {
    $result = netstat -ano | findstr ":$port" | findstr "LISTENING"
    if ($result) {
        Write-Host "❌ Port $port is STILL in use!" -ForegroundColor Red
        Write-Host "   Try this command manually:"
        Write-Host "   netstat -ano | findstr :$port" -ForegroundColor Gray
    } else {
        Write-Host "✅ Port $port is free" -ForegroundColor Green
    }
}

Write-Host "`n💥 NUCLEAR CLEANUP COMPLETE!" -ForegroundColor Cyan
Write-Host "Press Enter to exit..." -ForegroundColor Gray
pause