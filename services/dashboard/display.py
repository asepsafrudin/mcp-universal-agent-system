"""
Correspondence Dashboard Service - PostgreSQL Edition.
Migrated from JSON cache to PostgreSQL tables.
"""
import os
import sys
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional

PROJECT_ROOT = "/home/aseps/MCP/mcp-unified"
sys.path.insert(0, PROJECT_ROOT)

from observability.logger import logger
from integrations.korespondensi.utils import parse_posisi_timeline, translate_disposisi

def get_db_conn():
    return psycopg.connect(os.getenv("DATABASE_URL", "postgresql://mcp_user@localhost:5433/mcp_knowledge"))

def parse_indonesian_date(date_str: str) -> datetime:
    if not date_str or str(date_str).strip().lower() in ('', 'null'):
        return datetime.min
    try:
        val = str(date_str).strip().upper()
        months = [
            ('JANUARI', '1'), ('FEBRUARI', '2'), ('MARET', '3'), ('APRIL', '4'),
            ('MEI', '5'), ('JUNI', '6'), ('JULI', '7'), ('AGUSTUS', '8'),
            ('SEPTEMBER', '9'), ('OKTOBER', '10'), ('NOVEMBER', '11'), ('DESEMBER', '12'),
            ('JAN', '1'), ('FEB', '2'), ('MAR', '3'), ('APR', '4'), ('MAY', '5'),
            ('JUN', '6'), ('JUL', '7'), ('AGU', '8'), ('SEP', '9'), ('OKT', '10'),
            ('NOV', '11'), ('DES', '12'), ('SEPT', '9'), ('NOP', '11'),
        ]
        for m_name, m_num in months:
            if m_name in val:
                val = val.replace(m_name, m_num)
                break
        clean = re.sub(r'[^\d]', '/', val.strip())
        clean = re.sub(r'/+', '/', clean).strip('/')
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%m/%d/%Y", "%d/%m"):
            try:
                dt = datetime.strptime(clean, fmt)
                if fmt == "%d/%m":
                    dt = dt.replace(year=datetime.now().year)
                elif dt.year < 100:
                    dt = dt.replace(year=dt.year + 2000)
                return dt
            except ValueError:
                continue
    except Exception:
        pass
    return datetime.min

def indent_hal(text: str, indent: str = "     ") -> str:
    if not text: return "-"
    lines = [l.strip() for l in str(text).splitlines() if l.strip()]
    return ("\n" + indent).join(lines)

STORAGE_DIR = "/home/aseps/MCP/storage/admin_data/korespondensi"
SYNC_CONFIG = os.path.join(PROJECT_ROOT, "knowledge/sync_targets.json")
SYNC_STATE = os.path.join(STORAGE_DIR, "sync_state.json")
import psycopg

