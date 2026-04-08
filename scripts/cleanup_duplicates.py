#!/usr/bin/env python3
import os
import sys
import psycopg
from psycopg.rows import dict_row

# Tambahkan root ke path
sys.path.insert(0, '/home/aseps/MCP/korespondensi-server')

from src.database import get_db_connection

def cleanup_duplicates():
    print("🚀 Memulai pembersihan duplikat di surat_masuk_puu_internal...")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Cari NOMOR_ND yang muncul lebih dari sekali
            cur.execute("""
                SELECT nomor_nd, count(*) as cnt 
                FROM surat_masuk_puu_internal 
                GROUP BY nomor_nd 
                HAVING count(*) > 1
            """)
            duplicates = cur.fetchall()
            print(f"🔍 Ditemukan {len(duplicates)} nomor ND yang terduplikasi.")
            
            for dup in duplicates:
                nd = dup['nomor_nd']
                # Ambil semua record untuk ND ini
                cur.execute("""
                    SELECT id, unique_id, agenda_puu, pic_name, drive_file_url 
                    FROM surat_masuk_puu_internal 
                    WHERE nomor_nd = %s
                    ORDER BY id DESC
                """, [nd])
                rows = cur.fetchall()
                
                # Identifikasi "Master" (biasanya yang ID-nya baru bukan format INT-)
                master = None
                others = []
                
                for r in rows:
                    if not r['unique_id'].startswith('INT-'):
                        master = r
                    else:
                        others.append(r)
                
                # Jika tidak ada master dengan format baru, ambil yang ID paling besar
                if not master:
                    master = rows[0]
                    others = rows[1:]
                
                print(f"  - Memproses ND: {nd} (Master ID: {master['id']})")
                
                # Migrasi data penting dari 'others' ke 'master' jika master kosong
                updates = {}
                for other in others:
                    if other['agenda_puu'] and (not master['agenda_puu'] or master['agenda_puu'] == 'N/A'):
                        master['agenda_puu'] = other['agenda_puu']
                        updates['agenda_puu'] = other['agenda_puu']
                    if other['pic_name'] and not master['pic_name']:
                        master['pic_name'] = other['pic_name']
                        updates['pic_name'] = other['pic_name']
                    if other['drive_file_url'] and not master['drive_file_url']:
                        master['drive_file_url'] = other['drive_file_url']
                        updates['drive_file_url'] = other['drive_file_url']
                
                if updates:
                    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
                    cur.execute(f"UPDATE surat_masuk_puu_internal SET {set_clause} WHERE id = %s", 
                                list(updates.values()) + [master['id']])
                
                # Hapus yang duplikat
                other_ids = [o['id'] for o in others]
                if other_ids:
                    cur.execute("DELETE FROM surat_masuk_puu_internal WHERE id = ANY(%s)", [other_ids])
                    print(f"    ✅ Menghapus {len(other_ids)} entri duplikat.")
            
            conn.commit()
    print("✨ Pembersihan selesai.")

if __name__ == "__main__":
    cleanup_duplicates()
