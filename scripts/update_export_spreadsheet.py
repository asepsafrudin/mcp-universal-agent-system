#!/usr/bin/env python3
"""
Update Export Spreadsheet with latest data including TGL DITERIMA PUU
========================================================================
Export data from surat_untuk_substansi_puu to Google Spreadsheet.

Spreadsheet ID: 1G6h7IrvDbJ0Ikvtn1YXvpAHly5jb4cZCklNHhaGpyug
"""
import os, sys, json
sys.path.insert(0, 'mcp-unified')
from core.secrets import load_runtime_secrets
load_runtime_secrets()

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import psycopg

SPREADSHEET_ID = "1G6h7IrvDbJ0Ikvtn1YXvpAHly5jb4cZCklNHhaGpyug"
TOKEN_PATH = "/home/aseps/MCP/config/credentials/google/puubangda/token.json"
SECRET_PATH = "/home/aseps/MCP/config/credentials/google/puubangda/client_secret.json"

def get_auth():
    with open(TOKEN_PATH) as f:
        tok = json.load(f)
    with open(SECRET_PATH) as f:
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
    return build("sheets", "v4", credentials=creds)

def run():
    sheets_svc = get_auth()
    dsn = os.getenv("DATABASE_URL")
    
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY sp.id) as no,
                    sp.agenda,
                    LPAD(ROW_NUMBER() OVER (ORDER BY sp.id)::text, 3, '0') || '-L' as agenda_puu,
                    COALESCE(sp.no_agenda_ses, ''),
                    sp.surat_dari,
                    sp.nomor_surat,
                    COALESCE(sdlb.perihal, ''),
                    COALESCE(TO_CHAR(sdlb.tgl_surat, 'DD/MM/YYYY'), ''),
                    COALESCE(sp.disposisi_kepada, ''),
                    COALESCE(sp.isi_disposisi, ''),
                    COALESCE(TO_CHAR(sp.tanggal_disposisi, 'DD/MM/YYYY'), ''),
                    COALESCE(TO_CHAR(sp.tanggal_diterima, 'DD/MM/YYYY'), 'Belum diterima'),
                    COALESCE(sp.status, 'pending')
                FROM surat_untuk_substansi_puu sp
                JOIN surat_dari_luar_bangda sdlb ON sdlb.id = sp.surat_id
                ORDER BY sp.id
            """)
            rows = cur.fetchall()
    
    headers = ["NO", "AGENDA ULA", "AGENDA PUU", "NO AGENDA SES", "SURAT DARI", 
               "NOMOR SURAT", "PERIHAL", "TGL SURAT", "DISPOSISI KEPADA", 
               "ISI DISPOSISI", "TGL DISPOSISI", "TGL DITERIMA PUU", "STATUS"]
    values = [headers]
    for r in rows:
        values.append([str(x) for x in r])
    
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="A1",
        valueInputOption="USER_ENTERED",
        body={"values": values}
    ).execute()
    
    print(f"Spreadsheet updated: {len(rows)} rows")
    print(f"URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")

if __name__ == "__main__":
    run()