class CorrespondenceDashboard:
    def __init__(self):
        self.targets = self._load_targets()

    def _load_targets(self) -> List[Dict]:
        if os.path.exists(SYNC_CONFIG):
            with open(SYNC_CONFIG, 'r') as f:
                return json.load(f)
        return []

    def get_sync_status(self) -> Dict[str, Any]:
        state = {}
        if os.path.exists(SYNC_STATE):
            with open(SYNC_STATE, 'r') as f:
                state = json.load(f)
        status_report = []
        for target in self.targets:
            ns = target['namespace']
            ns_state = state.get(ns, {})
            status_report.append({
                "name": target['name'], "namespace": ns,
                "last_sync": ns_state.get('last_sync', 'Never'),
                "spreadsheet_id": target['spreadsheet_id']
            })
        return status_report

    def get_recent_summary(self, days: int = 5) -> str:
        from datetime import date, timedelta
        today = date.today()
        cutoff = today - timedelta(days=days - 1)   # inklusif hari ini
        bulan_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'Mei',6:'Jun',
                       7:'Jul',8:'Agu',9:'Sep',10:'Okt',11:'Nov',12:'Des'}

        def fmt_date(d):
            """Format date object/string ke DD Mon."""
            if not d: return '?'
            if isinstance(d, str):
                try: d = datetime.strptime(d, '%Y-%m-%d').date()
                except: return str(d)
            return f"{d.day} {bulan_names.get(d.month, str(d.month))}"

        report = "📊 *DASHBOARD KORESPONDENSI PUU*\n"
        report += f"_5 Hari Terakhir: {fmt_date(cutoff)} – {fmt_date(today)} {today.year}_\n\n"

        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:

                    # ── Statistik Anomali & Personnel ────────────────────────
                    cur.execute("SELECT COUNT(*) FROM surat_masuk_puu_internal WHERE (no_agenda_dispo IS NULL OR TRIM(no_agenda_dispo) = '')")
                    res_anomali = cur.fetchone()
                    anomali_count = res_anomali[0] if res_anomali else 0

                    cur.execute("""
                        SELECT pic_name, COUNT(*) as count 
                        FROM surat_masuk_puu_internal 
                        WHERE pic_name IS NOT NULL AND pic_name != ''
                        GROUP BY pic_name ORDER BY count DESC LIMIT 5
                    """)
                    personnel_rows = cur.fetchall()
                    personnel_report = " | ".join([f"{r[0]}: *{r[1]}*" for r in personnel_rows]) if personnel_rows else "-"

                    # ── Statistik bulan berjalan ─────────────────────────
                    cur.execute(
                        "SELECT COUNT(*) FROM surat_masuk_puu_internal "
                        "WHERE EXTRACT(MONTH FROM tanggal_diterima_puu)=%s "
                        "AND EXTRACT(YEAR FROM tanggal_diterima_puu)=%s",
                        (today.month, today.year)
                    )
                    res_masuk = cur.fetchone()
                    masuk_bulan = res_masuk[0] if res_masuk else 0

                    cur.execute(
                        "SELECT COUNT(*) FROM surat_keluar_puu "
                        "WHERE EXTRACT(MONTH FROM tanggal_surat)=%s "
                        "AND EXTRACT(YEAR FROM tanggal_surat)=%s",
                        (today.month, today.year)
                    )
                    res_keluar = cur.fetchone()
                    keluar_bulan = res_keluar[0] if res_keluar else 0

                    cur.execute(
                        "SELECT COUNT(*) FROM surat_untuk_substansi_puu "
                        "WHERE EXTRACT(MONTH FROM tanggal_diterima)=%s "
                        "AND EXTRACT(YEAR FROM tanggal_diterima)=%s",
                        (today.month, today.year)
                    )
                    res_substansi = cur.fetchone()
                    substansi_bulan = res_substansi[0] if res_substansi else 0

                    report += (
                        f"📁 *Statistik Bulan Ini*\n"
                        f"├ 📥 Masuk: *{masuk_bulan}*\n"
                        f"├ 📤 Keluar: *{keluar_bulan}*\n"
                        f"└ 📊 Total Surat: *{masuk_bulan + keluar_bulan}*\n\n"
                    )
                    
                    if anomali_count > 0:
                        cur.execute("""
                            SELECT nomor_nd, hal 
                            FROM surat_masuk_puu_internal 
                            WHERE (no_agenda_dispo IS NULL OR TRIM(no_agenda_dispo) = '')
                            LIMIT 5
                        """)
                        anomali_rows = cur.fetchall()
                        report += f"⚠️ *DATA ANOMALI ({anomali_count})*\n"
                        for ar in anomali_rows:
                            report += f"• `{ar[0] or '-'}` | _{str(ar[1])[:70]}..._\n"
                        report += "\n"
                    else:
                        report += "✅ *Tidak ada anomali*\n\n"

                    # ══ SEKSI 1: Surat Masuk PUU (5 hari terakhir) ════════
                    cur.execute("""
                        SELECT s.nomor_nd, s.dari_full, s.dari,
                               s.tanggal_surat, s.tanggal_diterima_puu,
                               s.hal, rp.posisi
                        FROM surat_masuk_puu s
                        LEFT JOIN korespondensi_raw_pool rp ON rp.id = s.raw_pool_id
                        WHERE s.tanggal_diterima_puu >= %s
                        ORDER BY s.tanggal_diterima_puu DESC, s.tanggal_surat DESC
                    """, (cutoff,))
                    rows_masuk = cur.fetchall()

                    report += f"📨 *SURAT MASUK PUU* ({len(rows_masuk)})\n"
                    report += "─────────────────────\n"
                    if not rows_masuk:
                        report += "_Tidak ada surat masuk_\n\n"
                    else:
                        for row in rows_masuk:
                            no, dari_full, dari, tgl_surat, tgl_terima, hal, posisi = row
                            pengirim = dari_full or dari or '-'
                            report += f"🔹 `{no or '-'}`\n"
                            report += f"   👤 *{pengirim}*\n"
                            report += f"   🗓️ {fmt_date(tgl_terima)} | 📄 {str(hal or '-')[:90]}...\n"
                            if posisi:
                                report += f"   📍 `{posisi}`\n"
                            report += "\n"

                    def summarize_posisi(pos_str: str) -> str:
                        if not pos_str: return "-"
                        parts = [p.strip() for p in pos_str.replace(";", " ").split() if p.strip()]
                        if len(parts) <= 4: return pos_str
                        # Ambil 2 step terakhir (biasanya Unit + Tanggal)
                        return "... " + " ".join(parts[-4:])

                    # ══ SEKSI 2: Surat Keluar PUU (Top 5 Terbaru berdasar Nomor) ═════════
                    # Ambil 10 data terbaru berdasar angka di nomor surat (misal 053/PUU)
                    cur.execute("""
                        SELECT s.nomor_nd, s.dari, s.tanggal_surat, s.hal, s.tujuan, rp.posisi
                        FROM surat_keluar_puu s
                        LEFT JOIN korespondensi_raw_pool rp ON rp.id = s.raw_pool_id
                        ORDER BY 
                            NULLIF(regexp_replace(s.nomor_nd, '^.*/([0-9]+)/.*$', '\\1'), s.nomor_nd)::integer DESC NULLS LAST,
                            s.updated_at DESC
                        LIMIT 10
                    """)
                    rows_potential = cur.fetchall()
                    
                    from integrations.korespondensi.utils import parse_posisi
                    
                    rows_keluar = []
                    rows_macet = [] # Posisi terakhir KOREKSI
                    
                    for row in rows_potential:
                        no, dari, tgl_surat, hal, tujuan, posisi_raw = row
                        parsed_pos = parse_posisi(posisi_raw or "")
                        pos_date_str = parsed_pos.get("last_date")
                        
                        acuan_dt = None
                        if pos_date_str:
                            acuan_dt = parse_indonesian_date(pos_date_str)
                        if not acuan_dt or acuan_dt == datetime.min:
                            if tgl_surat:
                                acuan_dt = datetime.combine(tgl_surat, datetime.min.time())
                        
                        # Data surat
                        letter_data = {
                            "no": no, "dari": dari, "hal": hal, 
                            "tgl_display": acuan_dt.date() if acuan_dt else tgl_surat, 
                            "posisi": posisi_raw,
                            "days_stuck": (today - acuan_dt.date()).days if acuan_dt else 0
                        }
                        
                        # Check if "KOREKSI" is the latest relevant action
                        parsed_timeline = parsed_pos.get("timeline", [])
                        relevant_events = [ev for ev in parsed_timeline if ev.get("action") not in ["UPDATE", "POSITION_CHECK"]]
                        last_rel_action = str(relevant_events[-1].get("action", "")).upper() if relevant_events else ""
                        
                        is_macet = "KOREKSI" in last_rel_action and not parsed_pos.get("is_done")
                        
                        if is_macet:
                            if len(rows_macet) < 5: rows_macet.append(letter_data)
                        else:
                            if len(rows_keluar) < 5: rows_keluar.append(letter_data)

                    # Tampilkan Surat Macet duluan (urut dari yang paling lama macet)
                    if rows_macet:
                        # Sort by days_stuck DESC
                        rows_macet.sort(key=lambda x: x['days_stuck'], reverse=True)
                        
                        report += f"🛑 *SURAT DALAM TAHAP KOREKSI* ({len(rows_macet)})\n"
                        report += "─────────────────────\n"
                        for item in rows_macet:
                            days = item['days_stuck']
                            if days <= 1:
                                label = f"🟡 *Menunggu Koreksi* ({days} hari)"
                                icon = "▫️"
                            elif days <= 4:
                                label = f"🟠 *Perlu Perhatian* ({days} hari)"
                                icon = "🚩"
                            else:
                                label = f"🔴 *TERTAHAN LAMA* ({days} hari)"
                                icon = "🚨"

                            report += f"{icon} `{item['no'] or '-'}`\n"
                            report += f"   {label} | 🗓️ {fmt_date(item['tgl_display'])}\n"
                            report += f"   📄 _{str(item['hal'] or '-')[:85]}..._\n"
                            report += f"   📍 {summarize_posisi(item['posisi'])}\n\n"
                        report += "\n"

                    report += f"📤 *SURAT KELUAR PUU* ({len(rows_keluar)})\n"
                    report += "─────────────────────\n"
                    if not rows_keluar and not rows_macet:
                        report += "_Tidak ada aktivitas surat keluar_\n\n"
                    else:
                        for item in rows_keluar:
                            report += f"🔸 `{item['no'] or '-'}`\n"
                            report += f"   🗓️ {fmt_date(item['tgl_display'])} | 📄 _{str(item['hal'] or '-')[:85]}..._\n"
                            if item['posisi']:
                                report += f"   📍 {summarize_posisi(item['posisi'])}\n"
                            report += "\n"


        except Exception as e:
            report += f"⚠️ Error memuat data: `{str(e)}`\n"

        # ── SEKSI SYNC STATUS ─────────────────────────
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT status, started_at FROM correspondence_sync_runs ORDER BY started_at DESC LIMIT 1")
                    last_sync = cur.fetchone()
                    if last_sync:
                        status_ic = "🟢" if last_sync[0] == 'success' else "🔴"
                        report += f"\n🔄 *Last Sync Status:* {status_ic} `{last_sync[0]}` ({fmt_date(last_sync[1].date())})\n"
        except:
            pass

        return report

    def get_puu_production(self, limit: int = 10, year: int = 2026) -> str:
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT nomor_nd, dari, tanggal_surat::text, hal
                        FROM surat_keluar_puu
                        WHERE EXTRACT(YEAR FROM tanggal_surat) = %s
                        ORDER BY tanggal_surat DESC LIMIT %s
                    """, (year, limit))
                    rows = cur.fetchall()
            report = f"📤 *SURAT KELUAR PUU — {year}*\n"
            report += f"Total: *{len(rows)} surat*\n\n"
            for row in rows:
                no, dari, tgl, hal = row
                report += f"• [{tgl or '?'}] {no or '-'}\n  {dari or '-'}\n"
                report += f"  📤 {indent_hal(hal[:100] if hal else '-')}\n\n"
            return report
        except Exception as e:
            return f"⚠️ Error: {str(e)}"

    def count_letters_by_period(self, bulan: Optional[int] = None, tahun: int = 2026, tipe: str = "masuk") -> Dict[str, Any]:
        bulan_names = {1:'Januari',2:'Februari',3:'Maret',4:'April',5:'Mei',6:'Juni',
                       7:'Juli',8:'Agustus',9:'September',10:'Oktober',11:'November',12:'Desember'}
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    if tipe in ["keluar", "internal"]:
                        if bulan is not None:
                            cur.execute("""
                                SELECT nomor_nd, dari, tanggal_surat, hal FROM surat_keluar_puu
                                WHERE EXTRACT(YEAR FROM tanggal_surat) = %s::integer
                                AND EXTRACT(MONTH FROM tanggal_surat) = %s::integer
                                ORDER BY tanggal_surat DESC
                            """, (tahun, bulan))
                        else:
                            cur.execute("""
                                SELECT nomor_nd, dari, tanggal_surat, hal FROM surat_keluar_puu
                                WHERE EXTRACT(YEAR FROM tanggal_surat) = %s::integer
                                ORDER BY tanggal_surat DESC
                            """, (tahun,))
                    else:
                        if bulan is not None:
                            cur.execute("""
                                SELECT s.nomor_nd, s.dari, s.tanggal_surat, s.hal FROM surat_masuk_puu s
                                WHERE EXTRACT(YEAR FROM s.tanggal_surat) = %s::integer
                                AND EXTRACT(MONTH FROM s.tanggal_surat) = %s::integer
                                ORDER BY s.tanggal_surat DESC
                            """, (tahun, bulan))
                        else:
                            cur.execute("""
                                SELECT s.nomor_nd, s.dari, s.tanggal_surat, s.hal FROM surat_masuk_puu s
                                WHERE EXTRACT(YEAR FROM s.tanggal_surat) = %s::integer
                                ORDER BY s.tanggal_surat DESC
                            """, (tahun,))
                    rows = cur.fetchall()
            bulan_label = bulan_names.get(bulan, "semua bulan") if bulan else "semua bulan"
            return {
                "total": len(rows), "tipe": tipe, "bulan": bulan_label, "tahun": tahun,
                "detail": [{"nomor_nd": r[0] or "-", "dari": r[1] or "-", "tanggal": r[2].isoformat() if r[2] else "", "perihal": (r[3] or "-")[:150]} for r in rows]
            }
        except Exception as e:
            return {"total": 0, "error": str(e), "tipe": tipe}

    def search_letters(self, query: str, namespace: Optional[str] = None) -> List[Dict]:
        if not query: return []
        q = query.lower().strip()
        results = []
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 'masuk' as tipe, s.nomor_nd, s.dari, s.dari_full, s.hal, s.tanggal_surat::text,
                               rp.posisi, rp.disposisi, 'PUU' as direktorat
                        FROM surat_masuk_puu s
                        LEFT JOIN korespondensi_raw_pool rp ON rp.id = s.raw_pool_id
                        WHERE s.nomor_nd ILIKE %s OR s.hal ILIKE %s OR s.dari ILIKE %s OR s.dari_full ILIKE %s
                        UNION ALL
                        SELECT 'keluar' as tipe, nomor_nd, dari, NULL, hal, tanggal_surat::text,
                               NULL, NULL, 'PUU' as direktorat
                        FROM surat_keluar_puu
                        WHERE nomor_nd ILIKE %s OR hal ILIKE %s OR dari ILIKE %s
                        ORDER BY tanggal_surat DESC LIMIT 25
                    """, tuple([f'%{q}%'] * 7))
                    for row in cur.fetchall():
                        results.append({
                            "direktorat": row[8] or "PUU", "tipe": row[0],
                            "nomor_nd": row[1], "dari": row[2], "hal": row[4],
                            "posisi": row[6], "disposisi": row[7]
                        })
        except Exception as e:
            logger.error(f"search_letters error: {e}")
        return results

    def search_by_position(self, query: str) -> List[Dict]:
        q = query.lower().strip()
        results = []
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT s.nomor_nd, s.dari, s.dari_full, s.hal, s.tanggal_surat::text, rp.posisi, rp.disposisi
                        FROM surat_masuk_puu s
                        JOIN korespondensi_raw_pool rp ON rp.id = s.raw_pool_id
                        WHERE rp.posisi ILIKE %s OR rp.disposisi ILIKE %s OR s.dari ILIKE %s
                        ORDER BY s.tanggal_surat DESC LIMIT 25
                    """, tuple([f'%{q}%'] * 3))
                    for row in cur.fetchall():
                        pos_raw = row[5] or ""
                        timeline = parse_posisi_timeline(pos_raw, sender=row[1] or "")
                        results.append({
                            "direktorat": "PUU", "nomor_nd": row[0], "dari": row[2] or row[1],
                            "hal": row[3], "tanggal": row[4], "posisi": pos_raw,
                            "disposisi": row[6], "has_code": bool(timeline)
                        })
        except Exception as e:
            logger.error(f"search_by_position error: {e}")
        return results

    def _search_internal_by_day_month(self, day: int, month: int) -> List[Dict]:
        results = []
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT s.nomor_nd, s.dari, s.dari_full, s.hal, s.tanggal_surat::text, rp.posisi, rp.disposisi
                        FROM surat_masuk_puu s
                        JOIN korespondensi_raw_pool rp ON rp.id = s.raw_pool_id
                        WHERE EXTRACT(DAY FROM s.tanggal_surat) = %s
                          AND EXTRACT(MONTH FROM s.tanggal_surat) = %s
                        ORDER BY s.tanggal_surat DESC
                    """, (day, month))
                    for row in cur.fetchall():
                        results.append({
                            "direktorat": "PUU", "nomor_nd": row[0], "dari": row[2] or row[1],
                            "hal": row[3], "tanggal": row[4], "posisi": row[5] or "",
                            "disposisi": row[6], "has_code": True
                        })
        except Exception as e:
            logger.error(f"_search_internal_by_day_month error: {e}")
        return results

    def get_anomalies_report(self, limit: int = 10) -> str:
        """List letters with missing metadata (anomalies)."""
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT unique_id, nomor_nd, dari, hal, tanggal_surat 
                        FROM surat_masuk_puu_internal 
                        WHERE (no_agenda_dispo IS NULL OR TRIM(no_agenda_dispo) = '')
                        ORDER BY tanggal_surat DESC LIMIT %s
                    """, (limit,))
                    rows = cur.fetchall()
            
            if not rows:
                return "✅ *Tidak ada anomali surat ditemukan.* Semua data memiliki agenda."
                
            report = "⚠️ *LAPORAN ANOMALI SURAT (Missing Agenda)*\n\n"
            for r in rows:
                tgl = r[4].strftime('%d/%m/%y') if r[4] else '?'
                report += f"• `{r[1] or '-'}` | {tgl}\n  📄 {str(r[3])[:100]}...\n\n"
            return report
        except Exception as e:
            return f"⚠️ Error: {str(e)}"

    def send_reminder(self, letter_no: str, agent_pesan: str) -> Dict[str, Any]:
        """Prepare reminder data for a letter."""
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT nomor_nd, hal, posisi, dari 
                        FROM korespondensi_raw_pool 
                        WHERE nomor_nd ILIKE %s LIMIT 1
                    """, (f"%{letter_no}%",))
                    row = cur.fetchone()
            
            if not row:
                return {"success": False, "error": f"Surat '{letter_no}' tidak ditemukan."}
            
            return {
                "success": True,
                "data": {
                    "nomor_nd": row[0],
                    "hal": row[1],
                    "posisi": row[2] or "Unknown",
                    "dari": row[3],
                    "pesan": agent_pesan
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_personnel_report(self) -> str:
        """Get report of PIC workloads."""
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT pic_name, COUNT(*) as count 
                        FROM surat_masuk_puu_internal 
                        WHERE pic_name IS NOT NULL AND pic_name != ''
                        GROUP BY pic_name ORDER BY count DESC
                    """)
                    rows = cur.fetchall()
            
            if not rows:
                return "👤 *Data PIC belum tersedia atau belum ada penugasan.*"
                
            report = "👤 *BEBAN KERJA PIC (PUU)*\n"
            report += "─────────────────────────\n"
            for r in rows:
                report += f"• *{r[0]}*: `{r[1]} surat`\n"
            return report
        except Exception as e:
            return f"⚠️ Error: {str(e)}"

    def trigger_sync(self) -> bool:
        """Trigger ETL and internal sync scripts with anti-spam protection."""
        import subprocess
        import time
        
        lock_file = "/tmp/mcp_correspondence_sync.lock"
        # Check if lock exists and is recent (within 5 minutes)
        if os.path.exists(lock_file):
            try:
                mtime = os.path.getmtime(lock_file)
                if time.time() - mtime < 300: # 5 minutes cooldown
                    logger.warning("⚠️ Sinkronisasi sudah berjalan atau baru saja dipicu. Silakan tunggu beberapa menit.")
                    return False
            except Exception:
                pass
        
        # Create/Update lock
        try:
            with open(lock_file, 'w') as f:
                f.write(str(time.time()))
        except Exception as e:
            logger.warning(f"Could not create sync lock: {e}")

        etl_script = "/home/aseps/MCP/scripts/etl_korespondensi_db_centric.py"
        python_bin = "/home/aseps/MCP/.venv/bin/python3"
        
        try:
            # Run ETL in background
            subprocess.Popen(
                [python_bin, etl_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd="/home/aseps/MCP/korespondensi-server"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to trigger sync: {e}")
            if os.path.exists(lock_file):
                try: os.unlink(lock_file)
                except: pass
            return False

def format_search_results(results, query):
    if not results:
        return f"🔍 Tidak ditemukan hasil untuk: *{query}*"
    output = f"🔍 *HASIL PENCARIAN*\nInput: `{query}` ({len(results)} temuan)\n\n"
    for res in results[:10]:
        no = res.get('nomor_nd', 'N/A')
        dari = res.get('dari', 'N/A')
        hal = res.get('hal', 'N/A')
        pos = res.get('posisi', '-')
        tgl = res.get('tanggal', '?')
        badge = "📝 " if 'has_code' not in res or not res['has_code'] else "🏷️ "
        output += f"{badge}*{dari}*\n  🔢 `{no}` | 📅 `{tgl}`\n"
        output += f"📄 Hal: {indent_hal(str(hal)[:100])}\n"
        if pos and pos != '-': output += f"📍 Posisi: `{pos}`\n"
        # Decode disposisi
        dispo_raw = res.get('disposisi')
        if dispo_raw:
            info = translate_disposisi(dispo_raw, sender=dari)
            if info["priority"] != "NORMAL": output += f"🚨 *{info['priority']}*\n"
            if info["forwarded_to_list"]:
                output += f"↪️ Forwarded: {info['forwarded_from']} → {', '.join(info['forwarded_to_list'])}\n"
            output += f"📥 Arahan: _{dispo_raw}_\n"
    return output

if __name__ == "__main__":
    db = CorrespondenceDashboard()
    print(db.get_recent_summary())