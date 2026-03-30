#!/usr/bin/env python3
import json
import os
import re
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import psycopg

STORAGE_DIR = "/home/aseps/MCP/storage/admin_data/korespondensi"

DEFAULT_FILES = [
    ("korespondensi_internal_pooling", "korespondensi_internal_pooling_data.json", "internal"),
    ("korespondensi_sekretariat_dispo_puu", "korespondensi_sekretariat_dispo_puu_data.json", "external"),
]


def parse_date(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() == "null":
        return None

    months = {
        "JAN": 1, "JANUARI": 1,
        "FEB": 2, "FEBRUARI": 2,
        "MAR": 3, "MARET": 3,
        "APR": 4, "APRIL": 4,
        "MEI": 5,
        "JUN": 6, "JUNI": 6,
        "JUL": 7, "JULI": 7,
        "AGU": 8, "AGUSTUS": 8,
        "SEP": 9, "SEPT": 9, "SEPTEMBER": 9,
        "OKT": 10, "OKTOBER": 10,
        "NOV": 11, "NOVEMBER": 11,
        "DES": 12, "DESEMBER": 12,
    }

    up = s.upper()
    for m, num in months.items():
        up = re.sub(rf"\\b{m}\\b", str(num), up)

    clean = re.sub(r"[^0-9]", "/", up)
    clean = re.sub(r"/+", "/", clean).strip("/")
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(clean, fmt)
            if dt.year < 100:
                dt = dt.replace(year=dt.year + 2000)
            return dt.date().isoformat()
        except ValueError:
            continue
    return None


def find_idx(header: List[str], patterns: List[str], default: int = -1) -> int:
    for i, h in enumerate(header):
        hu = str(h).upper()
        if any(p in hu for p in patterns):
            return i
    return default


def safe_get(row: List[Any], idx: int) -> str:
    if idx < 0 or idx >= len(row):
        return ""
    v = row[idx]
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() == "null" else s


def infer_source_type(namespace: str, sender: str) -> str:
    ns = namespace.lower()
    if "dispo" in ns or "eksternal" in ns or "external" in ns:
        return "external"
    if "pooling" in ns and "PUU" in sender.upper():
        return "outgoing"
    return "internal"


def make_dedupe_key(namespace: str, row_num: int, letter_number: str, sender: str, subject: str, letter_date: Optional[str]) -> str:
    raw = f"{namespace}|{row_num}|{letter_number}|{sender}|{subject}|{letter_date or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def extract_records(namespace: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    values = data.get("values", [])
    if len(values) <= 1:
        return []

    header = values[0]
    rows = values[1:]

    idx_num = find_idx(header, ["NOMOR SURAT", "NOMOR", "NO", "ND", "REF"]) 
    idx_tgl = find_idx(header, ["TANGGAL SURAT", "TGL SURAT", "TANGGAL", "TGL"]) 
    idx_tgl_terima = find_idx(header, ["DITERIMA PUU", "TGL DITERIMA", "TANGGAL DITERIMA"]) 
    idx_sender = find_idx(header, ["SURAT DARI", "DARI", "PENGIRIM"]) 
    idx_recipient = find_idx(header, ["KEPADA", "TUJUAN", "PENERIMA"]) 
    idx_subject = find_idx(header, ["PERIHAL", "HAL", "ISI"]) 
    idx_pos = find_idx(header, ["POSISI", "STATUS POSISI"]) 
    idx_dispo = find_idx(header, ["DISPOSISI", "ARAHAN"]) 

    out: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, start=2):
        sender = safe_get(row, idx_sender)
        subject = safe_get(row, idx_subject)
        if not sender and not subject:
            continue

        letter_number = safe_get(row, idx_num)
        letter_date = parse_date(safe_get(row, idx_tgl))
        received_date = parse_date(safe_get(row, idx_tgl_terima))
        recipient = safe_get(row, idx_recipient)
        position_raw = safe_get(row, idx_pos)
        disposition_raw = safe_get(row, idx_dispo)

        source_type = infer_source_type(namespace, sender)
        dedupe_key = make_dedupe_key(namespace, i, letter_number, sender, subject, letter_date)

        out.append({
            "source_namespace": namespace,
            "source_sheet_id": data.get("spreadsheet_id"),
            "source_range": data.get("range"),
            "source_row_num": i,
            "source_type": source_type,
            "letter_number": letter_number,
            "letter_date": letter_date,
            "received_date": received_date,
            "sender": sender,
            "recipient": recipient,
            "subject": subject,
            "position_raw": position_raw,
            "disposition_raw": disposition_raw,
            "status": position_raw or disposition_raw or "",
            "payload": dict(zip([str(h) for h in header], row)),
            "dedupe_key": dedupe_key,
        })
    return out


def run_migration(dsn: str, files: List[Tuple[str, str, str]]) -> Dict[str, int]:
    stats = {"inserted": 0, "updated": 0, "skipped": 0}

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for namespace, filename, _ in files:
                path = os.path.join(STORAGE_DIR, filename)
                if not os.path.exists(path):
                    continue

                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                records = extract_records(namespace, data)
                for rec in records:
                    cur.execute(
                        """
                        INSERT INTO correspondence_letters (
                            source_namespace, source_sheet_id, source_range, source_row_num,
                            source_type, letter_number, letter_date, received_date,
                            sender, recipient, subject, position_raw, disposition_raw,
                            status, payload, dedupe_key
                        ) VALUES (
                            %(source_namespace)s, %(source_sheet_id)s, %(source_range)s, %(source_row_num)s,
                            %(source_type)s, %(letter_number)s, %(letter_date)s, %(received_date)s,
                            %(sender)s, %(recipient)s, %(subject)s, %(position_raw)s, %(disposition_raw)s,
                            %(status)s, %(payload)s::jsonb, %(dedupe_key)s
                        )
                        ON CONFLICT (dedupe_key)
                        DO UPDATE SET
                            source_sheet_id = EXCLUDED.source_sheet_id,
                            source_range = EXCLUDED.source_range,
                            source_row_num = EXCLUDED.source_row_num,
                            source_type = EXCLUDED.source_type,
                            letter_number = EXCLUDED.letter_number,
                            letter_date = EXCLUDED.letter_date,
                            received_date = EXCLUDED.received_date,
                            sender = EXCLUDED.sender,
                            recipient = EXCLUDED.recipient,
                            subject = EXCLUDED.subject,
                            position_raw = EXCLUDED.position_raw,
                            disposition_raw = EXCLUDED.disposition_raw,
                            status = EXCLUDED.status,
                            payload = EXCLUDED.payload,
                            synced_at = NOW(),
                            updated_at = NOW()
                        RETURNING (xmax = 0) AS inserted
                        """,
                        rec,
                    )
                    inserted = cur.fetchone()[0]
                    if inserted:
                        stats["inserted"] += 1
                    else:
                        stats["updated"] += 1

    return stats


def main():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL belum diset")

    stats = run_migration(dsn, DEFAULT_FILES)
    print(json.dumps({"ok": True, "stats": stats}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
