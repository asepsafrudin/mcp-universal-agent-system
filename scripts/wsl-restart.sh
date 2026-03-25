#!/bin/bash
# ============================================
# WSL + MCP Force Restart Script
# ============================================
# Script untuk restart paksa WSL dan MCP services
# Usage: ./wsl-restart.sh [--full]
#
# Options:
#   --full    Restart entire WSL instance (Windows side)
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FULL_RESTART=false

# Parse arguments
if [ "$1" == "--full" ]; then
    FULL_RESTART=true
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   WSL + MCP Force Restart   ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$FULL_RESTART" = true ]; then
    echo -e "${YELLOW}⚠ FULL WSL RESTART requested${NC}"
    echo "This will shutdown and restart the entire WSL instance."
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    
    echo -e "${BLUE}Shutting down WSL...${NC}"
    wsl.exe --shutdown
    
    echo -e "${BLUE}Waiting 5 seconds...${NC}"
    sleep 5
    
    echo -e "${BLUE}Starting WSL...${NC}"
    wsl.exe -d Ubuntu -- bash -c "echo 'WSL Restarted'"
    
    echo -e "${GREEN}✓ WSL restarted. Please re-run this script without --full to start services.${NC}"
    exit 0
fi

# Normal restart - just services
echo -e "${BLUE}Step 1: Stopping MCP services...${NC}"
sudo systemctl stop wsl-health-monitor 2>/dev/null || true
sudo systemctl stop mcp-unified 2>/dev/null || true
echo -e "${GREEN}✓ Services stopped${NC}"

echo ""
echo -e "${BLUE}Step 2: Checking dependencies...${NC}"

# Check PostgreSQL
if ! docker ps | grep -q mcp-pg; then
    echo -e "${YELLOW}⚠ Starting PostgreSQL...${NC}"
    docker start mcp-pg 2>/dev/null || echo "  Container not found, may need manual setup"
else
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
fi

# Check Redis
if ! docker ps | grep -q redis; then
    echo -e "${YELLOW}⚠ Starting Redis...${NC}"
    docker start redis 2>/dev/null || echo "  Container not found, may need manual setup"
else
    echo -e "${GREEN}✓ Redis is running${NC}"
fi

echo ""
echo -e "${BLUE}Step 3: Starting MCP services...${NC}"
sudo systemctl daemon-reload
sudo systemctl start mcp-unified
sleep 3

# Verify MCP started
if systemctl is-active --quiet mcp-unified; then
    echo -e "${GREEN}✓ mcp-unified started${NC}"
else
    echo -e "${RED}✗ mcp-unified failed to start${NC}"
    echo "Check logs: sudo journalctl -u mcp-unified -n 50"
    exit 1
fi

# Optional: Start health monitor
sudo systemctl start wsl-health-monitor 2>/dev/null || true

echo ""
echo -e "${BLUE}Step 4: Verifying health endpoint...${NC}"
sleep 3

for i in {1..5}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ MCP server is responding${NC}"
        curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || true
        break
    else
        echo "  Attempt $i/5..."
        sleep 2
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Restart complete!${NC}"
echo ""
echo "Commands:"
echo "  Check status:   ./wsl-status.sh"
echo "  View logs:      sudo journalctl -u mcp-unified -f"
echo "  Health check:   curl http://localhost:8000/health"
