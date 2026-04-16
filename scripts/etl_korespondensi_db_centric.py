#!/usr/bin/env python3
"""
ETL Korespondensi Database-Centric
===================================
Menggantikan ketergantungan pada spreadsheet 1BtKu...
Membaca langsung dari 6 spreadsheet sumber unit,
melakukan filtering PUU, dan menyimpan ke PostgreSQL.

Flow:
  1. Baca korespondensi_source_config dari DB
  2. Fetch data tiap sheet via Google Sheets API
  3. Normalisasi + dedupe → korespondensi_raw_pool (UPSERT)
  4. Filter is_puu (DARI atau POSISI mengandung 'PUU') → surat_masuk_puu_internal (UPSERT)
  5. Ekstrak no_agenda_dispo dari kolom DISPOSISI via regex
  6. Log hasil ke korespondensi_sync_runs

Jalankan:
  python3 scripts/etl_korespondensi_db_centric.py
  # atau dengan DATABASE_URL eksplisit:
  DATABASE_URL=postgres://... python3 scripts/etl_korespondensi_db_centric.py
"""
import os
import re
import sys
import json
import hashlib
import logging
import subprocess
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import psycopg

PROJECT_ROOT = "/home/aseps/MCP/mcp-unified"
sys.path.insert(0, PROJECT_ROOT)
from core.secrets import load_runtime_secrets  # type: ignore
from integrations.korespondensi.utils import extract_puu_received_date  # type: ignore

load_runtime_secrets()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("etl_korespondensi")

# ── regex untuk ekstrak nomor agenda dari DISPOSISI ──────────────────────────
AGENDA_REGEX = re.compile(
    r'\d{4}/[A-Za-z0-9\s\.\-]+(?:/[A-Za-z0-9\s\.\-]+)*(?:/\d{4})?'
)

# ── Mapping kode DARI → nama lengkap (sinkron dengan dari_lookup di DB) ──────
_DARI_RAW = {
    "BU": "Bagian Umum",
    "UM": "Bagian Umum",
    "TU": "Tata Usaha",
    "TU SUPD II": "Tata Usaha SUPD II",
    "PRC": "Bagian Perencanaan",
    "PUU": "Substansi Perundang-Undangan",
    "KEU": "Bagian Keuangan",
    "SD I": "Subdit Wilayah I",
    "SD.I": "Subdit Wilayah I",
    "SD 1": "Subdit Wilayah I",
    "SD II": "Subdit Wilayah II",
    "SD.II": "Subdit Wilayah II",
    "SD III": "Subdit Wilayah III",
    "SD.III": "Subdit Wilayah III",
    "SD IV": "Subdit Wilayah IV",
    "SD.IV": "Subdit Wilayah IV",
    "SD V": "Subdit Wilayah V",
    "SD.V": "Subdit Wilayah V",
    "SD VI": "Subdit Wilayah VI",
    "SD.VI": "Subdit Wilayah VI",
    "SD PMIPD": "Subdit PMIPD",
    "SD.PMIPD": "Subdit PMIPD",
    "SD PIMPD": "Subdit PMIPD",
    "SD": "Subdit",
    "PEIPD": "Direktorat PEIPD",
    "PMIPD": "Subdit PMIPD",
    "SUPD I": "Direktorat SUPD I",
    "SUPD II": "Direktorat SUPD II",
    "SUPD III": "Direktorat SUPD III",
    "SUPD IV": "Direktorat SUPD IV",
    "PPK": "Pejabat Pembuat Komitmen",
    "BANGDA": "Ditjen Bina Pembangunan Daerah",
    "UN": "Unit Pengelola (Belum Terdefinisi)",
}
DARI_LOOKUP: dict = {}
for _k, _v in _DARI_RAW.items():
    _norm = re.sub(r'[\s\.]+', ' ', _k.upper()).strip()
    DARI_LOOKUP[_norm] = _v


