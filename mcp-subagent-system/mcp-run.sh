#!/bin/bash
# Script untuk menjalankan MCP Sub-Agent System

export PYTHONPATH=$PYTHONPATH:$(pwd):$(dirname $(pwd))
/home/aseps/MCP/mcp-subagent-system/.venv/bin/python3 server.py "$@"
