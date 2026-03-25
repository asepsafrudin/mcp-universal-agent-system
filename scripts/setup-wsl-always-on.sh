#!/bin/bash
# ============================================
# WSL Always-On Server Setup Script
# ============================================
# Script ini dijalankan dari WSL untuk setup complete
# WSL Always-On Server configuration.
#
# Usage: ./setup-wsl-always-on.sh
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   WSL Always-On Server Setup   ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ============================================
# CHECK PREREQUISITES
# ============================================
echo -e "${CYAN}Step 0: Checking prerequisites...${NC}"

# Check if running in WSL
if ! grep -qE "(Microsoft|WSL)" /proc/version 2>/dev/null; then
    echo -e "${RED}✗ This script must be run from WSL${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Running in WSL${NC}"

# Check systemd
if ! ps --pid 1 -o comm= | grep -q systemd; then
    echo -e "${RED}✗ Systemd is not running${NC}"
    echo "  Enable systemd in /etc/wsl.conf:"
    echo "    [boot]"
    echo "    systemd=true"
    echo "  Then run: wsl --shutdown"
    exit 1
fi
echo -e "${GREEN}✓ Systemd is active${NC}"

# Check Windows access
if ! powershell.exe -Command "echo test" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot access Windows PowerShell${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Windows PowerShell accessible${NC}"

# ============================================
# WSL SIDE SETUP
# ============================================
echo ""
echo -e "${CYAN}Step 1: Setting up WSL side (Health Monitor)...${NC}"

# Copy health monitor service
if [ -f "$SCRIPT_DIR/wsl-health-monitor.service" ]; then
    sudo cp "$SCRIPT_DIR/wsl-health-monitor.service" /etc/systemd/system/
    echo -e "${GREEN}✓ Copied wsl-health-monitor.service${NC}"
else
    echo -e "${RED}✗ wsl-health-monitor.service not found${NC}"
    exit 1
fi

# Reload systemd
sudo systemctl daemon-reload
echo -e "${GREEN}✓ Systemd daemon reloaded${NC}"

# Enable health monitor
sudo systemctl enable wsl-health-monitor
echo -e "${GREEN}✓ Enabled wsl-health-monitor service${NC}"

# Start health monitor (will fail if mcp-unified not ready, that's ok)
sudo systemctl start wsl-health-monitor 2>/dev/null || {
    echo -e "${YELLOW}⚠ Could not start wsl-health-monitor (mcp-unified may not be ready)${NC}"
    echo "  This is OK - it will auto-start when mcp-unified is available"
}

# Make scripts executable
chmod +x "$SCRIPT_DIR/wsl-status.sh" "$SCRIPT_DIR/wsl-restart.sh" 2>/dev/null || true
echo -e "${GREEN}✓ Made utility scripts executable${NC}"

# ============================================
# WINDOWS SIDE SETUP (via PowerShell)
# ============================================
echo ""
echo -e "${CYAN}Step 2: Setting up Windows side (Task Scheduler)...${NC}"
echo -e "${YELLOW}  This will use Windows PowerShell...${NC}"

# Get Windows username
WIN_USER=$(powershell.exe -Command '$env:USERNAME' | tr -d '\r')
echo "  Windows username: $WIN_USER"

# Create C:\Scripts directory
powershell.exe -Command "New-Item -ItemType Directory -Path 'C:\Scripts' -Force" > /dev/null 2>&1
echo -e "${GREEN}✓ Created C:\Scripts directory${NC}"

# Copy start-wsl.ps1
if [ -f "$SCRIPT_DIR/windows/start-wsl.ps1" ]; then
    # Copy via /mnt/c
    cp "$SCRIPT_DIR/windows/start-wsl.ps1" /mnt/c/Scripts/ 2>/dev/null || {
        echo -e "${YELLOW}⚠ Could not copy via /mnt/c, trying PowerShell...${NC}"
        powershell.exe -Command "Copy-Item -Path '$SCRIPT_DIR/windows/start-wsl.ps1' -Destination 'C:\Scripts\' -Force"
    }
    echo -e "${GREEN}✓ Copied start-wsl.ps1 to C:\Scripts\${NC}"
else
    echo -e "${RED}✗ start-wsl.ps1 not found${NC}"
    exit 1
fi

# Setup .wslconfig - ADD autoShutdown=false to existing or create new
echo ""
echo -e "${CYAN}Step 2b: Configuring .wslconfig...${NC}"
WIN_PROFILE="/mnt/c/Users/$WIN_USER"
WSLCONFIG_PATH="$WIN_PROFILE/.wslconfig"

if [ -f "$WSLCONFIG_PATH" ]; then
    echo "  Found existing .wslconfig"
    # Check if autoShutdown is already set
    if grep -q "autoShutdown" "$WSLCONFIG_PATH" 2>/dev/null; then
        echo -e "${GREEN}✓ autoShutdown already configured${NC}"
    else
        echo "  Adding autoShutdown=false to existing .wslconfig..."
        # Add to [experimental] section or create it
        if grep -q "^\[experimental\]" "$WSLCONFIG_PATH"; then
            # Add after [experimental] line
            sed -i '/^\[experimental\]/a autoShutdown=false' "$WSLCONFIG_PATH"
        else
            # Append new section
            echo "" >> "$WSLCONFIG_PATH"
            echo "[experimental]" >> "$WSLCONFIG_PATH"
            echo "autoShutdown=false" >> "$WSLCONFIG_PATH"
        fi
        echo -e "${GREEN}✓ Added autoShutdown=false to .wslconfig${NC}"
        echo -e "${YELLOW}  ⚠ IMPORTANT: Run 'wsl --shutdown' to apply changes!${NC}"
    fi
else
    # Copy template if no existing config
    if [ -f "$SCRIPT_DIR/windows/.wslconfig" ]; then
        cp "$SCRIPT_DIR/windows/.wslconfig" "$WSLCONFIG_PATH" 2>/dev/null || {
            echo -e "${YELLOW}⚠ Could not copy .wslconfig via /mnt/c${NC}"
        }
        echo -e "${GREEN}✓ Created new .wslconfig${NC}"
    else
        echo -e "${YELLOW}⚠ .wslconfig template not found${NC}"
    fi
fi

# Create Task Scheduler task
echo ""
echo -e "${CYAN}Step 3: Creating Windows Task Scheduler task...${NC}"

# PowerShell script to create task
TASK_SCRIPT='
$TaskName = "WSL-MCP-KeepAlive"
$ScriptPath = "C:\Scripts\start-wsl.ps1"

# Remove existing task
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create action
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`""

# Create triggers
$TriggerStartup = New-ScheduledTaskTrigger -AtStartup
$TriggerStartup.Delay = "PT2M"
$TriggerLogon = New-ScheduledTaskTrigger -AtLogon
$Triggers = @($TriggerStartup, $TriggerLogon)

# Create settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

# Create principal
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Triggers -Settings $Settings -Principal $Principal -Force
    Write-Host "Task created successfully"
    exit 0
} catch {
    Write-Host "Failed to create task: $_"
    exit 1
}
'

# Execute task creation
if powershell.exe -Command "$TASK_SCRIPT" 2>/dev/null; then
    echo -e "${GREEN}✓ Created Task Scheduler task 'WSL-MCP-KeepAlive'${NC}"
else
    echo -e "${YELLOW}⚠ Could not create task automatically${NC}"
    echo "  Please run manually from PowerShell Admin:"
    echo "    $SCRIPT_DIR/windows/setup-task-scheduler.ps1"
fi

# ============================================
# VERIFICATION
# ============================================
echo ""
echo -e "${CYAN}Step 4: Verification...${NC}"

# Check Task Scheduler task
TASK_EXISTS=$(powershell.exe -Command "Get-ScheduledTask -TaskName 'WSL-MCP-KeepAlive' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty TaskName" 2>/dev/null | tr -d '\r')
if [ "$TASK_EXISTS" = "WSL-MCP-KeepAlive" ]; then
    echo -e "${GREEN}✓ Task Scheduler task exists${NC}"
else
    echo -e "${YELLOW}⚠ Task Scheduler task not found${NC}"
fi

# Check health monitor service
if systemctl is-enabled wsl-health-monitor >/dev/null 2>&1; then
    echo -e "${GREEN}✓ wsl-health-monitor is enabled${NC}"
else
    echo -e "${YELLOW}⚠ wsl-health-monitor is not enabled${NC}"
fi

# ============================================
# SUMMARY
# ============================================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   Setup Complete!   ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo ""
echo "1. ${YELLOW}Restart WSL${NC} to apply .wslconfig changes:"
echo "   ${GREEN}wsl.exe --shutdown${NC}"
echo "   Tunggu 10 detik, lalu buka WSL lagi"
echo ""
echo "2. ${YELLOW}Test the setup:${NC}"
echo "   ${GREEN}./scripts/wsl-status.sh${NC}"
echo ""
echo "3. ${YELLOW}Restart Windows untuk test auto-start:${NC}"
echo "   Setelah reboot, cek apakah MCP berjalan:"
echo "   ${GREEN}curl http://localhost:8000/health${NC}"
echo ""
echo -e "${CYAN}Useful Commands:${NC}"
echo "  Check status:    ${GREEN}./scripts/wsl-status.sh${NC}"
echo "  Restart MCP:     ${GREEN}./scripts/wsl-restart.sh${NC}"
echo "  Full WSL restart:${GREEN}./scripts/wsl-restart.sh --full${NC}"
echo "  View logs:       ${GREEN}sudo journalctl -u mcp-unified -f${NC}"
echo "  Windows logs:    ${GREEN}Get-Content C:\Scripts\wsl-keepalive.log -Tail 20${NC}"
echo ""
echo -e "${CYAN}Documentation:${NC}"
echo "  ${GREEN}docs/04-operations/wsl-always-on-server.md${NC}"
echo ""
