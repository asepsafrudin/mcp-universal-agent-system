#!/bin/bash
#
# MCP-UNIFIED Health Check Script
# Script ini WAJIB dijalankan di awal setiap tugas untuk memastikan
# MCP-UNIFIED dan service yang dibutuhkan berjalan dengan baik.
#
# Penggunaan: ./mcp_health_check.sh
# Exit code: 0 = semua OK, 1 = ada masalah
#

set -e

echo "=========================================="
echo "MCP-UNIFIED Health Check"
echo "=========================================="
echo ""

ERRORS=0

# 1. Cek PostgreSQL
echo "[1/5] Memeriksa PostgreSQL..."
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "  ✅ PostgreSQL (port 5432) - accepting connections"
else
    echo "  ❌ PostgreSQL (port 5432) - TIDAK DAPAT DIHUBUNGI"
    ERRORS=$((ERRORS + 1))
fi

if pg_isready -h localhost -p 5433 > /dev/null 2>&1; then
    echo "  ✅ PostgreSQL (port 5433) - accepting connections"
else
    echo "  ❌ PostgreSQL (port 5433) - TIDAK DAPAT DIHUBUNGI"
    ERRORS=$((ERRORS + 1))
fi

# 2. Cek Redis
echo ""
echo "[2/5] Memeriksa Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Redis - responding"
else
    echo "  ⚠️  Redis - TIDAK DAPAT DIHUBUNGI (opsional)"
fi

# 3. Cek MCP Server SSE
echo ""
echo "[3/5] Memeriksa MCP Server SSE..."
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "  ✅ MCP Server SSE - running"
    echo "  📊 Status: $HEALTH"
else
    echo "  ❌ MCP Server SSE - TIDAK BERJALAN"
    echo "  💡 Jalankan: cd /home/aseps/MCP/mcp-unified && nohup python3 mcp_server_sse.py > /tmp/mcp_server.log 2>&1 &"
    ERRORS=$((ERRORS + 1))
fi

# 4. Cek Database Connection
echo ""
echo "[4/5] Memeriksa koneksi database..."
PGPASSWORD=secure123 psql -h localhost -p 5432 -U aseps -d mcp -c "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Database 'mcp' - connected"
else
    echo "  ❌ Database 'mcp' - GAGAL TERHUBUNG"
    ERRORS=$((ERRORS + 1))
fi

PGPASSWORD=mcp_password_2024 psql -h localhost -p 5433 -U mcp_user -d mcp_knowledge -c "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Database 'mcp_knowledge' - connected"
else
    echo "  ❌ Database 'mcp_knowledge' - GAGAL TERHUBUNG"
    ERRORS=$((ERRORS + 1))
fi

# 5. Cek MCP Tools
echo ""
echo "[5/5] Memeriksa MCP Tools..."
TOOLS_COUNT=$(echo "$HEALTH" | grep -o '"tools_available":[0-9]*' | cut -d: -f2)
if [ ! -z "$TOOLS_COUNT" ]; then
    echo "  ✅ Tools tersedia: $TOOLS_COUNT"
else
    echo "  ⚠️  Tidak dapat membaca jumlah tools"
fi

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ SEMUA CHECK LULUS - Sistem siap digunakan"
    exit 0
else
    echo "❌ DITEMUKAN $ERRORS MASALAH - Periksa log di atas"
    exit 1
fi