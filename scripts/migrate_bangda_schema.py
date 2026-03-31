#!/usr/bin/env python3
"""
Migration: Simplifikasi Skema Bangda
=====================================
1. Tambah kolom `arahan` (gabungan menteri + sekjen)
2. Fix FK linking via agenda_ula ↔ nomor_disposição
3. Tambah kolom dispo ke surat_dari_luar_bangda (dari lembar_disposisi)
4. Fix Dispo Ses ETL - extract proper columns

Jalankan:
  python3 scripts/migrate_bangda_schema.py
"""
import os
import sys
import psycopg

PROJECT_ROOT = "/home/aseps/MCP/mcp-unified"
sys.path.insert(0, PROJECT_ROOT)
from core.secrets import load_runtime_secrets
load_runtime_secrets()

dsn = os.getenv("DATABASE_URL")
if not dsn:
    raise RuntimeError("DATABASE_URL belum diset")

with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
        print("=" * 60)
        print("MIGRATION 1: Tambah kolom `arahan` (gabungan)")
        print("=" * 60)
        
        # Add new column
        cur.execute("""
            ALTER TABLE surat_dari_luar_bangda 
            ADD COLUMN IF NOT EXISTS arahan TEXT
        """)
        conn.commit()
        
        # Merge arahan_menteri + arahan_sekjen
        cur.execute("""
            UPDATE surat_dari_luar_bangda
            SET arahan = CASE
                WHEN arahan_menteri IS NOT NULL AND arahan_menteri != ''
                     AND arahan_sekjen IS NOT NULL AND arahan_sekjen != ''
                    THEN arahan_menteri || '; ' || arahan_sekjen
                WHEN arahan_menteri IS NOT NULL AND arahan_menteri != ''
                    THEN arahan_menteri
                WHEN arahan_sekjen IS NOT NULL AND arahan_sekjen != ''
                    THEN arahan_sekjen
                ELSE NULL
            END
            WHERE arahan IS NULL OR arahan = ''
        """)
        conn.commit()
        print(f"  Updated {cur.rowcount} rows with merged arahan")

        print()
        print("=" * 60)
        print("MIGRATION 2: Fix FK linking - lembar_disposisi_bangda")
        print("=" * 60)
        
        # Link via agenda_ula ↔ nomor_disposisi
        cur.execute("""
            UPDATE lembar_disposisi_bangda ldb
            SET surat_keluar_id = sdlb.id
            FROM surat_dari_luar_bangda sdlb
            WHERE ldb.nomor_disposisi = sdlb.agenda_ula
              AND ldb.surat_keluar_id IS NULL
        """)
        conn.commit()
        print(f"  Linked {cur.rowcount} lembar_disposisi rows to surat")
        
        # Check remaining unlinked
        cur.execute("SELECT count(*) FROM lembar_disposisi_bangda WHERE surat_keluar_id IS NULL")
        remaining = cur.fetchone()[0]
        print(f"  Remaining unlinked: {remaining}")

        print()
        print("=" * 60)
        print("MIGRATION 3: Fix FK linking - disposisi_distributions")
        print("=" * 60)
        
        # Link via unique_id pattern matching agenda_ula
        cur.execute("""
            UPDATE disposisi_distributions dd
            SET surat_keluar_id = sdlb.id
            FROM surat_dari_luar_bangda sdlb
            WHERE dd.unique_id LIKE '%' || sdlb.agenda_ula || '%'
              AND dd.surat_keluar_id IS NULL
        """)
        conn.commit()
        print(f"  Linked {cur.rowcount} disposisi rows to surat (via unique_id pattern)")
        
        # Check remaining
        cur.execute("SELECT count(*) FROM disposisi_distributions WHERE surat_keluar_id IS NULL")
        remaining = cur.fetchone()[0]
        print(f"  Remaining unlinked: {remaining}")

        print()
        print("=" * 60)
        print("MIGRATION 4: Add dispo fields to main table (from lembar_disposisi)")
        print("=" * 60)
        
        # Add dispo columns to main table
        cur.execute("""
            ALTER TABLE surat_dari_luar_bangda 
            ADD COLUMN IF NOT EXISTS dispo_nomor TEXT,
            ADD COLUMN IF NOT EXISTS dispo_tanggal DATE,
            ADD COLUMN IF NOT EXISTS dispo_dari TEXT,
            ADD COLUMN IF NOT EXISTS dispo_perihal TEXT
        """)
        conn.commit()
        print("  Added dispo_* columns")
        
        # Populate from linked lembar_disposisi
        cur.execute("""
            UPDATE surat_dari_luar_bangda sdlb
            SET 
                dispo_nomor = ldb.nomor_disposisi,
                dispo_tanggal = ldb.tanggal_disposisi,
                dispo_dari = ldb.dari_disposisi,
                dispo_perihal = ldb.perihal_disposisi
            FROM lembar_disposisi_bangda ldb
            WHERE sdlb.id = ldb.surat_keluar_id
        """)
        conn.commit()
        print(f"  Populated dispo fields for {cur.rowcount} rows")

        print()
        print("=" * 60)
        print("FINAL STATUS")
        print("=" * 60)
        
        cur.execute("SELECT count(*) FROM surat_dari_luar_bangda")
        print(f"  surat_dari_luar_bangda: {cur.fetchone()[0]} rows")
        
        cur.execute("SELECT count(*) FROM lembar_disposisi_bangda WHERE surat_keluar_id IS NOT NULL")
        print(f"  linked lembar_disposisi: {cur.fetchone()[0]} rows")
        
        cur.execute("SELECT count(*) FROM disposisi_distributions WHERE surat_keluar_id IS NOT NULL")
        print(f"  linked disposisi_distributions: {cur.fetchone()[0]} rows")
        
        cur.execute("SELECT count(*) FROM surat_dari_luar_bangda WHERE arahan IS NOT NULL")
        print(f"  rows with merged arahan: {cur.fetchone()[0]}")
        
        cur.execute("SELECT count(*) FROM surat_dari_luar_bangda WHERE dispo_nomor IS NOT NULL")
        print(f"  rows with dispo_nomor: {cur.fetchone()[0]}")

        conn.commit()

print("\nMigration completed!")