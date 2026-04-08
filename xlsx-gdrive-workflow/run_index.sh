#!/bin/bash
# Arsip Indexing Runner
cd /home/aseps/MCP/xlsx-gdrive-workflow

echo "🚀 Starting Arsip PUU Indexing..."
echo "Files in arsip-2025/scan: $(find arsip-2025/scan -name '*.png' | wc -l)"

python3 index_arsip.py

echo "✅ Done! Check:"
echo "  - arsip-extracted/*.json (backup)"
echo "  - memory_search(query='SPTJB', namespace='arsip-puu-2025')"
echo "  - knowledge_search('Dangda')"