def map_dari(dari: str) -> str:
    """Kembalikan nama lengkap dari kode DARI, fallback ke nilai asli."""
    if not dari:
        return ""
    norm = re.sub(r'[\s\.]+', ' ', dari.strip().upper()).strip()
    return DARI_LOOKUP.get(norm, dari.strip())


# Bulan Indonesia → angka
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


def parse_posisi_date(posisi_str: str, fallback_year: int = 2026) -> Optional[datetime]:
    """Ekstrak tanggal dari string posisi (mis: 'PUU 17/3' -> 2026-03-17)."""
    if not posisi_str:
        return None
    # Cari pola dd/mm atau dd/m atau d/m (mis: 17/3, 2/4)
    m = re.search(r'(\d{1,2})\s*/\s*(\d{1,2})', posisi_str)
    if m:
        try:
            day, month = int(m.group(1)), int(m.group(2))
            # Sesuaikan tahun jika Desember -> 2025
            year = fallback_year - 1 if month == 12 else fallback_year
            return datetime(year, month, day)
        except (ValueError, TypeError):
            pass
    return None


def make_unique_id(no_agenda: str, nomor_nd: str) -> str:
    """
    Buat ID stabil dari gabungan NO AGENDA + NOMOR ND.
    
    Menggunakan no_agenda + nomor_nd karena:
    1. Kombinasi ini unik untuk setiap surat
    2. Tidak bergantung pada tanggal yang bisa NULL atau inkonsisten
    3. Mencegah duplikasi data
    
    Contoh:
    - no_agenda="0097", nomor_nd="500.5/40/SD/SUPD II" → "0097_500.5/40/sd/supd ii"
    - no_agenda="0120", nomor_nd="500.5/40/SD/SUPD II" → "0120_500.5/40/sd/supd ii"
    """
    agenda_part = str(no_agenda).strip() if no_agenda else "NOAGENDA"
    nd_part = str(nomor_nd).strip() if nomor_nd else "NOND"
    raw = f"{agenda_part}_{nd_part}".lower()
    # Bersihkan karakter yang tidak aman untuk ID
    raw = re.sub(r'[\s\/]+', '_', raw)
    return raw


def extract_agenda(disposisi: str) -> Optional[str]:
    """Ekstrak nomor agenda dari teks disposisi."""
    if not disposisi:
        return None
    m = AGENDA_REGEX.search(disposisi)
    return m.group(0) if m else None


def is_surat_keluar_puu(nomor_nd: str) -> bool:
    """Cek apakah surat adalah surat keluar PUU."""
    import re as _r
    return bool(_r.search(r'/\s*PUU\s*$', nomor_nd.strip(), _r.IGNORECASE))


def is_puu_row(dari: str, posisi: str, nomor_nd: str = "", disposisi: str = "") -> Tuple[bool, str, bool]:
    """
    Tentukan apakah baris ini masuk kategori PUU berdasarkan kondisi ketat:
    1. Surat Keluar: ND berakhiran /PUU
    2. Surat Masuk: disposisi memuat format REG \d{3,4}/.+/\d{4} & posisi mengandung 'PUU.*?\d{1,2}/\d{1,2}'
    """
    import re as _r
    # Cek surat keluar PUU
    if _r.search(r'/\s*PUU\s*$', nomor_nd.strip(), _r.IGNORECASE):
        return False, f"surat keluar PUU (nomor ND berakhiran /PUU): {nomor_nd}", True
    
    posisi_up = (posisi or "").upper()
    disposisi_up = (disposisi or "").upper()
    
    is_valid_reg = bool(_r.search(r'\d{3,4}/.+/\d{4}', disposisi_up))
    is_valid_posisi = bool(_r.search(r'PUU.*?\d{1,2}/\d{1,2}', posisi_up))
    
    if is_valid_reg and is_valid_posisi:
        return True, f"POSISI & REG (Disposisi) valid PUU", False
        
    return False, "", False


def fetch_sheet_data(spreadsheet_id: str, sheet_name: str) -> List[List[Any]]:
    """Fetch raw data dari Google Sheets."""
    from integrations.google_workspace.client import get_google_client  # type: ignore
    client = get_google_client()
    svc = client.sheets
    rng = f"'{sheet_name}'!A1:Z5000"
    result = svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=rng
    ).execute()
    return result.get("values", [])


