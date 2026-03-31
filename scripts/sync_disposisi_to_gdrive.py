#!/usr/bin/env python3
"""
Sync Dokumen Disposisi Lokal → Google Drive
============================================
Membaca file DOCX lokal yang sudah digenerate (sync_status='pending'),
upload ke Google Drive folder menggunakan SA credentials,
lalu update DB dengan doc_url dan sync_status='synced'.

Jalankan:
  python3 scripts/sync_disposisi_to_gdrive.py
  python3 scripts/sync_disposisi_to_gdrive.py --dry-run
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime

import psycopg

PROJECT_ROOT = "/home/aseps/MCP/mcp-unified"
sys.path.insert(0, PROJECT_ROOT)
from core.secrets import load_runtime_secrets
load_runtime_secrets()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sync_disposisi")

# Use OAuth2 credentials from puubangda folder with proper token support
CREDENTIALS_DIR = "/home/aseps/MCP/config/credentials/google/puubangda"
CLIENT_SECRET_FILE = os.path.join(CREDENTIALS_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]


def get_drive_service():
    """Buat Drive service menggunakan OAuth2 user credentials (puubangda)."""
    import json
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(
            f"Token file not found: {TOKEN_FILE}\n"
            "Run: python3 scripts/reauth_google_drive.py\n"
            "Then re-run this sync script."
        )

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
        scopes=tok.get("scopes", SCOPES),
    )
    if creds.expired and creds.refresh_token:
        log.info("Refreshing OAuth2 token...")
        creds.refresh(Request())
        # Save updated token
        new_tok = {**tok, "token": creds.token}
        new_tok.setdefault("client_id", web.get("client_id"))
        new_tok.setdefault("client_secret", web.get("client_secret"))
        with open(TOKEN_FILE, "w") as f:
            json.dump(new_tok, f, indent=2)

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload_docx(drive_svc, local_path: str, folder_id: str, display_name: str, force: bool = False) -> dict:
    """
    Upload DOCX ke Drive.
    Jika force=True, hapus file lama dan upload ulang (untuk update konten).
    """
    from googleapiclient.http import MediaFileUpload

    # Cek apakah sudah ada di folder
    safe_q = display_name.replace("'", "\\'")
    q = f"name='{safe_q}' and '{folder_id}' in parents and trashed=false"
    existing = drive_svc.files().list(q=q, fields="files(id,webViewLink)", pageSize=1).execute()
    if existing.get("files"):
        if not force:
            f = existing["files"][0]
            log.info("Skip (sudah ada): %s", display_name)
            return {"id": f["id"], "url": f["webViewLink"], "skipped": True}
        else:
            # Hapus file lama sebelum upload ulang
            old_id = existing["files"][0]["id"]
            drive_svc.files().delete(fileId=old_id).execute()
            log.info("Deleted old file: %s (id=%s)", display_name, old_id)

    media = MediaFileUpload(
        local_path,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        resumable=False
    )
    file_meta = {
        "name": display_name,
        "parents": [folder_id],
        # Konversi ke Google Docs saat upload (tidak pakai quota file karena sudah owned folder owner)
        # Komentari baris di bawah jika tidak ingin konversi
        # "mimeType": "application/vnd.google-apps.document"
    }
    f = drive_svc.files().create(
        body=file_meta,
        media_body=media,
        fields="id,webViewLink",
        # supportsAllDrives=True  # aktifkan jika folder adalah Shared Drive
    ).execute()

    doc_id = f["id"]
    doc_url = f["webViewLink"]
    # OAuth2 user credentials: file langsung milik user yang login, tidak perlu transfer ownership
    return {"id": doc_id, "url": doc_url, "skipped": False}


def run_sync(dry_run: bool = False, force: bool = False) -> None:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL belum diset")

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, lembar_disposisi_id, agenda_puu, file_name,
                       local_file_path, folder_id
                FROM disposisi_documents
                WHERE generation_status = 'local_ready'
                  AND sync_status IN ('pending', 'error')
                  AND local_file_path IS NOT NULL
                ORDER BY id
            """)
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]

        if not rows:
            log.info("Tidak ada dokumen yang perlu disync ke Drive.")
            print(json.dumps({"ok": True, "synced": 0, "message": "Semua sudah tersync"}))
            return

        log.info("%d dokumen akan disync ke Drive", len(rows))

        if dry_run:
            for r in rows:
                row = dict(zip(cols, r))
                log.info("  [DRY-RUN] %s → %s", row["agenda_puu"], row["local_file_path"])
            return

        drive_svc = get_drive_service()
        synced = skipped = failed = 0

        for r in rows:
            row = dict(zip(cols, r))
            doc_db_id    = row["id"]
            agenda_puu   = row["agenda_puu"]
            local_path   = row["local_file_path"]
            folder_id    = row["folder_id"]
            # Nama tampilan di Drive (tanpa .docx agar lebih bersih)
            display_name = row["file_name"].replace(".docx", "") if row["file_name"] else f"Disposisi - {agenda_puu}"

            if not os.path.exists(local_path):
                log.warning("File lokal tidak ditemukan: %s", local_path)
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE disposisi_documents SET sync_status='error', error_message=%s WHERE id=%s",
                        ("File lokal tidak ditemukan", doc_db_id)
                    )
                conn.commit()
                failed += 1
                continue

            try:
                result = upload_docx(drive_svc, local_path, folder_id, display_name, force=force)
                doc_url = result["url"]

                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE disposisi_documents
                        SET doc_id     = %s,
                            doc_url    = %s,
                            sync_status = 'synced',
                            synced_at   = NOW()
                        WHERE id = %s
                    """, (result["id"], doc_url, doc_db_id))
                conn.commit()

                if result.get("skipped"):
                    log.info("Skip: %s", display_name)
                    skipped += 1
                else:
                    log.info("Synced: %s → %s", display_name, doc_url)
                    synced += 1

            except Exception as e:
                log.error("GAGAL sync %s: %s", agenda_puu, e)
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE disposisi_documents
                        SET sync_status='error', error_message=%s
                        WHERE id=%s
                    """, (str(e)[:500], doc_db_id))
                conn.commit()
                failed += 1

    print(json.dumps({
        "ok": True,
        "synced": synced,
        "skipped": skipped,
        "failed": failed,
        "finished_at": datetime.utcnow().isoformat()
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync dokumen disposisi lokal ke Google Drive")
    parser.add_argument("--dry-run", action="store_true", help="Preview tanpa upload")
    parser.add_argument("--force", action="store_true", help="Hapus & re-upload file yang sudah ada di Drive")
    args = parser.parse_args()
    run_sync(dry_run=args.dry_run, force=args.force)
