#!/usr/bin/env python3
"""
ETL Surat Luar 2026 (ULA - Unit Layanan Administrasi)
======================================================
Mengambil data dari spreadsheet eksternal "data surat luar 2026"
dan menyimpan ke PostgreSQL dalam tabel-tabel baru.

Spreadsheet ID: 1N6K0mXrGU1aWaUAOB0O97n7LdpooKBI27hu3KqqOAYA

Tabs:
  1. "Surat Masuk" (507 rows) → surat_dari_luar_bangda
  2. "Lembar Disposisi Dirjen" (507 rows) → lembar_disposisi_bangda  
  3. "Dispo DJ/TU Pim" (1333 rows) → disposisi_distributions
  4. "Dispo Ses" (1203 rows) → disposisi_distributions (source_tab='Dispo Ses')
  5. "Log Activity mailmerge" (1000 rows) → logging saja

Credentials: config/credentials/google/puubangda/token.json

Jalankan:
  cd /home/aseps/MCP
  source mcp-unified/.env
  export GOOGLE_WORKSPACE_TOKEN_FILE=config/credentials/google/puubangda/token.json
  export GOOGLE_WORKSPACE_CREDENTIALS_PATH=config/credentials/google/puubangda
  python3 scripts/etl_surat_luar_2026.py
"""
import os
import re
import sys
import json
import hashlib
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

# ── Setup project path ──────────────────────────────────────────────────────
PROJECT_ROOT = "/home/aseps/MCP/mcp-unified"
sys.path.insert(0, PROJECT_ROOT)

from core.secrets import load_runtime_secrets
load_runtime_secrets()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("etl_surat_luar_2026")

# ── Configuration ────────────────────────────────────────────────────────────
SPREADSHEET_ID = "1N6K0mXrGU1aWaUAOB0O97n7LdpooKBI27hu3KqqOAYA"
SHEET_SURAT_MASUK = "Surat Masuk"
SHEET_LEMBAR_DISPOSISI = "Lembar Disposisi Dirjen"
SHEET_DISPO_DJ_TU = "Dispo DJ/TU Pim"
SHEET_DISPO_SES = "Dispo Ses"
SHEET_LOG_MAILMERGE = "Log Activity mailmerge"

import psycopg


# ── Bulan Indonesia → angka ─────────────────────────────────────────────────
BULAN_MAP = {
    "JANUARI": 1, "FEBRUARI": 2, "MARET": 3, "APRIL": 4,
    "MEI": 5, "JUNI": 6, "JULI": 7, "AGUSTUS": 8,
    "SEPTEMBER": 9, "OKTOBER": 10, "NOVEMBER": 11, "DESEMBER": 12,
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4,
    "MAY": 5, "JUN": 6, "JUL": 7, "AGU": 8,
    "SEP": 9, "OKT": 10, "NOV": 11, "DES": 12,
    "SEPT": 9, "NOP": 11,
}


def parse_date(val: Any) -> Optional[date]:
    """Parse tanggal multi-format termasuk bahasa Indonesia dan datetime dengan timestamp."""
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val

    s = str(val).strip()
    if not s or s.lower() == "null":
        return None

    # Strip time component jika ada, e.g. '02/01/2026 11.44.02' → '02/01/2026'
    if ' ' in s:
        s = s.split(' ')[0].strip()

    up = s.upper()
    for m_name, m_num in sorted(BULAN_MAP.items(), key=lambda x: -len(x[0])):
        if m_name in up:
            up = up.replace(m_name, str(m_num))
            break

    clean = re.sub(r"[^0-9]", "/", up)
    clean = re.sub(r"/+", "/", clean).strip("/")
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(clean, fmt)
            if dt.year < 100:
                dt = dt.replace(year=dt.year + 2000)
            return dt.date()
        except ValueError:
            continue
    return None


