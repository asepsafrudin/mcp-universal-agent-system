#!/bin/bash

BACKUP_DIR="$HOME/MCP/backups"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

mkdir -p "$BACKUP_DIR"

echo "🔄 Starting backup at $TIMESTAMP..."

# Backup PostgreSQL
# Assuming container name 'mcp-pg' as per user guide. 
# Check if running first to avoid script failure spam
if docker ps | grep -q mcp-pg; then
    docker exec mcp-pg pg_dump -U aseps mcp | gzip > "$BACKUP_DIR/mcp_db_$TIMESTAMP.sql.gz"
else
    echo "⚠️  PostgreSQL container 'mcp-pg' not found. Skipping DB backup."
fi

# Backup configuration
# Using wildcard or checking file existence to prevent tar errors
FILES_TO_BACKUP=""
[ -f "$HOME/MCP/mcp-unified/config.py" ] && FILES_TO_BACKUP="$FILES_TO_BACKUP $HOME/MCP/mcp-unified/config.py"
[ -f "$HOME/MCP/antigravity-mcp-config.json" ] && FILES_TO_BACKUP="$FILES_TO_BACKUP $HOME/MCP/antigravity-mcp-config.json"

if [ ! -z "$FILES_TO_BACKUP" ]; then
    tar -czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" $FILES_TO_BACKUP
fi

# Backup logs (last 7 days)
# Ensure logs dir exists
if [ -d "$HOME/MCP/logs" ]; then
    find "$HOME/MCP/logs" -name "*.log" -mtime -7 | tar -czf "$BACKUP_DIR/logs_$TIMESTAMP.tar.gz" -T - --no-recursion 2>/dev/null || true
fi

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

echo "✅ Backup completed: $BACKUP_DIR"
ls -lh "$BACKUP_DIR" | tail -5
