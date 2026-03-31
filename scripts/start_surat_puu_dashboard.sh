#!/bin/bash
# ============================================================
# Start Surat PUU Management Dashboard
# URL: http://localhost:8081/surat-puu/dashboard
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$(dirname "$SCRIPT_DIR")"
APP_PATH="$MCP_DIR/mcp-unified/knowledge/admin/surat_puu_app.py"
LOG_FILE="/tmp/surat_puu_dashboard.log"
PID_FILE="/tmp/surat_puu_dashboard.pid"

# Check if already running via PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "✅ Dashboard sudah berjalan (PID: $PID)"
        echo "📍 URL: http://localhost:8081/surat-puu/dashboard"
        exit 0
    fi
fi

# Also check if port 8081 is in use by any process
if lsof -ti:8081 > /dev/null 2>&1; then
    EXISTING_PID=$(lsof -ti:8081)
    echo "⚠️  Port 8081 sudah dipakai oleh PID $EXISTING_PID"
    echo "   Jalankan: kill $EXISTING_PID  untuk menghentikannya"
    echo "   Atau gunakan: kill \$(lsof -t -i:8081) && bash $0"
    # Save PID anyway so script knows about it
    echo "$EXISTING_PID" > "$PID_FILE"
    echo "📍 URL: http://localhost:8081/surat-puu/dashboard"
    exit 0
fi

# Set default credentials (override via env vars)
export MCP_ADMIN_PASSWORD="${MCP_ADMIN_PASSWORD:-admin123}"
export MCP_REVIEWER_PASSWORD="${MCP_REVIEWER_PASSWORD:-reviewer123}"
export MCP_VIEWER_PASSWORD="${MCP_VIEWER_PASSWORD:-viewer123}"

# Start the server
echo "🚀 Starting Surat PUU Dashboard..."
PYTHONPATH="$MCP_DIR/mcp-unified" nohup python3 "$APP_PATH" > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

# Wait for startup
sleep 2

# Check if started
if kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
    echo "✅ Dashboard started successfully!"
    echo "📍 URL: http://localhost:8081/surat-puu/dashboard"
    echo "🔐 Login: admin / ${MCP_ADMIN_PASSWORD}"
    echo "📄 Log: $LOG_FILE"
else
    echo "❌ Failed to start! Check log: $LOG_FILE"
    tail -20 "$LOG_FILE"
    exit 1
fi
