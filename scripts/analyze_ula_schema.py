#!/usr/bin/env python3
"""
Analisis Korelasi & Simplifikasi Skema Bangda
==============================================
Menganalisis korelasi antar tabel dan mengusulkan simplifikasi kolom.

Jalankan:
  python3 scripts/analyze_ula_schema.py
"""
import os
import sys
import psycopg

PROJECT_ROOT = "/home/aseps/MCP/mcp-unified"
sys.path.insert(0, PROJECT_ROOT)
from core.secrets import load_runtime_secrets

# Load and export DATABASE_URL
load_runtime_secrets()
dsn = os.getenv("DATABASE_URL")

if not dsn:
    raise RuntimeError("DATABASE_URL belum diset")

with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
        # 1. Check NULL ratio for each column
        print("=" * 80)
        print("ANALISIS 1: NULL RATIO PER KOLOM (surat_dari_luar_bangda)")
        print("=" * 80)
        
        cur.execute("""
            SELECT 
                'surat_dari' as kolom, count(surat_dari) as non_null, count(*) as total
            FROM surat_dari_luar_bangda
            UNION ALL SELECT 'nomor_surat', count(nomor_surat), count(*) FROM surat_dari_luar_bangda
            UNION ALL SELECT 'tgl_surat', count(tgl_surat), count(*) FROM surat_dari_luar_bangda
            UNION ALL SELECT 'tgl_diterima_ula', count(tgl_diterima_ula), count(*) FROM surat_dari_luar_bangda
            UNION ALL SELECT 'perihal', count(perihal), count(*) FROM surat_dari_luar_bangda
            UNION ALL SELECT 'arahan_menteri', count(arahan_menteri), count(*) FROM surat_dari_luar_bangda
            UNION ALL SELECT 'arahan_sekjen', count(arahan_sekjen), count(*) FROM surat_dari_luar_bangda
            UNION ALL SELECT 'agenda_ula', count(agenda_ula), count(*) FROM surat_dari_luar_bangda
            UNION ALL SELECT 'status_mailmerge', count(status_mailmerge), count(*) FROM surat_dari_luar_bangda;
        """)
        for row in cur.fetchall():
            col, non_null, total = row
            null_pct = ((total - non_null) / total * 100) if total > 0 else 0
            print(f"  {col:20s}: non_null={non_null:4d}/{total:4d}  NULL={null_pct:.1f}%")

        print()
        print("=" * 80)
        print("ANALISIS 2: KORELASI ANTAR TABEL")
        print("=" * 80)
        
        # FK coverage
        cur.execute("""
            SELECT 
                'surat_dari_luar_bangda' as tbl, count(*) as rows,
                (SELECT count(DISTINCT unique_id) FROM lembar_disposisi_bangda) as linked_ld,
                (SELECT count(DISTINCT unique_id) FROM disposisi_distributions) as linked_dd
            FROM surat_dari_luar_bangda;
        """)
        for row in cur.fetchall():
            print(f"  Main: {row[0]} ({row[1]} rows)")
            print(f"  Linked to lembar_disposisi: {row[2]} unique_ids")
            print(f"  Linked to disposisi_distributions: {row[3]} unique_ids")

        # Cross-tab analysis
        print()
        print("FK NULL check (disposisi tables tanpa surat_keluar_id):")
        cur.execute("SELECT count(*) FROM lembar_disposisi_bangda WHERE surat_keluar_id IS NULL")
        print(f"  lembar_disposisi tanpa FK: {cur.fetchone()[0]}")
        cur.execute("SELECT count(*) FROM disposisi_distributions WHERE surat_keluar_id IS NULL")
        print(f"  disposisi_distributions tanpa FK: {cur.fetchone()[0]}")

        print()
        print("=" * 80)
        print("ANALISIS 3: SAMPLE DATA (periksa overlap kolom)")
        print("=" * 80)
        
        cur.execute("""
            SELECT agenda_ula, nomor_surat, surat_dari
            FROM surat_dari_luar_bangda 
            LIMIT 3
        """)
        print("surat_dari_luar_bangda sample:")
        for row in cur.fetchall():
            print(f"  agenda={row[0]}, no={row[1]}, dari={row[2]}")

        cur.execute("""
            SELECT nomor_disposisi, dari_disposisi, perihal_disposisi
            FROM lembar_disposisi_bangda 
            LIMIT 3
        """)
        print("lembar_disposisi_bangda sample:")
        for row in cur.fetchall():
            print(f"  dispo_no={row[0]}, dari={row[1]}, perihal={row[2]}")

        cur.execute("""
            SELECT source_tab, nomor_disposisi, kepada, isi_disposisi
            FROM disposisi_distributions 
            LIMIT 3
        """)
        print("disposisi_distributions sample:")
        for row in cur.fetchall():
            print(f"  tab={row[0]}, dispo_no={row[1]}, kepada={row[2]}")

        print()
        print("=" * 80)
        print("PROPOSAL SIMPLIFIKASI SKEMA")
        print("=" * 80)
        print("""
REKOMENDASI:

1. SATUKAN lembar_disposisi_bangda → surat_dari_luar_bangda
   Alasan: 1:1 relationship (501 vs 507 hampir sama)
   Kolom yang dipindah: nomor_disposisi, tanggal_disposisi, dari_disposisi, perihal_disposisi
   
2. SATUKAN disposisi_distributions → jadi 1 tabel unified_disposisi
   Alasan: Dispo DJ/TU Pim (332) + Dispo Ses (202) = 534
   Keduanya punya struktur sama (nomor, tanggal, dari, kepada, isi)
   
3. SIMPLIFIKASI KOLOM DI surat_dari_luar_bangda:
   HAPUS (low-value / rarely used):
   - timestamp_raw        → hanya metadata ETL
   - source_sheet         → selalu 'Surat Masuk'
   - source_row           → hanya untuk debugging
   - unique_id            → bisa digenerate ulang dari id
   
   SIMPLIFY:
   - arahan_menteri + arahan_sekjen → gabung jadi 'arahan' (text)
   
4. FINAL TARGET SCHEMA (2 tabel saja):

   TABLE: bangda_surat
   - id BIGSERIAL PK
   - surat_dari TEXT           -- Pengirim
   - nomor_surat TEXT           -- Nomor surat
   - tgl_surat DATE             -- Tanggal surat
   - tgl_diterima DATE          -- Tanggal diterima ULA
   - perihal TEXT               -- Isi perihal
   - arahan TEXT                -- Gabungan arahan menteri + sekjen
   - agenda TEXT                -- Nomor agenda (was agenda_ula)
   - status TEXT                -- Status mailmerge
   
   -- Gabung dari lembar_disposisi (1:1)
   - dispo_nomor TEXT           -- From lembar_disposisi
   - dispo_tanggal DATE
   - dispo_perihal TEXT
   
   -- Metadata
   - created_at TIMESTAMPTZ
   - updated_at TIMESTAMPTZ

   TABLE: bangda_disposisi
   - id BIGSERIAL PK
   - surat_id BIGINT FK → bangda_surat
   - source_tab TEXT        -- 'Dispo DJ/TU Pim' | 'Dispo Ses'
   - nomor TEXT
   - tanggal DATE
   - dari TEXT
   - kepada TEXT
   - isi TEXT
   - batas_waktu DATE
   - created_at, updated_at
""")