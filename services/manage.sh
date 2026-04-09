#!/bin/bash
# ============================================
# Universal MCP Service Controller
# ============================================
# Script untuk manajemen terpadu seluruh layanan MCP
# Location: /home/aseps/MCP/services/manage.sh
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

ROOT_DIR="/home/aseps/MCP"
SERVICES_DIR="$ROOT_DIR/services"
MCP_DIR="$ROOT_DIR/mcp-unified"

# --- List of managed services ---
SERVICES=("mcp" "database" "vane" "waha" "serena" "dashboard" "korespondensi" "telegram")

usage() {
    echo -e "${BLUE}Usage: ./manage.sh [command] [service]${NC}"
    echo ""
    echo "Commands:"
    echo "  start [service|all]    - Start service(s)"
    echo "  stop [service|all]     - Stop service(s)"
    echo "  restart [service|all]  - Restart service(s)"
    echo "  status [service|all]   - Check service(s) status"
    echo "  logs [service]         - View service logs"
    echo ""
    echo "Services: ${SERVICES[*]}"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

CMD=$1
SVC=${2:-"all"}

# --- Service handlers ---

svc_mcp() {
    local task=$1
    case $task in
        start) 
            echo -e "${CYAN}🚀 Starting MCP Unified Hub...${NC}"
            sudo systemctl start mcp-unified || true
            ;;
        stop) 
            echo -e "${CYAN}🛑 Stopping MCP Unified Hub...${NC}"
            sudo systemctl stop mcp-unified || true
            ;;
        status)
            if systemctl is-active --quiet mcp-unified; then
                echo -e "  [mcp] ${GREEN}ACTIVE${NC} (Port 8000)"
            else
                echo -e "  [mcp] ${RED}INACTIVE${NC}"
            fi
            ;;
        logs)
            sudo journalctl -u mcp-unified -f -n 50
            ;;
    esac
}

svc_database() {
    local task=$1
    case $task in
        start)
            echo -e "${CYAN}🗄️ Starting Databases (Postgres/Redis)...${NC}"
            "$SERVICES_DIR/database/engine.sh" > /dev/null 2>&1 || true
            ;;
        stop)
            echo -e "${CYAN}🛑 Stopping Databases...${NC}"
            docker stop mcp-postgres mcp-redis 2>/dev/null || true
            ;;
        status)
            if docker ps --format '{{.Names}}' | grep -q 'mcp-postgres'; then
                echo -e "  [db]  ${GREEN}ACTIVE${NC} (Postgres/Redis)"
            else
                echo -e "  [db]  ${RED}INACTIVE${NC}"
            fi
            ;;
    esac
}

svc_vane() {
    local task=$1
    case $task in
        start)
            echo -e "${CYAN}🔍 Starting Vane AI Engine...${NC}"
            # Because we use docker run fallback in previous step
            docker start vane 2>/dev/null || echo "  ⚠️ Vane container not found"
            ;;
        stop)
            echo -e "${CYAN}🛑 Stopping Vane AI Engine...${NC}"
            docker stop vane 2>/dev/null || true
            ;;
        status)
            if docker ps --format '{{.Names}}' | grep -q 'vane'; then
                echo -e "  [vane] ${GREEN}ACTIVE${NC} (Port 3001, 8090)"
            else
                echo -e "  [vane] ${RED}INACTIVE${NC}"
            fi
            ;;
        logs)
            docker logs -f --tail 50 vane
            ;;
    esac
}

svc_waha() {
    local task=$1
    case $task in
        start)
            echo -e "${CYAN}📨 Starting WAHA WhatsApp Gateway...${NC}"
            docker start waha 2>/dev/null || echo "  ⚠️ WAHA container not found"
            ;;
        stop)
            echo -e "${CYAN}🛑 Stopping WAHA...${NC}"
            docker stop waha 2>/dev/null || true
            ;;
        status)
            if docker ps --format '{{.Names}}' | grep -q 'waha'; then
                echo -e "  [waha] ${GREEN}ACTIVE${NC} (Port 3000)"
            else
                echo -e "  [waha] ${RED}INACTIVE${NC}"
            fi
            ;;
        logs)
            docker logs -f --tail 50 waha
            ;;
    esac
}

svc_serena() {
    local task=$1
    case $task in
        status)
            if pgrep -f "serena-mcp-server" > /dev/null; then
                echo -e "  [serena] ${GREEN}ACTIVE${NC} (Process running)"
            else
                echo -e "  [serena] ${YELLOW}IDLE${NC} (Started on-demand)"
            fi
            ;;
    esac
}

svc_dashboard() {
    local task=$1
    case $task in
        status)
            if [ -f "$SERVICES_DIR/dashboard/display.py" ]; then
                echo -e "  [dash] ${GREEN}READY${NC} (Logika aktif)"
            else
                echo -e "  [dash] ${RED}MISSING${NC}"
            fi
            ;;
    esac
}

svc_korespondensi() {
    local task=$1
    case $task in
        start)
            echo -e "${CYAN}📄 Starting Korespondensi Server...${NC}"
            sudo systemctl start korespondensi-server || true
            ;;
        stop)
            echo -e "${CYAN}🛑 Stopping Korespondensi Server...${NC}"
            sudo systemctl stop korespondensi-server || true
            ;;
        status)
            if systemctl is-active --quiet korespondensi-server; then
                echo -e "  [korespondensi] ${GREEN}ACTIVE${NC} (Port 8082)"
            else
                echo -e "  [korespondensi] ${RED}INACTIVE${NC}"
            fi
            ;;
        logs)
            sudo journalctl -u korespondensi-server -f -n 50
            ;;
    esac
}

svc_telegram() {
    local task=$1
    case $task in
        start)
            echo -e "${CYAN}🤖 Starting Telegram Bot...${NC}"
            sudo systemctl start mcp-telegram-bot || true
            ;;
        stop)
            echo -e "${CYAN}🛑 Stopping Telegram Bot...${NC}"
            sudo systemctl stop mcp-telegram-bot || true
            ;;
        status)
            if systemctl is-active --quiet mcp-telegram-bot; then
                echo -e "  [telegram] ${GREEN}ACTIVE${NC} (Polling)"
            else
                echo -e "  [telegram] ${RED}INACTIVE${NC}"
            fi
            ;;
        logs)
            sudo journalctl -u mcp-telegram-bot -f -n 50
            ;;
    esac
}

# --- Dispatcher ---

handle_all() {
    local task=$1
    if [ "$task" == "status" ]; then
        echo -e "${BLUE}Unified System Status:${NC}"
        svc_database status
        svc_mcp status
        svc_vane status
        svc_waha status
        svc_korespondensi status
        svc_telegram status
        svc_serena status
        svc_dashboard status
    else
        # Sequence: DB -> Engine -> MCP -> Dependents
        svc_database "$task"
        svc_vane "$task"
        svc_waha "$task"
        svc_mcp "$task"
        svc_korespondensi "$task"
        svc_telegram "$task"
    fi
}

# Run command
case $SVC in
    all)          handle_all "$CMD" ;;
    mcp)          svc_mcp "$CMD" ;;
    database)     svc_database "$CMD" ;;
    vane)         svc_vane "$CMD" ;;
    waha)         svc_waha "$CMD" ;;
    serena)       svc_serena "$CMD" ;;
    dashboard)    svc_dashboard "$CMD" ;;
    korespondensi) svc_korespondensi "$CMD" ;;
    telegram)     svc_telegram "$CMD" ;;
    *)            echo "Unknown service: $SVC"; usage ;;
esac
