#!/bin/bash

# --- Antigravity MCP Global Initializer ---
# Author: Senior Engineer | MCP Unified
# Deskripsi: Menghubungkan folder proyek lokal ke Pusat MCP.

# 1. Tentukan Lokasi Pusat (Ganti 'aseps' sesuai username Anda)
export MCP_CENTRAL="/home/aseps/MCP"
export CURRENT_PROJECT=$(pwd)

echo "🛠️  Initializing MCP Session at: $CURRENT_PROJECT"

# 2. Logika Auto-Symlink
if [ "$CURRENT_PROJECT" != "$MCP_CENTRAL" ]; then
    echo "🔗 Project Satelit terdeteksi. Menautkan ke Pusat MCP..."
    
    # Buat symlink .agent jika belum ada
    if [ ! -L ".agent" ] && [ ! -f ".agent" ]; then
        ln -s "$MCP_CENTRAL/.agent" ".agent"
        echo "✅ Symlink .agent berhasil dibuat."
    else
        echo "ℹ️  File .agent sudah ada (skipping symlink)."
    fi
else
    echo "🏠 Menjalankan langsung dari Pusat MCP."
fi

# 3. Setup Environment Global
export PYTHONPATH=$PYTHONPATH:"$MCP_CENTRAL":"$MCP_CENTRAL/mcp_unified"

# 4. Jalankan Audit Kepatuhan (Mengacu ke skrip pusat)
echo "🔍 Running Senior Engineer Compliance Audit..."
python3 "$MCP_CENTRAL/test_agent_compliance.py"

# 5. Eksekusi Server
if [ $? -eq 0 ]; then
    echo "🚀 Audit passed. Launching MCP Unified..."
    exec "$MCP_CENTRAL/mcp_unified/start.sh"
else
    echo "❌ Audit failed. Periksa konfigurasi di $MCP_CENTRAL"
    exit 1
fi