#!/usr/bin/env python3
"""
Sync Dokumen Disposisi ULA Lokal → Google Drive
================================================
Upload DOCX disposisi ULA ke Google Drive folder.

Jalankan:
  python3 scripts/sync_ula_disposisi_to_gdrive.py
  python3 scripts/sync_ula_disposisi_to_gdrive.py --dry-run
  python3 scripts/sync_ula_disposisi_to_gdrive.py --force
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = "/home/aseps/MCP/mcp-unified"
sys.path.insert(0, PROJECT_ROOT)
from core.secrets import load_runtime_secrets
load_runtime_secrets()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sync_ula_disposisi")

# Configuration
LOCAL_DOCS_DIR = "/home/aseps/MCP/data/storage/disposisi_docs_ula"

# Google Drive folder for ULA disposisi (same as mailmerge)
FOLDER_ID = "1v5OjzdXBc9xX95FcRBopT6seze_p0H8Q"
GDRIVE_FOLDER_ID = os.getenv("ULA_GDRIVE_FOLDER_ID", FOLDER_ID)

# OAuth2 credentials path
CREDENTIALS_DIR = "/home/aseps/MCP/config/credentials/google/puubangda"
CLIENT_SECRET_FILE = os.path.join(CREDENTIALS_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "token.json")


def get_drive_service():
    """Get Google Drive service using OAuth2 credentials."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    with open(TOKEN_FILE) as f:
        tok = json.load(f)
    with open(CLIENT_SECRET_FILE) as f:
        cs = json.load(f)
    web = cs.get("web") or cs.get("installed", {})

    creds = Credentials(
        token=tok.get("token"),
        refresh_token=tok.get("refresh_token"),
        token_uri=tok.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=web.get("client_id", tok.get("client_id")),
        client_secret=web.get("client_secret", tok.get("client_secret")),
        scopes=tok.get("scopes", []),
    )
    if creds.expired and creds.refresh_token:
        log.info("Refreshing OAuth2 token...")
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            json.dump({**tok, "token": creds.token}, f, indent=2)

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload_file(drive_svc, local_path: str, folder_id: str, file_name: str, force: bool = False) -> dict:
    """Upload DOCX to Google Drive."""
    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(local_path, mimetyp="application/vnd.openxmlformats-officedocument.wordprocessingml.document", resumable=False)
    file_meta = {"name": file_name, "parents": [folder_id]}
    
    f = drive_svc.files().create(body=file_meta, media_body=media, fields="id,webViewLink").execute()
    return {"id": f["id"], "url": f["webViewLink"], "skipped": False}


def sync_files(dry_run: bool = False, force: bool = False) -> None:
    """Sync all DOCX files from local directory to Google Drive."""
    if not os.path.exists(LOCAL_DOCS_DIR):
        log.error("Directory not found: %s", LOCAL_DOCS_DIR)
        return

    docx_files = list(Path(LOCAL_DOCS_DIR).glob("*.docx"))
    if not docx_files:
        log.info("No DOCX files found in %s", LOCAL_DOCS_DIR)
        return

    log.info("Found %d DOCX files to sync", len(docx_files))

    if dry_run:
        for f in docx_files[:10]:
            log.info("  [DRY-RUN] %s (%d bytes)", f.name, f.stat().st_size)
        if len(docx_files) > 10:
            log.info("  ... and %d more", len(docx_files) - 10)
        return

    drive_svc = get_drive_service()
    synced = skipped = failed = 0

    for f in docx_files:
        try:
            result = upload_file(drive_svc, str(f), GDRIVE_FOLDER_ID, f.name, force=force)
            if result.get("skipped"):
                skipped += 1
            else:
                synced += 1
                log.info("Synced: %s", f.name)
        except Exception as e:
            log.error("Failed: %s - %s", f.name, e)
            failed += 1

    result = {
        "ok": True,
        "synced": synced,
        "skipped": skipped,
        "failed": failed,
        "total": len(docx_files),
        "finished_at": datetime.now().isoformat()
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    sync_files(dry_run=args.dry_run, force=args.force)