#!/usr/bin/env python3
"""
Non-sensitive runtime secret verification for MCP workspace services.

Usage:
  python3 scripts/runtime_secret_check.py
  python3 scripts/runtime_secret_check.py telegram vane
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MCP_UNIFIED_ROOT = Path(__file__).resolve().parents[1] / "mcp-unified"
sys.path.insert(0, str(MCP_UNIFIED_ROOT))

from core.secrets import load_runtime_secrets, runtime_secret_status  # noqa: E402


SECRET_GROUPS = {
    "codex_mcp": [
        "MCP_SECRETS_FILE",
        "OPENAI_API_KEY",
        "MCP_CONFIG_PATH",
    ],
    "antigravity": [
        "POSTGRES_PASSWORD",
        "RABBITMQ_URL",
        "MCP_CONFIG_PATH",
    ],
    "mcp_unified": [
        "POSTGRES_PASSWORD",
        "REDIS_URL",
        "RABBITMQ_URL",
        "JWT_SECRET",
        "MCP_DEV_KEY",
    ],
    "telegram": [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "TELEGRAM_WEBHOOK_SECRET",
        "GROQ_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
    ],
    "vane": [
        "SEARXNG_API_URL",
        "GROQ_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
    ],
    "serena": [
        "SERENA_HOME",
        "OPENAI_API_KEY",
        "GITHUB_TOKEN",
    ],
    "google_workspace": [
        "GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE",
        "GOOGLE_WORKSPACE_OAUTH_CLIENT_FILE",
        "GOOGLE_WORKSPACE_TOKEN_FILE",
    ],
}


def main(argv: list[str]) -> int:
    load_runtime_secrets()

    selected = argv or list(SECRET_GROUPS.keys())
    unknown = [name for name in selected if name not in SECRET_GROUPS]
    if unknown:
        print(json.dumps({"error": f"unknown groups: {', '.join(unknown)}"}, indent=2))
        return 2

    payload = {
        group: runtime_secret_status(SECRET_GROUPS[group])
        for group in selected
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
