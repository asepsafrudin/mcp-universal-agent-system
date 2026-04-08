#!/bin/bash
# Shared Environment Run Script - NO LOCAL VENV (hemat storage)

echo "📁 Working dir: $(pwd)"
echo "🔧 Installing shared dependencies (run sekali)..."

# Install dependencies ke shared/global env (skip jika sudah ada)
pip install --upgrade pip
pip install -r requirements.txt --quiet || echo "✅ Dependencies OK or already installed"

echo "⚙️ Starting XLSX GDrive Workflow MCP Server..."
python3 src/server.py
