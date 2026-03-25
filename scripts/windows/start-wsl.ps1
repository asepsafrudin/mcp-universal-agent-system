#requires -RunAsAdministrator
<#
.SYNOPSIS
    WSL Keep-Alive Script untuk MCP Unified Hub
.DESCRIPTION
    Script ini menjalankan WSL dan memastikan MCP service berjalan.
    Dijalankan via Task Scheduler setiap 5 menit untuk health check.
    
    Lokasi: C:\Scripts\start-wsl.ps1
    
.USAGE
    PowerShell.exe -ExecutionPolicy Bypass -File "C:\Scripts\start-wsl.ps1"
    
.NOTES
    Author: MCP Unified Setup
    Version: 1.0
    Interval: 5 menit (dikonfigurasi di Task Scheduler)
#>

# ============================================
# Configuration
# ============================================
$WSL_DISTRO = "Ubuntu"  # Ganti sesuai distro WSL Anda
$MCP_SERVICE = "mcp-unified"
$LOG_FILE = "C:\Scripts\wsl-keepalive.log"
$MAX_LOG_SIZE = 10MB

# ============================================
# Logging Function
# ============================================
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to console
    if ($Level -eq "ERROR") {
        Write-Host $logEntry -ForegroundColor Red
    } elseif ($Level -eq "WARN") {
        Write-Host $logEntry -ForegroundColor Yellow
    } else {
        Write-Host $logEntry -ForegroundColor Green
    }
    
    # Write to file
    Add-Content -Path $LOG_FILE -Value $logEntry -ErrorAction SilentlyContinue
}

# ============================================
# Log Rotation
# ============================================
function Rotate-Log {
    if (Test-Path $LOG_FILE) {
        $logSize = (Get-Item $LOG_FILE).Length
        if ($logSize -gt $MAX_LOG_SIZE) {
            $backup = "$LOG_FILE.old"
            Move-Item $LOG_FILE $backup -Force
            Write-Log "Log file rotated"
        }
    }
}

# ============================================
# Main Script
# ============================================
Rotate-Log
Write-Log "=== WSL Keep-Alive Check Started ==="

try {
    # Check if WSL is running
    $wslStatus = wsl --list --running --quiet 2>$null
    $isRunning = $wslStatus -contains $WSL_DISTRO
    
    if (-not $isRunning) {
        Write-Log "WSL $WSL_DISTRO not running. Starting..." "WARN"
        
        # Start WSL
        wsl -d $WSL_DISTRO -- bash -c "echo 'WSL Started'" 2>&1 | Out-Null
        Start-Sleep -Seconds 5
        
        # Verify WSL started
        $wslStatus = wsl --list --running --quiet 2>$null
        if ($wslStatus -contains $WSL_DISTRO) {
            Write-Log "WSL $WSL_DISTRO started successfully"
        } else {
            Write-Log "Failed to start WSL $WSL_DISTRO" "ERROR"
            exit 1
        }
    } else {
        Write-Log "WSL $WSL_DISTRO is already running"
    }
    
    # Check MCP service status
    $serviceStatus = wsl -d $WSL_DISTRO -- systemctl is-active $MCP_SERVICE 2>$null
    
    if ($serviceStatus -ne "active") {
        Write-Log "MCP service not active. Starting..." "WARN"
        
        # Start MCP service
        wsl -d $WSL_DISTRO -- sudo systemctl start $MCP_SERVICE 2>&1 | Out-Null
        Start-Sleep -Seconds 3
        
        # Verify service started
        $serviceStatus = wsl -d $WSL_DISTRO -- systemctl is-active $MCP_SERVICE 2>$null
        if ($serviceStatus -eq "active") {
            Write-Log "MCP service started successfully"
        } else {
            Write-Log "Failed to start MCP service" "ERROR"
        }
    } else {
        Write-Log "MCP service is active"
    }
    
    # Health check via curl (if available in WSL)
    $healthCheck = wsl -d $WSL_DISTRO -- bash -c "curl -s http://localhost:8000/health 2>/dev/null || echo 'unhealthy'" 2>$null
    
    if ($healthCheck -like '*"status": "healthy"*') {
        Write-Log "Health check: PASSED"
    } else {
        Write-Log "Health check: FAILED - MCP server may not be responding" "WARN"
        # Attempt restart
        wsl -d $WSL_DISTRO -- sudo systemctl restart $MCP_SERVICE 2>&1 | Out-Null
        Write-Log "Attempted MCP service restart"
    }
    
} catch {
    Write-Log "Error occurred: $_" "ERROR"
    exit 1
}

Write-Log "=== WSL Keep-Alive Check Completed ==="
