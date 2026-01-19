# product-documenter/scripts/enhanced_backup.ps1
# SAFE BACKUP - PRESERVES YOUR WORKING SYSTEM

param(
    [string]$BackupType = "daily"
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = "$PSScriptRoot\..\..\backups"
$backupDir = "$backupRoot\$timestamp"

Write-Host "ENHANCED BACKUP" -ForegroundColor Cyan
Write-Host "Backup type: $BackupType" -ForegroundColor Gray
Write-Host "=" * 50

# 1. Create backup directory
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# 2. Backup CRITICAL files only
$backupItems = @(
    @{ Path = "$PSScriptRoot\*.json"; Description = "Configuration files" },
    @{ Path = "$PSScriptRoot\..\logs\*"; Description = "Log files" },
    @{ Path = "$PSScriptRoot\..\data\*"; Description = "Data files" },
    @{ Path = "$PSScriptRoot\*.ps1"; Description = "PowerShell scripts" },
    @{ Path = "$PSScriptRoot\*.py"; Description = "Python scripts" }
)

foreach ($item in $backupItems) {
    if (Test-Path $item.Path) {
        Copy-Item -Path $item.Path -Destination "$backupDir\" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "OK $($item.Description)" -ForegroundColor Green
    } else {
        Write-Host "SKIPPED: $($item.Description)" -ForegroundColor Yellow
    }
}

# 3. Create restore script
$restoreScript = @"
# RESTORE SCRIPT - Generated $timestamp
Write-Host "RESTORING BACKUP FROM $timestamp" -ForegroundColor Cyan

`$backupSource = "`$PSScriptRoot"
`$projectRoot = "$PSScriptRoot\..\.."

Write-Host "Source: `$backupSource" -ForegroundColor Gray
Write-Host "Target: `$projectRoot" -ForegroundColor Gray

# Restore files
Copy-Item -Path "`$backupSource\*" -Destination "`$projectRoot\product-documenter\" -Recurse -Force

Write-Host "Restore completed!" -ForegroundColor Green
Write-Host "Run: .\start_monitoring.ps1" -ForegroundColor Gray
"@

$restoreScript | Out-File -FilePath "$backupDir\RESTORE_INSTRUCTIONS.ps1"

# 4. Summary
$totalSize = [math]::Round((Get-ChildItem $backupDir -Recurse | Measure-Object Length -Sum).Sum / 1MB, 2)

Write-Host "`nBACKUP COMPLETE" -ForegroundColor Cyan
Write-Host "Location: $backupDir" -ForegroundColor Gray
Write-Host "Size: $totalSize MB" -ForegroundColor Gray
Write-Host "Files: $(Get-ChildItem $backupDir -Recurse -File | Measure-Object).Count" -ForegroundColor Gray

# 5. Cleanup old backups
if ($BackupType -eq "daily") {
    Get-ChildItem $backupRoot -Directory | 
        Sort-Object CreationTime -Descending | 
        Select-Object -Skip 7 | 
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Kept latest 7 daily backups" -ForegroundColor Yellow
}

Write-Host "`nTO RESTORE:" -ForegroundColor Cyan
Write-Host "1. Go to: $backupDir" -ForegroundColor Gray
Write-Host "2. Run: .\RESTORE_INSTRUCTIONS.ps1" -ForegroundColor Gray