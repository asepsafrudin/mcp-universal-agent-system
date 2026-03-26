#!/bin/bash
# ============================================
# WSL + MCP Status Checker
# ============================================
# Script untuk cek status WSL dan MCP Unified Hub
# Usage: ./wsl-status.sh
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   WSL + MCP Unified Hub Status Check   ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check WSL version
echo -e "${BLUE}WSL Version:${NC}"
wsl.exe --version 2>/dev/null || echo "  WSL not detected from Linux side"

# Check systemd
echo ""
echo -e "${BLUE}Systemd Status:${NC}"
if ps --pid 1 -o comm= | grep -q systemd; then
    echo -e "  ${GREEN}✓ Systemd is running${NC}"
else
    echo -e "  ${RED}✗ Systemd is NOT running${NC}"
    echo "    Run: sudo systemctl set-default multi-user.target"
fi

# Check MCP service
echo ""
echo -e "${BLUE}MCP Unified Service:${NC}"
if systemctl is-active --quiet mcp-unified; then
    echo -e "  ${GREEN}✓ mcp-unified is active${NC}"
    systemctl status mcp-unified --no-pager | grep -E "(Active|Memory|CPU)" || true
else
    echo -e "  ${RED}✗ mcp-unified is NOT active${NC}"
fi

# Check Health Monitor service
echo ""
echo -e "${BLUE}WSL Health Monitor:${NC}"
if systemctl is-active --quiet wsl-health-monitor 2>/dev/null; then
    echo -e "  ${GREEN}✓ wsl-health-monitor is active${NC}"
else
    echo -e "  ${YELLOW}⚠ wsl-health-monitor is NOT active (optional)${NC}"
fi

# Check HTTP endpoint
echo ""
echo -e "${BLUE}HTTP Health Check (localhost:8000):${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health)
    echo -e "  ${GREEN}✓ MCP server is responding${NC}"
    echo "    Tools available: $(echo $HEALTH | grep -o '"tools_available":[0-9]*' | cut -d: -f2)"
else
    echo -e "  ${RED}✗ MCP server is NOT responding${NC}"
fi

# Check PostgreSQL
echo ""
echo -e "${BLUE}PostgreSQL (Docker):${NC}"
if docker ps | grep -q mcp-postgres; then
    echo -e "  ${GREEN}✓ mcp-postgres container is running${NC}"
else
    echo -e "  ${YELLOW}⚠ mcp-postgres container is NOT running${NC}"
fi

# Check Redis
echo ""
echo -e "${BLUE}Redis (Docker):${NC}"
if docker ps | grep -q mcp-redis; then
    echo -e "  ${GREEN}✓ mcp-redis container is running${NC}"
else
    echo -e "  ${YELLOW}⚠ mcp-redis container is NOT running${NC}"
fi

# Check Vane AI Search
echo ""
echo -e "${BLUE}Vane AI Search (Docker):${NC}"
if docker ps | grep -q vane; then
    echo -e "  ${GREEN}✓ vane container is running (Port 3001, 8090)${NC}"
else
    echo -e "  ${YELLOW}⚠ vane container is NOT running${NC}"
fi

# Check WAHA (WhatsApp)
echo ""
echo -e "${BLUE}WAHA WhatsApp Gateway (Docker):${NC}"
if docker ps | grep -q waha; then
    echo -e "  ${GREEN}✓ waha container is running (Port 3000)${NC}"
else
    echo -e "  ${YELLOW}⚠ waha container is NOT running${NC}"
fi

# Check Serena
echo ""
echo -e "${BLUE}Serena Coding Toolkit:${NC}"
if [ -d "/home/aseps/MCP/services/serena" ]; then
    echo -e "  ${GREEN}✓ serena directory exists in services/${NC}"
    if pgrep -f "serena-mcp-server" > /dev/null; then
        echo -e "  ${GREEN}✓ serena-mcp-server process is active${NC}"
    else
        echo -e "  ${YELLOW}ℹ serena-mcp-server is not running (started on-demand)${NC}"
    fi
else
    echo -e "  ${RED}✗ serena directory NOT found in services/${NC}"
fi

# Check Doc Processor
echo ""
echo -e "${BLUE}Document Processor Engine:${NC}"
if [ -f "/home/aseps/MCP/services/doc-processor/paddle_ocr.py" ]; then
    echo -e "  ${GREEN}✓ Doc-Processor (PaddleOCR) engine is ready${NC}"
else
    echo -e "  ${YELLOW}⚠ Doc-Processor engine not found in services/${NC}"
fi

# Check Google Workspace Service
echo ""
echo -e "${BLUE}Google Workspace Service:${NC}"
if [ -d "/home/aseps/MCP/services/google" ]; then
    echo -e "  ${GREEN}✓ Google service interface exists${NC}"
    if [ -d "/home/aseps/MCP/config/credentials/google" ]; then
        echo -e "  ${GREEN}✓ Google credentials directory found${NC}"
    fi
else
    echo -e "  ${RED}✗ Google service NOT found in services/${NC}"
fi

# Check resources
echo ""
echo -e "${BLUE}Resource Usage:${NC}"
echo "  Memory:"
free -h | grep -E "Mem|Swap" | sed 's/^/    /'

echo ""
echo "  Disk:"
df -h /home/aseps/MCP | tail -1 | sed 's/^/    /'

echo ""
echo -e "${BLUE}========================================${NC}"
echo "Check complete. Run 'sudo systemctl status mcp-unified' for details."
