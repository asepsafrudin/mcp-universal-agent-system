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
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%m/%d/%Y"):
            try:
                dt = datetime.strptime(clean, fmt)
                if dt.year < 100:
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

                    # ── Statistik bulan berjalan ───────────────────────────
                    cur.execute(
                        "SELECT COUNT(*) FROM surat_masuk_puu "
                        "WHERE EXTRACT(MONTH FROM tanggal_diterima_puu)=%s "
                        "AND EXTRACT(YEAR FROM tanggal_diterima_puu)=%s",
                        (today.month, today.year)
                    )
                    masuk_bulan = cur.fetchone()[0]

                    cur.execute(
                        "SELECT COUNT(*) FROM surat_keluar_puu "
                        "WHERE EXTRACT(MONTH FROM tanggal_surat)=%s "
                        "AND EXTRACT(YEAR FROM tanggal_surat)=%s",
                        (today.month, today.year)
                    )
                    keluar_bulan = cur.fetchone()[0]

                    cur.execute(
                        "SELECT COUNT(*) FROM surat_untuk_substansi_puu "
                        "WHERE EXTRACT(MONTH FROM tanggal_diterima)=%s "
                        "AND EXTRACT(YEAR FROM tanggal_diterima)=%s",
                        (today.month, today.year)
                    )
                    substansi_bulan = cur.fetchone()[0]

                    report += (
                        f"📥 Masuk PUU: *{masuk_bulan}* | "
                        f"📤 Keluar: *{keluar_bulan}* | "
                        f"📋 Substansi: *{substansi_bulan}* _(bulan ini)_\n\n"
                    )

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

                    report += f"📨 *Surat Masuk PUU* ({len(rows_masuk)} surat)\n"
                    report += "─────────────────────────\n"
                    if not rows_masuk:
                        report += "_Tidak ada surat masuk dalam 5 hari terakhir_\n\n"
                    else:
                        for row in rows_masuk:
                            no, dari_full, dari, tgl_surat, tgl_terima, hal, posisi = row
                            pengirim = dari_full or dari or '-'
                            report += f"• `{no or '-'}`\n"
                            report += f"  👤 {pengirim}\n"
                            report += f"  📅 Diterima: *{fmt_date(tgl_terima)}*"
                            if tgl_terima and tgl_surat and tgl_terima != tgl_surat:
                                report += f" _(surat: {fmt_date(tgl_surat)})_"
                            report += "\n"
                            report += f"  📄 {indent_hal(str(hal or '-')[:120])}\n"
                            if posisi:
                                report += f"  📍 `{posisi}`\n"
                            report += "\n"

                    # ══ SEKSI 2: Surat Keluar PUU (5 hari terakhir) ═══════
                    cur.execute("""
                        SELECT nomor_nd, dari, tanggal_surat, hal, tujuan
                        FROM surat_keluar_puu
                        WHERE tanggal_surat >= %s
                        ORDER BY tanggal_surat DESC
                    """, (cutoff,))
                    rows_keluar = cur.fetchall()

                    report += f"📤 *Surat Keluar PUU* ({len(rows_keluar)} surat)\n"
                    report += "─────────────────────────\n"
                    if not rows_keluar:
                        report += "_Tidak ada surat keluar dalam 5 hari terakhir_\n\n"
                    else:
                        for row in rows_keluar:
                            no, dari, tgl, hal, tujuan = row
                            report += f"• `{no or '-'}` | *{fmt_date(tgl)}*\n"
                            if tujuan:
                                report += f"  → {str(tujuan)[:70]}\n"
                            report += f"  📄 {indent_hal(str(hal or '-')[:110])}\n\n"

                    # ══ SEKSI 3: Surat untuk Substansi PUU (5 hari terakhir) ══
                    cur.execute(
                        "SELECT COUNT(*) FROM surat_untuk_substansi_puu WHERE tanggal_diterima >= %s",
                        (cutoff,)
                    )
                    total_substansi_5hari = cur.fetchone()[0]

                    cur.execute("""
                        SELECT sp.nomor_surat, sp.surat_dari, sp.tanggal_disposisi,
                               sp.tanggal_diterima, sp.isi_disposisi,
                               sp.status, sl.perihal
                        FROM surat_untuk_substansi_puu sp
                        LEFT JOIN surat_dari_luar_bangda sl ON sl.id = sp.surat_id
                        WHERE sp.tanggal_diterima >= %s
                        ORDER BY sp.tanggal_diterima DESC, sp.tanggal_disposisi DESC
                        LIMIT 10
                    """, (cutoff,))
                    rows_substansi = cur.fetchall()

                    report += f"📋 *Surat untuk Substansi PUU* ({total_substansi_5hari} surat, tampil 10 terbaru)\n"
                    report += "─────────────────────────\n"
                    if not rows_substansi:
                        report += "_Tidak ada surat substansi dalam 5 hari terakhir_\n"
                    else:
                        status_icon = {"pending": "⏳", "selesai": "✅", "proses": "🔄"}
                        for row in rows_substansi:
                            no, sdr, tgl_dispo, tgl_terima, isi_dispo, status, perihal = row
                            icon = status_icon.get(str(status or '').lower(), "📝")
                            report += f"• `{no or '-'}`\n"
                            report += f"  👤 {sdr or '-'}\n"
                            report += f"  📅 Diterima: *{fmt_date(tgl_terima)}*"
                            if tgl_dispo and tgl_terima and tgl_dispo != tgl_terima:
                                report += f" _(dispo: {fmt_date(tgl_dispo)})_"
                            report += "\n"
                            if perihal:
                                report += f"  📄 {indent_hal(str(perihal)[:110])}\n"
                            if isi_dispo:
                                clean_dispo = str(isi_dispo).replace('\n', ' ')[:90]
                                report += f"  📌 _{clean_dispo}_\n"
                            report += f"  {icon} Status: `{status or '-'}`\n"
                            report += "\n"
                        if total_substansi_5hari > 10:
                            report += f"_...dan {total_substansi_5hari - 10} surat lainnya. Gunakan /cari untuk pencarian spesifik._\n"

        except Exception as e:
            report += f"⚠️ Error memuat data: `{str(e)}`\n"

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
        output += "\n"
    return output

if __name__ == "__main__":
    db = CorrespondenceDashboard()
    print(db.get_recent_summary())