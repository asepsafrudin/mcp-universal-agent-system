#!/usr/bin/env python3
"""
Audit helper untuk migrasi ke single centralized secret file.

Script ini tidak mencetak nilai secret. Output hanya:
- file mana yang mengandung key
- key mana yang duplikat antar file
- key mana yang sebaiknya dipertahankan di source of truth

Usage:
  python3 scripts/centralize_secrets_audit.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path("/home/aseps/MCP")
FILES = [
    ROOT / ".env",
    ROOT / "mcp-unified" / ".env",
    ROOT / "mcp-unified" / "integrations" / "telegram" / ".env",
]

KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def read_keys(path: Path) -> list[str]:
    if not path.exists():
        return []

    keys: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if KEY_RE.match(line):
            keys.append(line.split("=", 1)[0])
    return sorted(set(keys))


def main() -> int:
    by_file = {str(path): read_keys(path) for path in FILES}
    resolved_map = {str(path): str(path.resolve()) for path in FILES if path.exists()}

    canonical_groups: dict[str, list[str]] = {}
    for original, resolved in resolved_map.items():
        canonical_groups.setdefault(resolved, []).append(original)

    locations: dict[str, list[str]] = {}
    for path, keys in by_file.items():
        canonical_path = resolved_map.get(path, path)
        for key in keys:
            current = locations.setdefault(key, [])
            if canonical_path not in current:
                current.append(canonical_path)

    duplicates = {
        key: paths
        for key, paths in sorted(locations.items())
        if len(paths) > 1
    }

    payload = {
        "source_of_truth_recommended": str(ROOT / ".env"),
        "files_scanned": [str(path) for path in FILES],
        "symlink_aliases": canonical_groups,
        "keys_by_file": by_file,
        "duplicate_keys": duplicates,
        "next_actions": [
            "Pilih satu source of truth: root .env atau file yang ditunjuk MCP_SECRETS_FILE",
            "Gunakan symlink alias hanya untuk kompatibilitas, bukan sebagai tempat edit utama",
            "Jalankan python3 scripts/runtime_secret_check.py untuk verifikasi",
        ],
    }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
