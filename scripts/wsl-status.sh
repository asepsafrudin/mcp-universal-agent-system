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
if docker ps | grep -q mcp-pg; then
    echo -e "  ${GREEN}✓ mcp-pg container is running${NC}"
else
    echo -e "  ${YELLOW}⚠ mcp-pg container is NOT running${NC}"
fi

# Check Redis
echo ""
echo -e "${BLUE}Redis (Docker):${NC}"
if docker ps | grep -q redis; then
    echo -e "  ${GREEN}✓ redis container is running${NC}"
else
    echo -e "  ${YELLOW}⚠ redis container is NOT running${NC}"
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