def parse_datetime(val: Any) -> Optional[datetime]:
    """Parse timestamp lengkap (DD/MM/YYYY HH:MM:SS)."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val

    s = str(val).strip()
    if not s or s.lower() == "null":
        return None

    # Try DD/MM/YYYY HH:MM:SS or DD/MM/YYYY HH.MM.SS
    s = s.replace(".", ":")
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%y %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    # Fallback: try date only
    d = parse_date(val)
    if d:
        return datetime.combine(d, datetime.min.time())
    return None


def make_unique_id(prefix: str, nomor_surat: str, surat_dari: str, row: int) -> str:
    """Buat ID stabil dari prefix + nomor_surat + pengirim + baris."""
    nomor = str(nomor_surat).strip().lower() if nomor_surat else "nonomor"
    dari = str(surat_dari).strip().lower() if surat_dari else "nodari"
    raw = f"{prefix}_{nomor}_{dari}_{row}"
    raw = re.sub(r'[\s\/\\]+', '_', raw)
    raw = re.sub(r'[^a-z0-9_]', '', raw)
    return raw[:200]  # Limit length


# ── Google Sheets client ────────────────────────────────────────────────────
_ula_client = None

def get_client():
    """Get Google Sheets client with ULA credentials - direct OAuth2 loading."""
    global _ula_client
    if _ula_client is not None:
        return _ula_client
    
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    
    token_path = "/home/aseps/MCP/config/credentials/google/puubangda/token.json"
    
    # Load token file directly
    with open(token_path, 'r') as f:
        token_data = json.load(f)
    
    # Create credentials from token data
    _ula_creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes", [])
    )
    
    # Refresh if expired
    if _ula_creds.expired and _ula_creds.refresh_token:
        log.info("Token expired, refreshing...")
        _ula_creds.refresh(Request())
        # Save updated token
        with open(token_path, 'w') as f:
            json.dump({
                "token": _ula_creds.token,
                "refresh_token": _ula_creds.refresh_token,
                "token_uri": _ula_creds.token_uri,
                "client_id": _ula_creds.client_id,
                "client_secret": _ula_creds.client_secret,
                "scopes": _ula_creds.scopes
            }, f, indent=2)
        log.info("Token refreshed and saved")
    
    # Build Sheets API client
    _ula_client = build("sheets", "v4", credentials=_ula_creds, cache_discovery=False)
    return _ula_client


def fetch_sheet_data(sheet_name: str, range_str: str = "A1:Z5000") -> List[List[Any]]:
    """Fetch raw data dari Google Sheets tab tertentu."""
    svc = get_client()  # Direct sheets API client
    rng = f"'{sheet_name}'!{range_str}"
    result = svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=rng
    ).execute()
    return result.get("values", [])


def get_cell(row: List[Any], idx: int) -> str:
    """Get cell value dari row, return empty string jika out of bounds."""
    if idx < 0 or idx >= len(row):
        return ""
    v = row[idx]
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() == "null" else s


# ── Proses tab "Surat Masuk" ────────────────────────────────────────────────
# Tab Surat Masuk columns:
#   A: Timestamp (F)
#   B: Surat Dari (Pengirim)
#   C: Nomor Surat
#   D: Tgl Surat Masuk (DD/MM/YYYY)
#   E: Tgl Diterima ULA
#   F: Perihal
#   G: Arahan Menteri
#   H: Arahan Sekjen
#   I: Agenda ULA (format: NNN/L)
#   J: Status Mailmerge

def process_surat_masuk(conn) -> Dict[str, int]:
    """Process tab 'Surat Masuk' → surat_dari_luar_bangda."""
    stats = {"total": 0, "inserted": 0, "updated": 0, "skipped": 0}

    log.info("Fetching tab '%s'...", SHEET_SURAT_MASUK)
    try:
        values = fetch_sheet_data(SHEET_SURAT_MASUK, "A1:Z5000")
    except Exception as e:
        log.error("Gagal fetch tab '%s': %s", SHEET_SURAT_MASUK, e)
        return stats

    if len(values) <= 1:
        log.warning("Data kosong di tab '%s'", SHEET_SURAT_MASUK)
        return stats

    header = values[0]
    rows = values[1:]
    stats["total"] = len(rows)

    log.info("Header %s: %s", SHEET_SURAT_MASUK, header)
    log.info("Total rows to process: %d", len(rows))

    with conn.cursor() as cur:
        for row_num, row in enumerate(rows, start=2):
            # Column mapping (0-based index)
            # A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, I=8, J=9
            timestamp_raw = parse_datetime(get_cell(row, 0))      # A: Timestamp
            surat_dari = get_cell(row, 1)                          # B: Surat Dari
            nomor_surat = get_cell(row, 2)                         # C: Nomor Surat
            tgl_surat = parse_date(get_cell(row, 3))               # D: Tgl Surat Masuk
            tgl_diterima_ula = parse_date(get_cell(row, 4))        # E: Tgl Diterima ULA
            perihal = get_cell(row, 5)                             # F: Perihal
            arahan_menteri = get_cell(row, 6)                      # G: Arahan Menteri
            arahan_sekjen = get_cell(row, 7)                       # H: Arahan Sekjen
            agenda_ula = get_cell(row, 8)                          # I: Agenda ULA
            status_mailmerge = get_cell(row, 9)                    # J: Status Mailmerge

            # Skip rows yang tidak ada nomor surat dan pengirim
            if not nomor_surat and not surat_dari:
                stats["skipped"] += 1
                continue

            unique_id = make_unique_id("SKULA", nomor_surat, surat_dari, row_num)

            # UPSERT ke surat_dari_luar_bangda
            cur.execute(
                """
                INSERT INTO surat_dari_luar_bangda (
                    unique_id,
                    surat_dari,
                    nomor_surat,
                    tgl_surat,
                    tgl_diterima_ula,
                    perihal,
                    arahan_menteri,
                    arahan_sekjen,
                    agenda_ula,
                    status_mailmerge,
                    timestamp_raw,
                    source_sheet,
                    source_row
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (unique_id) DO UPDATE SET
                    surat_dari       = EXCLUDED.surat_dari,
                    nomor_surat      = EXCLUDED.nomor_surat,
                    tgl_surat        = EXCLUDED.tgl_surat,
                    tgl_diterima_ula = EXCLUDED.tgl_diterima_ula,
                    perihal          = EXCLUDED.perihal,
                    arahan_menteri   = EXCLUDED.arahan_menteri,
                    arahan_sekjen    = EXCLUDED.arahan_sekjen,
                    agenda_ula       = EXCLUDED.agenda_ula,
                    status_mailmerge = EXCLUDED.status_mailmerge,
                    timestamp_raw    = EXCLUDED.timestamp_raw,
                    source_row       = EXCLUDED.source_row,
                    updated_at       = NOW()
                RETURNING id, (xmax = 0) AS is_insert
                """,
                (
                    unique_id,
                    surat_dari,
                    nomor_surat,
                    tgl_surat.isoformat() if tgl_surat else None,
                    tgl_diterima_ula.isoformat() if tgl_diterima_ula else None,
                    perihal,
                    arahan_menteri,
                    arahan_sekjen,
                    agenda_ula,
                    status_mailmerge,
                    timestamp_raw.isoformat() if timestamp_raw else None,
                    SHEET_SURAT_MASUK,
                    row_num
                )
            )
            row_result = cur.fetchone()
            if row_result:
                _, is_insert = row_result[0], row_result[1]
                if is_insert:
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1

    log.info(
        "Tab '%s': total=%d inserted=%d updated=%d skipped=%d",
        SHEET_SURAT_MASUK, stats["total"], stats["inserted"],
        stats["updated"], stats["skipped"]
    )
    return stats


# ── Proses tab "Lembar Disposisi Dirjen" ────────────────────────────────────
def process_lembar_disposisi(conn) -> Dict[str, int]:
    """Process tab 'Lembar Disposisi Dirjen' → lembar_disposisi_bangda."""
    stats = {"total": 0, "inserted": 0, "updated": 0, "skipped": 0}

    log.info("Fetching tab '%s'...", SHEET_LEMBAR_DISPOSISI)
    try:
        values = fetch_sheet_data(SHEET_LEMBAR_DISPOSISI, "A1:Z5000")
    except Exception as e:
        log.error("Gagal fetch tab '%s': %s", SHEET_LEMBAR_DISPOSISI, e)
        return stats

    if len(values) <= 1:
        log.warning("Data kosong di tab '%s'", SHEET_LEMBAR_DISPOSISI)
        return stats

    header = values[0]
    rows = values[1:]
    stats["total"] = len(rows)
    log.info("Header %s: %s", SHEET_LEMBAR_DISPOSISI, header)

    with conn.cursor() as cur:
        for row_num, row in enumerate(rows, start=2):
            # 4 columns (A, B, C, D) - flexible mapping berdasarkan header
            col_a = get_cell(row, 0)
            col_b = get_cell(row, 1)
            col_c = get_cell(row, 2)
            col_d = get_cell(row, 3)
            
            # Heuristic mapping: detect content type
            nomor_disposisi = ""
            tanggal_disposisi = None
            dari_disposisi = ""
            perihal_disposisi = ""
            
            for i, h in enumerate(header[:4]):
                h_upper = str(h).upper().strip()
                val = get_cell(row, i)
                if 'NOMOR' in h_upper and 'DISPO' in h_upper:
                    nomor_disposisi = val
                elif 'TANGGAL' in h_upper or 'TGL' in h_upper:
                    try:
                        tanggal_disposisi = parse_date(val)
                    except:
                        pass
                elif 'DARI' in h_upper or 'PENGIRIM' in h_upper or 'OLEH' in h_upper:
                    dari_disposisi = val
                elif 'PERIHAL' in h_upper or 'HAL' in h_upper or 'ISI' in h_upper:
                    perihal_disposisi = val
            
            # Fallback positional: A=nomor, B=tanggal, C=dari, D=perihal
            if not nomor_disposisi:
                nomor_disposisi = col_a
            if not tanggal_disposisi:
                tanggal_disposisi = parse_date(col_b)
            if not dari_disposisi:
                dari_disposisi = col_c
            if not perihal_disposisi:
                perihal_disposisi = col_d

            unique_id = make_unique_id("LDULA", nomor_disposisi, dari_disposisi, row_num)

            cur.execute(
                """
                INSERT INTO lembar_disposisi_bangda (
                    unique_id,
                    nomor_disposisi,
                    tanggal_disposisi,
                    dari_disposisi,
                    perihal_disposisi,
                    source_sheet,
                    source_row
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (unique_id) DO UPDATE SET
                    nomor_disposisi   = EXCLUDED.nomor_disposisi,
                    tanggal_disposisi = EXCLUDED.tanggal_disposisi,
                    dari_disposisi    = EXCLUDED.dari_disposisi,
                    perihal_disposisi = EXCLUDED.perihal_disposisi,
                    source_row        = EXCLUDED.source_row,
                    updated_at        = NOW()
                RETURNING id, (xmax = 0) AS is_insert
                """,
                (
                    unique_id,
                    nomor_disposisi,
                    tanggal_disposisi.isoformat() if tanggal_disposisi else None,
                    dari_disposisi,
                    perihal_disposisi,
                    SHEET_LEMBAR_DISPOSISI,
                    row_num
                )
            )
            row_result = cur.fetchone()
            if row_result:
                _, is_insert = row_result[0], row_result[1]
                if is_insert:
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1

    log.info(
        "Tab '%s': total=%d inserted=%d updated=%d skipped=%d",
        SHEET_LEMBAR_DISPOSISI, stats["total"], stats["inserted"],
        stats["updated"], stats["skipped"]
    )
    return stats


# ── Proses tab "Dispo DJ/TU Pim" dan "Dispo Ses" ───────────────────────────
def process_disposisi_distributions(conn, sheet_name: str, source_tab: str) -> Dict[str, int]:
    """Process distribusi disposisi dari tab tertentu."""
    stats = {"total": 0, "inserted": 0, "updated": 0, "skipped": 0}

    log.info("Fetching tab '%s'...", sheet_name)
    try:
        values = fetch_sheet_data(sheet_name, "A1:IH5000")  # Wide range for all columns
    except Exception as e:
        log.error("Gagal fetch tab '%s': %s", sheet_name, e)
        return stats

    if len(values) <= 1:
        log.warning("Data kosong di tab '%s'", sheet_name)
        return stats

    header = values[0]
    rows = values[1:]
    stats["total"] = len(rows)
    log.info("Tab '%s' has %d columns, %d rows", sheet_name, len(header), len(rows))

    # Build header-to-index mapping
    header_map = {}
    for i, h in enumerate(header):
        h_upper = str(h).upper().strip()
        header_map[h_upper] = i

    log.info("Tab '%s' header: %s", sheet_name, header[:12])

    # Dispo Ses column mapping (by position, NOT header name):
    #   A(0)=Timestamp, B(1)=No Agenda Dirjen, C(2)=No Agenda Ses
    #   D(3)=Tgl Disposisi Ses, E(4)=Arahan Ses, F(5)=Diteruskan kepada
    #   G(6)=Catatan, H(7)=Unggahan, I(8)=Column 9
    
    # Dispo DJ/TU Pim column mapping:
    #   A(0)=Timestamp, B(1)=Dispo Dari, C(2)=No. Agenda
    #   D(3)=Tgl Disposisi, E(4)=Diteruskan Kepada, F(5)=Arahan
    #   G(6)=Unggahan, H(7)=Catatan, I(8)=KAsubbag TU PEIPD

    def get_pos(row: List[Any], idx: int) -> str:
        return get_cell(row, idx)

    with conn.cursor() as cur:
        for row_num, row in enumerate(rows, start=2):
            if source_tab == "Dispo Ses":
                # Dispo Ses: B=index 1 = No Agenda Dirjen, C=index 2 = No Agenda Ses
                agenda_dirjen = get_pos(row, 1)   # Column B: No Agenda Dirjen (matches agenda_ula)
                agenda_ses = get_pos(row, 2)      # Column C: No Agenda Ses
                tgl_str = get_pos(row, 3)         # Column D: Tgl Disposisi Ses
                arahan = get_pos(row, 4)          # Column E: Arahan Ses
                kepada = get_pos(row, 5)          # Column F: Diteruskan kepada
                catatan = get_pos(row, 6)         # Column G: Catatan
                
                nomor_disposisi = f"{agenda_dirjen}"
                tanggal_disposisi = parse_date(tgl_str)
                dari = "Sekretaris Dirjen"
                isi_disposisi = f"Arahan: {arahan}\nCatatan: {catatan}" if arahan else catatan
                batas_waktu = None
                
                # Build unique_id using agenda_dirjen for linking
                unique_id = make_unique_id(f"DD_SES", agenda_dirjen, f"{kepada}", row_num)
                
            else:
                # Dispo DJ/TU Pim
                timestamp_raw = get_pos(row, 0)    # Column A
                dispo_dari = get_pos(row, 1)       # Column B: Dispo Dari
                no_agenda = get_pos(row, 2)        # Column C: No. Agenda
                tgl_str = get_pos(row, 3)          # Column D: Tgl Disposisi
                kepada = get_pos(row, 4)           # Column E: Diteruskan Kepada
                arahan = get_pos(row, 5)           # Column F: Arahan
                
                nomor_disposisi = f"{no_agenda}"
                tanggal_disposisi = parse_date(tgl_str)
                dari = dispo_dari
                isi_disposisi = f"Arahan: {arahan}" if arahan else ""
                batas_waktu = None
                
                unique_id = make_unique_id(f"DD_DJTU", no_agenda, f"{kepada}", row_num)

            # Skip empty rows
            if not nomor_disposisi and not dari and not kepada:
                stats["skipped"] += 1
                continue

            cur.execute(
                """
                INSERT INTO disposisi_distributions (
                    unique_id,
                    nomor_disposisi,
                    no_agenda_ses,
                    tanggal_disposisi,
                    dari,
                    kepada,
                    isi_disposisi,
                    batas_waktu,
                    source_tab,
                    source_row
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (unique_id) DO UPDATE SET
                    nomor_disposisi  = EXCLUDED.nomor_disposisi,
                    no_agenda_ses    = EXCLUDED.no_agenda_ses,
                    tanggal_disposisi = EXCLUDED.tanggal_disposisi,
                    dari             = EXCLUDED.dari,
                    kepada           = EXCLUDED.kepada,
                    isi_disposisi    = EXCLUDED.isi_disposisi,
                    batas_waktu      = EXCLUDED.batas_waktu,
                    source_row       = EXCLUDED.source_row,
                    updated_at       = NOW()
                RETURNING id, (xmax = 0) AS is_insert
                """,
                (
                    unique_id,
                    nomor_disposisi,
                    agenda_ses if source_tab == "Dispo Ses" else None,
                    tanggal_disposisi.isoformat() if tanggal_disposisi else None,
                    dari,
                    kepada,
                    isi_disposisi,
                    batas_waktu.isoformat() if batas_waktu else None,
                    source_tab,
                    row_num
                )
            )
            row_result = cur.fetchone()
            if row_result:
                _, is_insert = row_result[0], row_result[1]
                if is_insert:
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1

    log.info(
        "Tab '%s': total=%d inserted=%d updated=%d skipped=%d",
        sheet_name, stats["total"], stats["inserted"],
        stats["updated"], stats["skipped"]
    )
    return stats


# ── Run ETL ──────────────────────────────────────────────────────────────────
def run_etl() -> None:
    """Main ETL entry point."""
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL belum diset")

    log.info("=" * 60)
    log.info("ETL Surat Luar 2026 - Mulai")
    log.info("Spreadsheet: %s", SPREADSHEET_ID)
    log.info("=" * 60)

    total_stats = {}
    started_at = datetime.utcnow()

    with psycopg.connect(dsn) as conn:
        # 1. Process Surat Masuk
        stats = process_surat_masuk(conn)
        total_stats["surat_masuk"] = stats

        # 2. Process Lembar Disposisi
        stats = process_lembar_disposisi(conn)
        total_stats["lembar_disposisi"] = stats

        # 3. Process Dispo DJ/TU Pim
        stats = process_disposisi_distributions(conn, SHEET_DISPO_DJ_TU, "Dispo DJ/TU Pim")
        total_stats["dispo_dj_tu"] = stats

        # 4. Process Dispo Ses
        stats = process_disposisi_distributions(conn, SHEET_DISPO_SES, "Dispo Ses")
        total_stats["dispo_ses"] = stats

        # Commit all changes
        conn.commit()

    # Summary
    log.info("=" * 60)
    log.info("ETL Surat Luar 2026 - Selesai")
    for sheet, st in total_stats.items():
        log.info(
            "  %s: total=%d inserted=%d updated=%d skipped=%d",
            sheet, st.get("total", 0), st.get("inserted", 0),
            st.get("updated", 0), st.get("skipped", 0)
        )
    log.info("=" * 60)

    # Print JSON summary
    result = {
        "ok": True,
        "spreadsheet_id": SPREADSHEET_ID,
        "started_at": started_at.isoformat(),
        "finished_at": datetime.utcnow().isoformat(),
        "stats": {k: {str(kk): vv for kk, vv in v.items()} for k, v in total_stats.items()}
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # Set environment defaults
    creds_dir = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS_PATH")
    if not creds_dir:
        os.environ["GOOGLE_WORKSPACE_CREDENTIALS_PATH"] = \
            "/home/aseps/MCP/config/credentials/google/puubangda"
    
    token_file = os.getenv("GOOGLE_WORKSPACE_TOKEN_FILE")
    if not token_file:
        os.environ["GOOGLE_WORKSPACE_TOKEN_FILE"] = "token.json"
    
    run_etl()