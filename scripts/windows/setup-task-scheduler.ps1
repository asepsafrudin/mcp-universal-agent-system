#requires -RunAsAdministrator
<#
.SYNOPSIS
    Setup Task Scheduler untuk WSL Keep-Alive
.DESCRIPTION
    Script ini membuat scheduled task yang menjalankan WSL keep-alive
check setiap 5 menit.
    
    Run sebagai Administrator:
    PowerShell.exe -ExecutionPolicy Bypass -File "setup-task-scheduler.ps1"
    
.NOTES
    Author: MCP Unified Setup
    Version: 1.0
#>

# ============================================
# Configuration
# ============================================
$TaskName = "WSL-MCP-KeepAlive"
$ScriptPath = "C:\Scripts\start-wsl.ps1"
$Description = "Keep WSL and MCP Unified Hub running (health check every 5 min)"

# ============================================
# Ensure script directory exists
# ============================================
$ScriptDir = Split-Path $ScriptPath -Parent
if (-not (Test-Path $ScriptDir)) {
    New-Item -ItemType Directory -Path $ScriptDir -Force | Out-Null
    Write-Host "Created directory: $ScriptDir" -ForegroundColor Green
}

# ============================================
# Check if script exists
# ============================================
if (-not (Test-Path $ScriptPath)) {
    Write-Host "ERROR: Script not found at $ScriptPath" -ForegroundColor Red
    Write-Host "Please copy start-wsl.ps1 to $ScriptPath first" -ForegroundColor Yellow
    exit 1
}

# ============================================
# Remove existing task if exists
# ============================================
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task: $TaskName" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# ============================================
# Create Action
# ============================================
$Action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`""

# ============================================
# Create Triggers
# ============================================
# Trigger 1: At startup (with 2 min delay)
$TriggerStartup = New-ScheduledTaskTrigger `
    -AtStartup
$TriggerStartup.Delay = "PT2M"  # 2 minutes delay

# Trigger 2: At logon
$TriggerLogon = New-ScheduledTaskTrigger `
    -AtLogon

# Trigger 3: Every 5 minutes (repetition)
$TriggerRepeat = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 365)

$Triggers = @($TriggerStartup, $TriggerLogon, $TriggerRepeat)

# ============================================
# Create Settings
# ============================================
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# ============================================
# Create Principal (Run as SYSTEM with highest privileges)
# ============================================
$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# ============================================
# Register Task
# ============================================
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $Description `
        -Action $Action `
        -Trigger $Triggers `
        -Settings $Settings `
        -Principal $Principal `
        -Force
    
    Write-Host "`n✓ Task '$TaskName' created successfully!" -ForegroundColor Green
    Write-Host "`nTask Details:" -ForegroundColor Cyan
    Write-Host "  - Name: $TaskName"
    Write-Host "  - Script: $ScriptPath"
    Write-Host "  - Interval: Every 5 minutes"
    Write-Host "  - Startup: Yes (with 2 min delay)"
    Write-Host "  - Logon: Yes"
    Write-Host "  - Run as: SYSTEM"
    
    Write-Host "`nTo verify:" -ForegroundColor Cyan
    Write-Host "  1. Open Task Scheduler (taskschd.msc)"
    Write-Host "  2. Look for '$TaskName' in the list"
    Write-Host "  3. Right-click → Run to test"
    
    Write-Host "`nTo check logs:" -ForegroundColor Cyan
    Write-Host "  Get-Content C:\Scripts\wsl-keepalive.log -Tail 20"
    
} catch {
    Write-Host "`n✗ Failed to create task: $_" -ForegroundColor Red
    exit 1
}