def normalize_header(header: List[str]) -> Dict[str, int]:
    """Buat mapping nama kolom ke index, case-insensitive."""
    mapping = {}
    for i, h in enumerate(header):
        h_clean = str(h).strip().upper()
        if "NO AGENDA" in h_clean or "NOMOR AGENDA" in h_clean:
            mapping["NO_AGENDA"] = i
        elif "TANGGAL" in h_clean or "TGL" in h_clean:
            if "NO_AGENDA" not in mapping:
                mapping.setdefault("TANGGAL", i)
            mapping.setdefault("TANGGAL", i)
        elif "NOMOR ND" in h_clean or "NOMOR" in h_clean or h_clean in ("NO", "ND", "NOMOR"):
            mapping.setdefault("NOMOR_ND", i)
        elif "DARI" in h_clean or "PENGIRIM" in h_clean:
            mapping.setdefault("DARI", i)
        elif "HAL" in h_clean or "PERIHAL" in h_clean or "ISI" in h_clean:
            mapping.setdefault("HAL", i)
        elif "POSISI" in h_clean or "STATUS" in h_clean:
            mapping.setdefault("POSISI", i)
        elif "DISPOSISI" in h_clean or "ARAHAN" in h_clean:
            mapping.setdefault("DISPOSISI", i)
    # Fallback positional (sesuai format sumber unit yg umum: col2=TGL, col3=NOMOR_ND, dll)
    mapping.setdefault("NO_AGENDA", 0)
    mapping.setdefault("TANGGAL", 1)
    mapping.setdefault("NOMOR_ND", 2)
    mapping.setdefault("DARI", 3)
    mapping.setdefault("HAL", 4)
    mapping.setdefault("POSISI", 5)
    mapping.setdefault("DISPOSISI", 6)
    return mapping


def get(row: List[Any], idx_map: Dict[str, int], key: str) -> str:
    idx = idx_map.get(key, -1)
    if idx < 0 or idx >= len(row):
        return ""
    v = row[idx]
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() == "null" else s


