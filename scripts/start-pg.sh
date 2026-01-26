#!/bin/bash
# Start PostgreSQL 16 + pgvector
if ! docker ps -a | grep -q mcp-pg; then
  docker run -d \
    --name mcp-pg \
    -e POSTGRES_DB=mcp \
    -e POSTGRES_USER=aseps \
    -e POSTGRES_PASSWORD=secure123 \
    -v /home/aseps/MCP/mcp-data/pg:/var/lib/postgresql/data \
    -p 5432:5432 \
    pgvector/pgvector:pg16
else
  docker start mcp-pg 2>/dev/null
fi
