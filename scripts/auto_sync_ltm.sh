#!/bin/bash
# Auto Sync LTM - Sinkronisasi berkala antara file dan database
# 
# Usage: ./auto_sync_ltm.sh
# Setup cron: */5 * * * * /home/aseps/MCP/scripts/auto_sync_ltm.sh

set -e

echo "🔄 Auto Sync LTM - $(date)"
echo "================================"

cd /home/aseps/MCP

# Sync file LTM ke PostgreSQL
python3 scripts/sync_ltm_to_postgres.py --quiet 2>/dev/null || echo "⚠️ File to DB sync skipped"

# Sync Telegram data
python3 scripts/insert_telegram_ltm.py --quiet 2>/dev/null || echo "⚠️ Telegram sync skipped"

echo "✅ Auto sync completed at $(date)"
echo ""