def process_source(
    conn,
    unit_name: str,
    spreadsheet_id: str,
    sheet_name: str,
    skip_sheets: Optional[List[str]] = None,
    data_group: str = "INTERNAL"
) -> Dict[str, int]:
    stats = {"total": 0, "inserted_raw": 0, "updated_raw": 0, "surat_puu": 0, "skipped": 0}

    # Skip jika sheet ada dalam daftar skip_sheets
    if skip_sheets and sheet_name in skip_sheets:
        log.info("SKIP sheet %s / %s (terdaftar di skip_sheets)", unit_name, sheet_name)
        return stats

    log.info("Fetching %s / %s (%s)", unit_name, sheet_name, data_group)
    try:
        values = fetch_sheet_data(spreadsheet_id, sheet_name)
    except Exception as e:
        log.error("Gagal fetch %s: %s", unit_name, e)
        return stats

    if len(values) <= 1:
        log.warning("Data kosong di %s", unit_name)
        return stats

    header = values[0]
    rows = values[1:]
    idx_map = normalize_header(header)
    stats["total"] = len(rows)

    with conn.cursor() as cur:
        for row_num, row in enumerate(rows, start=2):
            nomor_nd_raw = get(row, idx_map, "NOMOR_ND")
            if not nomor_nd_raw:
                stats["skipped"] += 1
                continue
            # Anti-header baris
            if nomor_nd_raw.upper() in ("NOMOR ND", "NOMOR", "NO"):
                stats["skipped"] += 1
                continue

            tanggal = parse_date(get(row, idx_map, "TANGGAL"))
            no_agenda_val = get(row, idx_map, "NO_AGENDA")
            unique_id = make_unique_id(no_agenda_val, nomor_nd_raw)

            dari_val = get(row, idx_map, "DARI")
            hal_val = get(row, idx_map, "HAL")
            posisi_val = get(row, idx_map, "POSISI")
            disposisi_val = get(row, idx_map, "DISPOSISI")
            no_agenda_val = get(row, idx_map, "NO_AGENDA")

            # Upsert ke raw_pool dengan identitas unit resmi
            cur.execute(
                """
                INSERT INTO korespondensi_raw_pool (
                    unique_id, no_agenda, tanggal, nomor_nd,
                    dari, hal, posisi, disposisi,
                    source_spreadsheet_id, source_sheet_name, source_row_num,
                    sheet_identity, owner_unit, data_group
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (unique_id) DO UPDATE SET
                    no_agenda    = EXCLUDED.no_agenda,
                    tanggal      = EXCLUDED.tanggal,
                    nomor_nd     = EXCLUDED.nomor_nd,
                    dari         = EXCLUDED.dari,
                    hal          = EXCLUDED.hal,
                    posisi       = EXCLUDED.posisi,
                    disposisi    = EXCLUDED.disposisi,
                    source_spreadsheet_id = EXCLUDED.source_spreadsheet_id,
                    source_sheet_name     = EXCLUDED.source_sheet_name,
                    source_row_num        = EXCLUDED.source_row_num,
                    sheet_identity        = EXCLUDED.sheet_identity,
                    owner_unit            = EXCLUDED.owner_unit,
                    data_group            = EXCLUDED.data_group,
                    updated_at            = NOW()
                RETURNING id, (xmax = 0) AS is_insert
                """,
                (
                    unique_id, no_agenda_val,
                    tanggal.isoformat() if tanggal else None,
                    nomor_nd_raw, dari_val, hal_val, posisi_val, disposisi_val,
                    spreadsheet_id, sheet_name, row_num,
                    unit_name, unit_name, data_group
                )
            )
            row_result = cur.fetchone()
            raw_id, is_insert = row_result[0], row_result[1]
            
            # Check for position change to log in timeline
            cur.execute("SELECT posisi FROM surat_masuk_puu_internal WHERE unique_id = %s", (unique_id,))
            old_internal = cur.fetchone()
            old_posisi = old_internal[0] if old_internal else None
            
            if is_insert:
                stats["inserted_raw"] += 1
            else:
                stats["updated_raw"] += 1

            # Check if surat masuk or keluar PUU
            is_masuk, reason, is_keluar = is_puu_row(dari_val, posisi_val, nomor_nd_raw, disposisi_val)
            
            # Handle surat keluar PUU (NOMOR ND ending with /PUU)
            if is_keluar:
                cur.execute("""
                    INSERT INTO surat_keluar_puu (
                        unique_id, tanggal_surat, nomor_nd,
                        dari, hal, filter_reason, raw_pool_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (unique_id) DO UPDATE SET
                        tanggal_surat = EXCLUDED.tanggal_surat,
                        nomor_nd = EXCLUDED.nomor_nd,
                        dari = EXCLUDED.dari,
                        hal = EXCLUDED.hal,
                        filter_reason = EXCLUDED.filter_reason,
                        raw_pool_id = EXCLUDED.raw_pool_id,
                        updated_at = NOW()
                """, (unique_id, tanggal.isoformat() if tanggal else None,
                      nomor_nd_raw, dari_val, hal_val, reason, raw_id))
                stats["surat_keluar"] = stats.get("surat_keluar", 0) + 1
                continue
            
            if not is_masuk:
                continue

            no_agenda_dispo = extract_agenda(disposisi_val)
            dari_full_val   = map_dari(dari_val)
            
            # Ekstrak tanggal diterima PUU dari kolom POSISI
            tanggal_diterima_puu = None
            puu_date_str = extract_puu_received_date(posisi_val)
            if puu_date_str:
                parts = puu_date_str.split('/')
                if len(parts) == 2:
                    try:
                        puu_day = int(parts[0])
                        puu_month = int(parts[1])
                        # Asumsi tahun 2026 (atau 2025 untuk bulan Desember)
                        puu_year = 2025 if puu_month == 12 and tanggal and tanggal.month == 1 else 2026
                        tanggal_diterima_puu = date(puu_year, puu_month, puu_day)
                    except (ValueError, TypeError):
                        pass

            # Upsert ke surat_masuk_puu_internal (termasuk dari_full dan tanggal_diterima_puu)
            cur.execute(
                """
                INSERT INTO surat_masuk_puu_internal (
                    unique_id, tanggal_surat, nomor_nd,
                    dari, dari_full, hal, no_agenda_dispo,
                    is_puu, filter_reason, raw_pool_id, tanggal_diterima_puu,
                    posisi
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE,%s,%s,%s,%s)
                ON CONFLICT (unique_id) DO UPDATE SET
                    tanggal_surat    = EXCLUDED.tanggal_surat,
                    nomor_nd         = EXCLUDED.nomor_nd,
                    dari             = EXCLUDED.dari,
                    dari_full        = EXCLUDED.dari_full,
                    hal              = EXCLUDED.hal,
                    no_agenda_dispo  = COALESCE(EXCLUDED.no_agenda_dispo, surat_masuk_puu_internal.no_agenda_dispo),
                    filter_reason    = EXCLUDED.filter_reason,
                    raw_pool_id      = EXCLUDED.raw_pool_id,
                    tanggal_diterima_puu = COALESCE(EXCLUDED.tanggal_diterima_puu, surat_masuk_puu_internal.tanggal_diterima_puu),
                    posisi           = EXCLUDED.posisi,
                    updated_at       = NOW()
                RETURNING id
                """,
                (
                    unique_id,
                    tanggal.isoformat() if tanggal else None,
                    nomor_nd_raw, 
                    f"{dari_val} - {sheet_name}" if dari_val else sheet_name, 
                    dari_full_val, hal_val,
                    no_agenda_dispo, reason, raw_id,
                    tanggal_diterima_puu.isoformat() if tanggal_diterima_puu else None,
                    posisi_val
                )
            )
            internal_id = cur.fetchone()[0]
            
            # Log to timeline if position changed
            if old_posisi != posisi_val:
                extracted_dt = parse_posisi_date(posisi_val)
                event_time = extracted_dt if extracted_dt else datetime.now()
                
                cur.execute("""
                    INSERT INTO correspondence_events (letter_id, event_type, event_value, event_at)
                    VALUES (%s, 'posisi_change', %s, %s)
                """, (internal_id, posisi_val, event_time))
                log.info("[%s] Timeline update: %s -> %s (extracted_at=%s)", unique_id, old_posisi, posisi_val, event_time)
            stats["surat_puu"] += 1

    return stats


