# product-documenter/scripts/health_check.ps1
# NON-INVASIVE HEALTH CHECK FOR EXISTING SYSTEM

Write-Host "EXISTING SYSTEM HEALTH CHECK" -ForegroundColor Cyan
Write-Host "=" * 50

$issues = @()
$warnings = @()

# 1. Check if critical processes are running
Write-Host "`nPROCESS CHECK:" -ForegroundColor Yellow

$processes = @("python", "streamlit", "powershell")
foreach ($proc in $processes) {
    $count = (Get-Process $proc -ErrorAction SilentlyContinue).Count
    if ($count -gt 0) {
        Write-Host "OK $proc : $count process(es) running" -ForegroundColor Green
    } else {
        Write-Host "WARNING $proc : No processes found (might be normal)" -ForegroundColor Yellow
        $warnings += "$proc not running"
    }
}

# 2. Check if ports are in use
Write-Host "`nPORT CHECK:" -ForegroundColor Yellow

$ports = @(8000, 8501)
foreach ($port in $ports) {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            Write-Host "OK Port $port : IN USE (Good)" -ForegroundColor Green
        } else {
            Write-Host "ERROR Port $port : NOT IN USE" -ForegroundColor Red
            $issues += "Port $port not in use - API/Dashboard might be down"
        }
    } catch {
        Write-Host "UNKNOWN Port $port : Check failed" -ForegroundColor Gray
    }
}

# 3. Check log files
Write-Host "`nLOG CHECK:" -ForegroundColor Yellow

$logDir = "$PSScriptRoot\..\logs"
if (Test-Path $logDir) {
    $recentLogs = Get-ChildItem $logDir -Filter "*.log" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 3
    if ($recentLogs) {
        Write-Host "OK Log directory: $logDir" -ForegroundColor Green
        foreach ($log in $recentLogs) {
            $age = (Get-Date) - $log.LastWriteTime
            $ageText = if ($age.TotalHours -lt 1) { "just now" } 
                      elseif ($age.TotalHours -lt 24) { "$([math]::Round($age.TotalHours,1)) hours ago" }
                      else { "$([math]::Round($age.TotalDays,1)) days ago" }
            
            Write-Host "   - $($log.Name) : Updated $ageText" -ForegroundColor Gray
        }
    } else {
        Write-Host "WARNING No log files found" -ForegroundColor Yellow
        $warnings += "No log files found"
    }
} else {
    # AUTO-CREATE missing directory
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    Write-Host "CREATED Log directory: $logDir" -ForegroundColor Green
    $warnings += "Created missing log directory"
}

# 4. Check data directory
Write-Host "`nDATA CHECK:" -ForegroundColor Yellow

$dataDir = "$PSScriptRoot\..\data"
if (Test-Path $dataDir) {
    $fileCount = (Get-ChildItem $dataDir -Recurse -File).Count
    Write-Host "OK Data directory: $fileCount files" -ForegroundColor Green
} else {
    # AUTO-CREATE missing directory
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    Write-Host "CREATED Data directory: $dataDir" -ForegroundColor Green
    $warnings += "Created missing data directory"
}

# 5. Summary
Write-Host "`n" + "=" * 50
Write-Host "HEALTH SUMMARY" -ForegroundColor Cyan

if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "SYSTEM IS HEALTHY" -ForegroundColor Green
    Write-Host "   All checks passed!" -ForegroundColor Gray
} else {
    if ($issues.Count -gt 0) {
        Write-Host "CRITICAL ISSUES FOUND ($($issues.Count)):" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "   * $issue" -ForegroundColor Red
        }
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "WARNINGS ($($warnings.Count)):" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "   * $warning" -ForegroundColor Yellow
        }
    }
}

Write-Host "`nRECOMMENDED ACTIONS:" -ForegroundColor Cyan
if ($issues.Count -gt 0) {
    Write-Host "1. Restart the system: .\start_monitoring.ps1" -ForegroundColor Gray
}
Write-Host "2. Check recent activity in dashboard: http://localhost:8501" -ForegroundColor Gray
Write-Host "3. Verify API is responding: http://localhost:8000/health" -ForegroundColor Gray

Write-Host "`nTIP: Run this daily to catch issues early!" -ForegroundColor Cyan