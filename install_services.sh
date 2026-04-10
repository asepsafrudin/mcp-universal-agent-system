#!/bin/bash
# ============================================
# MCP Services Installer
# Instal & aktifkan ketiga service pendukung mcp-unified:
#   1. korespondensi-server  (port 8082)
#   2. vane-ai               (Docker container)
#   3. mcp-telegram-bot      (Telegram bot)
#
# Usage: sudo bash install_services.sh
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN} MCP Services Installer${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

SRC_DIR="/home/aseps/MCP"

# --- 1. Copy service files ke /etc/systemd/system/ ---
echo -e "${YELLOW}📋 Menyalin unit file ke systemd...${NC}"
cp "$SRC_DIR/korespondensi-server/korespondensi-server.service" /etc/systemd/system/
cp "$SRC_DIR/services/vane/vane-ai.service" /etc/systemd/system/
cp "$SRC_DIR/mcp-unified/integrations/telegram/mcp-telegram-bot.service" /etc/systemd/system/
echo -e "  ${GREEN}✓${NC} korespondensi-server.service"
echo -e "  ${GREEN}✓${NC} vane-ai.service"
echo -e "  ${GREEN}✓${NC} mcp-telegram-bot.service"

# --- 2. Reload daemon ---
echo ""
echo -e "${YELLOW}🔄 Reload systemd daemon...${NC}"
systemctl daemon-reload
echo -e "  ${GREEN}✓${NC} daemon-reload selesai"

# --- 3. Enable auto-start ---
echo ""
echo -e "${YELLOW}🔧 Mengaktifkan auto-start saat boot...${NC}"
systemctl enable korespondensi-server vane-ai mcp-telegram-bot
echo -e "  ${GREEN}✓${NC} Ketiga service enabled"

# --- 4. Start services ---
echo ""
echo -e "${YELLOW}🚀 Menjalankan service sekarang...${NC}"

echo -n "  [vane-ai] Memulai... "
systemctl start vane-ai && echo -e "${GREEN}OK${NC}" || echo -e "${RED}FAILED${NC}"

sleep 2

echo -n "  [korespondensi-server] Memulai... "
systemctl start korespondensi-server && echo -e "${GREEN}OK${NC}" || echo -e "${RED}FAILED${NC}"

sleep 2

echo -n "  [mcp-telegram-bot] Memulai... "
systemctl start mcp-telegram-bot && echo -e "${GREEN}OK${NC}" || echo -e "${RED}FAILED${NC}"

# --- 5. Status akhir ---
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN} Status Akhir${NC}"
echo -e "${CYAN}============================================${NC}"

for svc in mcp-unified korespondensi-server vane-ai mcp-telegram-bot; do
    if systemctl is-active --quiet "$svc"; then
        echo -e "  [$svc] ${GREEN}ACTIVE ✓${NC}"
    else
        echo -e "  [$svc] ${RED}INACTIVE ✗${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ Instalasi selesai!${NC}"
echo ""
echo "Perintah berguna:"
echo "  sudo systemctl status korespondensi-server"
echo "  sudo systemctl status vane-ai"
echo "  sudo systemctl status mcp-telegram-bot"
echo "  sudo journalctl -u korespondensi-server -f"
