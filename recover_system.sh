#!/bin/bash
echo "🚨 MCP System Recovery Started..."

# 1. Stop all services
pkill -f "mcp-unified"
fuser -k 8000/tcp 2>/dev/null
docker stop mcp-pg 2>/dev/null

# 2. Restore from latest backup
# We assume backups are in $HOME/MCP/backups
LATEST_DB=$(ls -t $HOME/MCP/backups/mcp_db_*.sql.gz 2>/dev/null | head -1)

if [ -f "$LATEST_DB" ]; then
    echo "Restoring DB from: $LATEST_DB"
    docker start mcp-pg
    
    # Wait for PG to be ready
    echo "Waiting for PostgreSQL to start..."
    sleep 5
    
    # Drop and create DB to be clean? Or just restore on top? 
    # pg_dump usually dumps data. Assuming clean restore might be better but risky without confirmation.
    # We follow the guide's simple restore logic.
    gunzip -c "$LATEST_DB" | docker exec -i mcp-pg psql -U aseps mcp
else
    echo "⚠️ No DB backup found in $HOME/MCP/backups/"
    # Still ensure DB is running
    docker start mcp-pg
fi

# 3. Restart services
cd $HOME/MCP/mcp-unified
bash run.sh &
PID=$!
echo "Server restarted with PID: $PID"

# 4. Verify
echo "Waiting for server to support requests..."
sleep 10
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$CODE" == "200" ]; then
    echo "✅ System recovered!"
else
    echo "❌ Recovery failed! Health check returned $CODE"
fi