def run_etl() -> None:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL belum diset")

    with psycopg.connect(dsn) as conn:
        # Ambil konfigurasi sumber aktif dari DB (termasuk skip_sheets)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT unit_name, spreadsheet_id, sheet_name, "
                "       COALESCE(skip_sheets, '[]'::jsonb) AS skip_sheets "
                "FROM korespondensi_source_config WHERE is_active = TRUE ORDER BY id"
            )
            sources = cur.fetchall()

        if not sources:
            log.warning("Tidak ada konfigurasi sumber aktif di korespondensi_source_config")
            return

        total_stats: Dict[str, int] = {
            "total": 0, "inserted_raw": 0, "updated_raw": 0,
            "surat_puu": 0, "skipped": 0
        }
        started_at = datetime.utcnow()

        for unit_name, spreadsheet_id, sheet_name, skip_sheets_val in sources:
            # psycopg3 auto-deserialize JSONB → Python list
            skip_sheets_list = skip_sheets_val if isinstance(skip_sheets_val, list) else []
            if skip_sheets_list:
                log.info("[%s] skip_sheets aktif: %s", unit_name, skip_sheets_list)
            
            # Tentukan grup data (Isolasi)
            # Unit Master Bangda atau Surat Masuk Umum masuk ke EXTERNAL
            group = "EXTERNAL" if "BANGDA" in unit_name.upper() or "SURAT MASUK" in sheet_name.upper() else "INTERNAL"
            
            stats = process_source(conn, unit_name, spreadsheet_id, sheet_name,
                                   skip_sheets=skip_sheets_list, data_group=group)
            for k in total_stats:
                total_stats[k] += stats.get(k, 0)
            log.info(
                "[%s] total=%d inserted_raw=%d surat_puu=%d skipped=%d",
                unit_name, stats["total"], stats["inserted_raw"],
                stats["surat_puu"], stats["skipped"]
            )
            # Update last_synced_at
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE korespondensi_source_config "
                    "SET last_synced_at=NOW(), last_row_count=%s "
                    "WHERE unit_name=%s",
                    (stats["total"], unit_name)
                )

        # Auto-populate lembar_disposisi dari surat_masuk_puu_internal + raw_pool
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO lembar_disposisi (surat_id, unique_id, agenda_puu, direktorat)
                SELECT
                    sp.id,
                    sp.unique_id,
                    LPAD(ROW_NUMBER() OVER (ORDER BY sp.tanggal_surat, sp.id)::TEXT, 3, '0') || '-I',
                    CASE rp.source_sheet_name
                        WHEN 'SEKRETARIAT' THEN 'Sekretariat'
                        WHEN 'PEIPD'       THEN 'Direktorat PEIPD'
                        WHEN 'SUPD I'      THEN 'Direktorat SUPD I'
                        WHEN 'SUPD II'     THEN 'Direktorat SUPD II'
                        WHEN 'SUPD III'    THEN 'Direktorat SUPD III'
                        WHEN 'SUPD IV'     THEN 'Direktorat SUPD IV'
                        ELSE rp.source_sheet_name
                    END
                FROM surat_masuk_puu_internal sp
                JOIN korespondensi_raw_pool rp ON rp.id = sp.raw_pool_id
                ON CONFLICT (unique_id) DO UPDATE SET
                    direktorat = EXCLUDED.direktorat,
                    updated_at = NOW()
            """)
            # Keep agenda_puu mirrored in surat_masuk_puu_internal because the
            # native DOCX mailmerge reads from this table directly.
            cur.execute("""
                UPDATE surat_masuk_puu_internal sp
                SET agenda_puu = ld.agenda_puu,
                    updated_at = NOW()
                FROM lembar_disposisi ld
                WHERE ld.unique_id = sp.unique_id
                  AND ld.agenda_puu IS NOT NULL
                  AND (sp.agenda_puu IS NULL OR sp.agenda_puu = '')
            """)
        log.info("lembar_disposisi auto-populated: %d rows", total_stats["surat_puu"])

        conn.commit()

        # Log ke sync_runs jika tabel tersedia
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO correspondence_sync_runs
                        (source_namespace, source_file, total_rows, inserted_rows,
                         updated_rows, skipped_rows, started_at, finished_at, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                    """,
                    (
                        "korespondensi_all_units",
                        "etl_korespondensi_db_centric",
                        total_stats["total"],
                        total_stats["inserted_raw"],
                        total_stats["updated_raw"],
                        total_stats["skipped"],
                        started_at,
                        json.dumps({"surat_puu": total_stats["surat_puu"]})
                    )
                )
            conn.commit()
        except Exception:
            pass

    # Optional workflow audit: capture POSISI mapping health after ETL.
    try:
        audit_script = os.path.join("/home/aseps/MCP/korespondensi-server", "scripts", "report_puu_posisi_mapping.py")
        audit_json = os.path.join("/home/aseps/MCP/korespondensi-server", "storage", "admin_data", "korespondensi", "puu_posisi_mapping_audit.json")
        os.makedirs(os.path.dirname(audit_json), exist_ok=True)
        subprocess.run(
            [sys.executable, audit_script, "--limit", "50", "--json-out", audit_json],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log.info("POSISI audit workflow completed: %s", audit_json)
    except Exception as e:
        log.warning("POSISI audit workflow skipped: %s", e)

    result = {
        "ok": True,
        "stats": total_stats,
        "finished_at": datetime.utcnow().isoformat()
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run_etl()
