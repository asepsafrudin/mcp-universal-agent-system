#!/usr/bin/env python3
"""
Patch tanggal_surat yang NULL di korespondensi_raw_pool dan surat_masuk_puu.

Cara kerja:
  1. Re-fetch data dari Google Sheets
  2. Parse tanggal dengan format baru (strip timestamp '02/01/2026 11.44.02' → '02/01/2026')
  3. UPDATE korespondensi_raw_pool SET tanggal = parsed WHERE nomor_nd = ... AND tanggal IS NULL
  4. UPDATE surat_masuk_puu SET tanggal_surat = ... WHERE nomor_nd = ... AND tanggal_surat IS NULL

Jalankan:
  DATABASE_URL='postgresql://...' python3 scripts/patch_tanggal_surat.py
"""
import os, sys, re, json, logging
from datetime import datetime, date
from typing import Any, Optional, List, Dict

import psycopg

sys.path.insert(0, "/home/aseps/MCP/mcp-unified")
from core.secrets import load_runtime_secrets
load_runtime_secrets()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("patch_tanggal")

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
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val
    s = str(val).strip()
    if not s or s.lower() == "null":
        return None
    # Strip timestamp jika ada: '02/01/2026 11.44.02' → '02/01/2026'
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


def normalize_header(header: List[str]) -> Dict[str, int]:
    mapping = {}
    for i, h in enumerate(header):
        h_clean = str(h).strip().upper()
        if "NO AGENDA" in h_clean or "NOMOR AGENDA" in h_clean:
            mapping["NO_AGENDA"] = i
        elif "TANGGAL" in h_clean or "TGL" in h_clean:
            mapping.setdefault("TANGGAL", i)
        elif "NOMOR ND" in h_clean or "NOMOR" in h_clean or h_clean in ("NO", "ND"):
            mapping.setdefault("NOMOR_ND", i)
        elif "DARI" in h_clean or "PENGIRIM" in h_clean:
            mapping.setdefault("DARI", i)
        elif "HAL" in h_clean or "PERIHAL" in h_clean:
            mapping.setdefault("HAL", i)
        elif "POSISI" in h_clean:
            mapping.setdefault("POSISI", i)
        elif "DISPOSISI" in h_clean:
            mapping.setdefault("DISPOSISI", i)
    mapping.setdefault("NO_AGENDA", 0)
    mapping.setdefault("TANGGAL", 1)
    mapping.setdefault("NOMOR_ND", 2)
    mapping.setdefault("DARI", 3)
    mapping.setdefault("HAL", 4)
    mapping.setdefault("POSISI", 5)
    mapping.setdefault("DISPOSISI", 6)
    return mapping


def get_val(row, idx_map, key):
    idx = idx_map.get(key, -1)
    if idx < 0 or idx >= len(row):
        return ""
    v = row[idx]
    return "" if v is None else str(v).strip()


def fetch_sheet(spreadsheet_id, sheet_name):
    from integrations.google_workspace.client import get_google_client
    client = get_google_client()
    result = client.sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!A1:Z5000"
    ).execute()
    return result.get("values", [])


def run_patch():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL belum diset")

    with psycopg.connect(dsn) as conn:
        # Ambil konfigurasi sumber
        with conn.cursor() as cur:
            cur.execute("SELECT unit_name, spreadsheet_id, sheet_name FROM korespondensi_source_config WHERE is_active = TRUE ORDER BY id")
            sources = cur.fetchall()

        updated_raw = updated_surat = 0

        for unit_name, spreadsheet_id, sheet_name in sources:
            log.info("Processing %s / %s", unit_name, sheet_name)
            try:
                values = fetch_sheet(spreadsheet_id, sheet_name)
            except Exception as e:
                log.error("Gagal fetch %s: %s", unit_name, e)
                continue

            if len(values) <= 1:
                continue

            # Deteksi header — jika row[0] hanya 1 kolom (judul), pakai row[1]
            if len(values[0]) <= 2 and len(values) > 2:
                log.info("  Deteksi 2-row header: Row1='%s', Row2=%s", values[0][0], values[1][:4])
                header = values[1]
                data_rows = values[2:]
            else:
                header = values[0]
                data_rows = values[1:]

            idx_map = normalize_header(header)
            log.info("  Header mapping: TANGGAL=%d, NOMOR_ND=%d",
                     idx_map.get("TANGGAL",-1), idx_map.get("NOMOR_ND",-1))

            for row in data_rows:
                nomor_nd = get_val(row, idx_map, "NOMOR_ND").strip()
                if not nomor_nd or nomor_nd.upper() in ("NOMOR ND", "NOMOR", "NO"):
                    continue

                tanggal_raw = get_val(row, idx_map, "TANGGAL")
                tanggal = parse_date(tanggal_raw)
                if tanggal is None:
                    continue

                # Update korespondensi_raw_pool
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE korespondensi_raw_pool
                        SET tanggal = %s, updated_at = NOW()
                        WHERE nomor_nd = %s AND tanggal IS NULL
                    """, (tanggal.isoformat(), nomor_nd))
                    updated_raw += cur.rowcount

                # Update surat_masuk_puu
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE surat_masuk_puu
                        SET tanggal_surat = %s, updated_at = NOW()
                        WHERE nomor_nd = %s AND tanggal_surat IS NULL
                    """, (tanggal.isoformat(), nomor_nd))
                    updated_surat += cur.rowcount

            conn.commit()
            log.info("  Done %s: updated_raw=%d, updated_surat=%d", unit_name, updated_raw, updated_surat)

    # Verifikasi hasil
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(tanggal) as has_tanggal,
                    COUNT(*) - COUNT(tanggal) as still_null
                FROM korespondensi_raw_pool
            """)
            r = cur.fetchone()
            log.info("raw_pool: total=%d, has_tanggal=%d, still_null=%d", *r)

            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(tanggal_surat) as has_tanggal,
                    COUNT(*) - COUNT(tanggal_surat) as still_null
                FROM surat_masuk_puu
            """)
            r = cur.fetchone()
            log.info("surat_masuk_puu: total=%d, has_tanggal=%d, still_null=%d", *r)

    print(json.dumps({
        "ok": True,
        "updated_raw_pool": updated_raw,
        "updated_surat_masuk_puu": updated_surat,
    }, indent=2))


if __name__ == "__main__":
    run_patch()
