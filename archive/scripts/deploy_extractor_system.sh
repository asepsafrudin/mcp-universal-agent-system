#!/bin/bash
# Deploy Extractor System to Production
# Usage: ./deploy_extractor_system.sh

set -e

echo "============================================================"
echo "🚀 DEPLOYING EXTRACTOR SYSTEM TO PRODUCTION"
echo "============================================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Checking dependencies...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

# Check Playwright
if ! python3 -c "import playwright" 2>/dev/null; then
    echo "⚠️  Playwright not installed, installing..."
    pip3 install playwright
    python3 -m playwright install chromium
fi
echo "✅ Playwright: OK"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found"
else
    echo "✅ PostgreSQL: OK"
fi

echo -e "${BLUE}Step 2: Setting up directories...${NC}"

# Create necessary directories
mkdir -p ~/.mcp/extractors
mkdir -p ~/logs/extractor
mkdir -p ~/data/extractions

echo "✅ Directories created"

echo -e "${BLUE}Step 3: Installing systemd service...${NC}"

# Create systemd service file
sudo tee /etc/systemd/system/extractor-scheduler.service > /dev/null <<EOF
[Unit]
Description=Extractor System Scheduler
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/aseps/MCP
Environment=PYTHONPATH=/home/aseps/MCP/mcp-unified/integrations/agentic_ai
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 /home/aseps/MCP/run_production_extraction.py --all --save
Restart=on-failure
RestartSec=3600
StandardOutput=append:/home/aseps/logs/extractor/scheduler.log
StandardError=append:/home/aseps/logs/extractor/scheduler-error.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd service created"

echo -e "${BLUE}Step 4: Enabling service...${NC}"

sudo systemctl daemon-reload
sudo systemctl enable extractor-scheduler.service

echo "✅ Service enabled"

echo -e "${BLUE}Step 5: Testing extraction (dry run)...${NC}"

# Test without saving
cd /home/aseps/MCP
python3 run_production_extraction.py --source hukumonline || echo "⚠️  Test extraction failed, but continuing..."

echo -e "${BLUE}Step 6: Creating cron job for regular extraction...${NC}"

# Add cron job for daily extraction at 6 AM
(crontab -l 2>/dev/null | grep -v "run_production_extraction.py"; echo "0 6 * * * cd /home/aseps/MCP && /usr/bin/python3 run_production_extraction.py --all --save >> ~/logs/extractor/cron.log 2>&1") | crontab -

echo "✅ Cron job added (daily at 6 AM)"

echo ""
echo "============================================================"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "============================================================"
echo ""
echo "System Status:"
echo "  • Service: extractor-scheduler.service"
echo "  • Config: /etc/systemd/system/extractor-scheduler.service"
echo "  • Logs: ~/logs/extractor/"
echo "  • Data: ~/data/extractions/"
echo ""
echo "Commands:"
echo "  sudo systemctl start extractor-scheduler  # Start now"
echo "  sudo systemctl status extractor-scheduler # Check status"
echo "  sudo systemctl stop extractor-scheduler   # Stop"
echo ""
echo "Manual extraction:"
echo "  python3 run_production_extraction.py --source hukumonline --save"
echo "  python3 run_production_extraction.py --all --save"
echo ""
echo "============================================================"
