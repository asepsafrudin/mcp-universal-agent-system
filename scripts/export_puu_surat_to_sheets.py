#!/usr/bin/env python3
"""
Export: Surat PUU ke Google Spreadsheet
=========================================
Export data dari tabel `surat_untuk_substansi_puu` ke Google Spreadsheet
dan simpan di folder yang sama dengan mailmerge (1v5OjzdXBc9xX95FcRBopT6seze_p0H8Q).

Jalankan:
  python3 scripts/export_puu_surat_to_sheets.py
"""
import os
import sys
import json
import logging
from datetime import datetime, date

PROJECT_ROOT = "/home/aseps/MCP/mcp-unified"
sys.path.insert(0, PROJECT_ROOT)
from core.secrets import load_runtime_secrets
load_runtime_secrets()

import psycopg

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("export_puu_sheets")

FOLDER_ID = "1v5OjzdXBc9xX95FcRBopT6seze_p0H8Q"
SPREADSHEET_NAME = "Export Surat PUU 2026"

def get_services():
    """Get Sheets & Drive services."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request

    token_path = "/home/aseps/MCP/config/credentials/google/puubangda/token.json"
    secret_path = "/home/aseps/MCP/config/credentials/google/puubangda/client_secret.json"

    with open(token_path) as f:
        tok = json.load(f)
    with open(secret_path) as f:
        cs = json.load(f)
    web = cs.get("web") or cs.get("installed", {})

    creds = Credentials(
        token=tok.get("token"), refresh_token=tok.get("refresh_token"),
        token_uri=tok.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=web.get("client_id", tok.get("client_id")),
        client_secret=web.get("client_secret", tok.get("client_secret")),
        scopes=tok.get("scopes", []))
    if creds.expired and creds.refresh_token:
        log.info("Refreshing token...")
        creds.refresh(Request())
        with open(token_path, "w") as f:
            json.dump({**tok, "token": creds.token}, f, indent=2)

    return build("sheets", "v4", credentials=creds), build("drive", "v3", credentials=creds)

def get_puu_data():
    """Get data dari tabel surat_untuk_substansi_puu JOIN surat_dari_luar_bangda.
    
    Note: agenda_puu is generated dynamically (001-L, 002-L, ...)
    """
    dsn = os.getenv("DATABASE_URL")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY sp.id) as no,
                    sp.agenda,
                    sp.no_agenda_ses,
                    sp.surat_dari,
                    sp.nomor_surat,
                    sdlb.perihal,
                    sdlb.tgl_surat::text,
                    sp.disposisi_kepada,
                    sp.isi_disposisi,
                    sp.tanggal_disposisi::text,
                    sp.status
                FROM surat_untuk_substansi_puu sp
                JOIN surat_dari_luar_bangda sdlb ON sdlb.id = sp.surat_id
                ORDER BY sp.id
            """)
            cols = [d.name for d in cur.description]
            return cols, cur.fetchall()

def fmt_date(d):
    """Format tanggal."""
    if d is None:
        return ""
    if isinstance(d, str) and d:
        try:
            dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y")
        except:
            return d
    return str(d)

def export_to_sheets(sheets_svc, drive_svc, cols, rows):
    """Create spreadsheet and populate with data."""
    # Create spreadsheet
    spreadsheet = {
        "properties": {
            "title": SPREADSHEET_NAME,
        }
    }
    created = sheets_svc.spreadsheets().create(body=spreadsheet, fields="spreadsheetId,spreadsheetUrl").execute()
    ss_id = created["spreadsheetId"]
    ss_url = created["spreadsheetUrl"]
    log.info(f"Created spreadsheet: {ss_url}")
    
    # Move to target folder using addParents
    drive_svc.files().update(
        fileId=ss_id,
        addParents=FOLDER_ID,
        fields="id,parents"
    ).execute()
    log.info(f"Moved to folder: {FOLDER_ID}")
    
    # Prepare data with custom column order and agenda_puu
    col_map = {
        "no": "NO",
        "agenda": "AGENDA",
        "agenda_puu": "AGENDA PUU",
        "surat_dari": "SURAT DARI",
        "nomor_surat": "NOMOR SURAT",
        "perihal": "PERIHAL",
        "tgl_surat": "TGL SURAT",
        "no_agenda_ses": "NO AGENDA SES",
        "disposisi_kepada": "DISPOSISI KEPADA",
        "isi_disposisi": "ISI DISPOSISI",
        "tanggal_disposisi": "TGL DISPOSISI",
        "status": "STATUS"
    }
    headers = list(col_map.values())
    values = [headers]
    
    for i, row in enumerate(rows, 1):
        # Build row with agenda_puu included
        row_dict = {cols[j]: row[j] for j in range(len(cols))}
        formatted = [
            str(row_dict.get("no", i)),
            row_dict.get("agenda", ""),
            f"{i:03d}-L",  # agenda_puu auto-generated
            row_dict.get("surat_dari", ""),
            row_dict.get("nomor_surat", ""),
            row_dict.get("perihal", ""),
            fmt_date(row_dict.get("tgl_surat", "")),
            row_dict.get("no_agenda_ses", ""),
            row_dict.get("disposisi_kepada", ""),
            row_dict.get("isi_disposisi", ""),
            fmt_date(row_dict.get("tanggal_disposisi", "")),
            row_dict.get("status", "pending")
        ]
        values.append(formatted)
    body = {"values": values}
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=ss_id,
        range="A1",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    
    # Format header row (bold)
    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True},
                        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8}
                    }
                },
                "fields": "userEnteredFormat"
            }
        },
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": len(headers)
                }
            }
        }
    ]
    sheets_svc.spreadsheets().batchUpdate(spreadsheetId=ss_id, body={"requests": requests}).execute()
    
    return ss_url, len(rows)

def run():
    """Main export function."""
    cols, rows = get_puu_data()
    log.info(f"Found {len(rows)} rows to export with {len(cols)} columns")
    
    sheets_svc, drive_svc = get_services()
    ss_url, count = export_to_sheets(sheets_svc, drive_svc, cols, rows)
    
    result = {
        "ok": True,
        "exported_rows": count,
        "spreadsheet_url": ss_url,
        "spreadsheet_name": SPREADSHEET_NAME,
        "folder_id": FOLDER_ID,
        "finished_at": datetime.now().isoformat()
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run()