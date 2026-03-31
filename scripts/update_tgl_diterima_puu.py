#!/usr/bin/env python3
"""
Update Tanggal Diterima PUU dari Google Spreadsheet
=====================================================
Membaca kolom "Tgl Diterima PUU" dari spreadsheet dan update database.

Sheet ID: 1GRLdIr0ONXKTGWxPqyJW9vgcwgaYkU8YdN6eAoVPAeQ
Tab: Dispo PUU

Jalankan:
  python3 scripts/update_tgl_diterima_puu.py
  python3 scripts/update_tgl_diterima_puu.py --dry-run
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
log = logging.getLogger("update_tgl_puu")

SPREADSHEET_ID = "1GRLdIr0ONXKTGWxPqyJW9vgcwgaYkU8YdN6eAoVPAeQ"
SHEET_NAME = "Dispo PUU"

# Column mapping based on expected sheet structure
# Column A: Row number / No
# Column B: AGENDA (e.g., 0018/L)
# Column ?: Tgl Diterima PUU (will be detected by header)

def get_services():
    """Get Sheets and Drive services."""
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
        token_uri=tok.get("token_uri"),
        client_id=web.get("client_id"),
        client_secret=web.get("client_secret"),
        scopes=tok.get("scopes", []))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w") as f:
            json.dump({**tok, "token": creds.token}, f, indent=2)

    return build("sheets", "v4", credentials=creds), build("drive", "v3", credentials=creds)

def get_sheets_data():
    """Get data from Dispo PUU sheet."""
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
        token_uri=tok.get("token_uri"),
        client_id=web.get("client_id"),
        client_secret=web.get("client_secret"),
        scopes=tok.get("scopes", []))
    if creds.expired and creds.refresh_token:
        log.info("Refreshing token...")
        creds.refresh(Request())
        with open(token_path, "w") as f:
            json.dump({**tok, "token": creds.token}, f, indent=2)

    svc = get_services()[0]
    result = svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{SHEET_NAME}'!A1:Z500"
    ).execute()
    return result.get("values", [])

BULAN = {"jan":1,"feb":2,"mar":3,"apr":4,"mei":5,"jun":6,"jul":7,"agu":8,"sep":9,"okt":10,"nov":11,"des":12}

def parse_date(val):
    """Parse date from spreadsheet - handle DD/MM/YYYY and DD-Mon-YYYY formats."""
    if not val or val == "":
        return None
    s = str(val).strip()
    # Handle DD/MM/YYYY format
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            try:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                return date(year + 2000 if year < 100 else year, month, day)
            except:
                pass
    
    # Handle DD-MMon-YYYY or DD Mon YYYY format (e.g., "8-Jan-2026" or "8 Jan 2026")
    for sep in ["-", " "]:
        if sep in s:
            parts = s.split(sep)
            if len(parts) >= 3:
                try:
                    day = int(parts[0])
                    month_str = parts[1].lower()[:3]
                    month = BULAN.get(month_str, 1)
                    year = int(parts[2])
                    return date(year, month, day)
                except:
                    pass
    return None

def run(dry_run=False):
    """Main update function."""
    # Get sheet data
    log.info(f"Fetching data from sheet '{SHEET_NAME}'...")
    values = get_sheets_data()
    
    if len(values) < 2:
        log.warning("No data found in sheet")
        return

    # Parse header to find column indices
    headers = [h.strip().upper() for h in values[0]]
    log.info(f"Headers: {headers}")
    
    # Find column indices - Match by NOMOR SURAT
    nomor_surat_col = None
    tgl_diterima_col = None
    new_tgl_col = None  # New column to write tanggal_diterima
    
    for i, h in enumerate(headers):
        if "NOMOR SURAT" in h:
            nomor_surat_col = i
        if "TGL DITERIMA PUU" in h:
            tgl_diterima_col = i
    
    if nomor_surat_col is None:
        log.error("Cannot find NOMOR SURAT column")
        return
    if tgl_diterima_col is None:
        log.error(f"Cannot find TGL DITERIMA PUU column. Headers: {headers}")
        return
    
    # Use the column after TGL_DITERIMA_PUU for writing
    new_tgl_col = tgl_diterima_col + 1
    
    log.info(f"NOMOR SURAT column index: {nomor_surat_col}")
    log.info(f"TGL DITERIMA PUU column index: {tgl_diterima_col}")
    log.info(f"New column index for writing: {new_tgl_col}")
    
    # Build update list - Match by NOMOR SURAT
    updates = []
    for i, row in enumerate(values[1:], 1):
        if len(row) <= max(nomor_surat_col, tgl_diterima_col):
            continue
        
        nomor_surat = row[nomor_surat_col].strip() if len(row) > nomor_surat_col else ""
        tgl_str = row[tgl_diterima_col].strip() if len(row) > tgl_diterima_col else ""
        
        if not nomor_surat or not tgl_str:
            continue
        
        tgl = parse_date(tgl_str)
        if tgl:
            updates.append({
                "row": i + 1,
                "nomor_surat": nomor_surat,
                "tgl_diterima": tgl.isoformat()
            })
    
    if not updates:
        log.info("No updates needed")
        return
    
    log.info(f"Found {len(updates)} dates to update")
    
    dsn = os.getenv("DATABASE_URL")
    write_values = []  # For writing back to sheet
    
    with psycopg.connect(dsn) as conn:
        for u in updates:
            if dry_run:
                log.info(f"[DRY RUN] Would update nomor_surat={u['nomor_surat']}, tgl={u['tgl_diterima']}")
                continue
            
            cur = conn.cursor()
            # Update via nomor_surat from surat_dari_luar_bangda
            cur.execute("""
                UPDATE surat_untuk_substansi_puu sp
                SET tanggal_diterima = %s::date
                FROM surat_dari_luar_bangda sdlb
                WHERE sp.surat_id = sdlb.id
                  AND sdlb.nomor_surat = %s
                  AND (sp.tanggal_diterima IS NULL OR sp.tanggal_diterima != %s::date)
                RETURNING sp.id
            """, (u["tgl_diterima"], u["nomor_surat"], u["tgl_diterima"]))
            
            if cur.fetchone():
                log.info(f"Updated: nomor_surat={u['nomor_surat']}, tgl={u['tgl_diterima']}")
            else:
                log.info(f"Skipped (no match or same value): nomor_surat={u['nomor_surat']}")
            conn.commit()
            
            # Prepare for writing back
            write_values.append({
                "range": f"R{u['row']}C{new_tgl_col + 1}",  # 1-based
                "value": u["tgl_diterima"]
            })
    
    # Write back dates to new column in spreadsheet
    if write_values and not dry_run:
        log.info(f"Writing {len(write_values)} dates back to spreadsheet...")
        sheets_svc, _ = get_services()
        
        # Calculate column letter (handles columns beyond Z)
        col_letter = ""
        col = new_tgl_col
        while col >= 0:
            col_letter = chr(65 + (col % 26)) + col_letter
            col = (col // 26) - 1
        
        for wv in write_values:
            sheets_svc.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{SHEET_NAME}'!{col_letter}{wv['row']}",
                valueInputOption="USER_ENTERED",
                body={"values": [[wv["value"]]]}
            ).execute()
        
        log.info("Dates written to spreadsheet")
    
    log.info("Done")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)