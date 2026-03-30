"""
Correspondence Dashboard Service.
Provides analytical views and search capabilities across multiple directorate spreadsheets.
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

def parse_indonesian_date(date_str: str) -> datetime:
    """Helper to parse various date formats including Indonesian month names.
    
    Handles:
    - '13/03/2026', '13-03-2026'
    - '13 Mar 2026', '13 Maret 2026'
    - '8-Jan-2026', '13 Maret 2026'
    """
    if not date_str or str(date_str).strip().lower() in ('', 'null'):
        return datetime.min

    try:
        val = str(date_str).strip().upper()

        # Month name -> number map (longest first to avoid partial match like MAR in MARET)
        months = [
            ('JANUARI', '1'), ('FEBRUARI', '2'), ('MARET', '3'),
            ('APRIL', '4'), ('MEI', '5'), ('JUNI', '6'),
            ('JULI', '7'), ('AGUSTUS', '8'), ('SEPTEMBER', '9'),
            ('OKTOBER', '10'), ('NOVEMBER', '11'), ('DESEMBER', '12'),
            ('JANUARI', '1'), ('FEBRUARI', '2'), ('SEPT', '9'), ('NOP', '11'),
            ('JAN', '1'), ('FEB', '2'), ('MAR', '3'), ('APR', '4'),
            ('MAY', '5'), ('JUN', '6'), ('JUL', '7'), ('AGU', '8'),
            ('SEP', '9'), ('OKT', '10'), ('NOV', '11'), ('DES', '12'),
        ]

        # Replace month name with its number
        for m_name, m_num in months:
            if m_name in val:
                val = val.replace(m_name, m_num)
                break

        # Normalize: strip non-numeric characters to spaces, then join with /
        clean = re.sub(r'[^\d]', '/', val.strip())
        # Collapse multiple slashes
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
    """Pastikan setiap baris teks hal/perihal memiliki indentasi konsisten 5 spasi."""
    if not text:
        return "-"
    # Bersihkan whitespace berlebih dan normalisasi newline
    lines = [l.strip() for l in str(text).splitlines() if l.strip()]
    return ("\n" + indent).join(lines)

STORAGE_DIR = "/home/aseps/MCP/storage/admin_data/korespondensi"
SYNC_CONFIG = os.path.join(PROJECT_ROOT, "knowledge/sync_targets.json")
SYNC_STATE = os.path.join(STORAGE_DIR, "sync_state.json")

class CorrespondenceDashboard:
    def __init__(self):
        self.targets = self._load_targets()
    
    def _load_targets(self) -> List[Dict]:
        if os.path.exists(SYNC_CONFIG):
            with open(SYNC_CONFIG, 'r') as f:
                return json.load(f)
        return []

    def get_sync_status(self) -> Dict[str, Any]:
        """Get the last sync time and status for all targets."""
        state = {}
        if os.path.exists(SYNC_STATE):
            with open(SYNC_STATE, 'r') as f:
                state = json.load(f)
        
        status_report = []
        for target in self.targets:
            ns = target['namespace']
            ns_state = state.get(ns, {})
            last_sync = ns_state.get('last_sync', 'Never')
            
            status_report.append({
                "name": target['name'],
                "namespace": ns,
                "last_sync": last_sync,
                "spreadsheet_id": target['spreadsheet_id']
            })
        return status_report

    def get_recent_summary(self, limit_per_ns: int = 3) -> str:
        """Generate a text summary of recent PUU letters for a dashboard view."""
        report = "📊 *DASHBOARD KORESPONDENSI PUU*\n\n"
        
        # 1. POSISI PUU (Internal)
        # Prioritize new pooling data, fallback to old internal masuk if needed
        internal_ns = "korespondensi_internal_pooling"
        file_path = os.path.join(STORAGE_DIR, f"{internal_ns}_data.json")
        
        if not os.path.exists(file_path):
            internal_ns = "korespondensi_sekretariat_internal_masuk"
            file_path = os.path.join(STORAGE_DIR, f"{internal_ns}_data.json")

        report += "*📂 SURAT POSISI DI PUU (Internal)*\n"
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    values = data.get("values", [])
                    if len(values) > 1:
                        header = values[0]
                        rows = values[1:]
                        
                        # Find indices based on headers for robustness
                        idx_tgl = next((i for i, h in enumerate(header) if "TANGGAL" in str(h).upper()), 2)
                        idx_dari = next((i for i, h in enumerate(header) if "DARI" in str(h).upper()), 4)
                        idx_hal = next((i for i, h in enumerate(header) if "HAL" in str(h).upper()), 5)
                        idx_pos = next((i for i, h in enumerate(header) if "POSISI" in str(h).upper()), 6)

                        # 1. Filter rows where POSISI (Index 6 in POOLING_DATA) contains "PUU"
                        # Or DARI contains PUU AND Year is NOT 2025
                        puu_rows = []
                        for r in rows:
                            pos = str(r[idx_pos]).upper() if len(r) > idx_pos else ""
                            dari = str(r[idx_dari]).upper() if len(r) > idx_dari else ""
                            tgl_val = r[idx_tgl] if len(r) > idx_tgl else ""
                            dt = parse_indonesian_date(tgl_val)
                            
                            # Filter criteria: "PUU" mention and Year != 2025
                            if ("PUU" in pos or "PUU" in dari) and dt.year != 2025 and dt != datetime.min:
                                puu_rows.append(r)
                        
                        # Sort by TANGGAL
                        puu_rows.sort(key=lambda x: parse_indonesian_date(x[idx_tgl] if len(x) > idx_tgl else ""), reverse=True)
                        
                        latest = puu_rows[:limit_per_ns]
                        
                        if not latest:
                            report += "   _Tidak ada surat PUU dalam radar_\n"
                        for row in latest:
                            tgl = row[idx_tgl] if len(row) > idx_tgl else "?"
                            dari = row[idx_dari] if len(row) > idx_dari else "-"
                            hal = indent_hal(row[idx_hal] if len(row) > idx_hal else "-")
                            pos = row[idx_pos] if len(row) > idx_pos else "-"
                            report += f"   • [{tgl}] *{dari}*\n     📄 {hal}\n     📍 Kode: `{pos}`\n"
                    else:
                        report += "   _Data kosong_\n"
            except Exception as e:
                report += f"   ⚠️ Error loading internal data: {str(e)}\n"
        else:
            report += "   _Data tracking belum tersinkron_\n"
            
        report += "\n"
        
        # 2. MASUK/EKSTERNAL - Selalu gunakan sumber data Dispo PUU Eksternal
        dispo_ns = "korespondensi_sekretariat_dispo_puu"
        file_path = os.path.join(STORAGE_DIR, f"{dispo_ns}_data.json")

        report += "*📥 DISPOSISI SURAT (EKSTERNAL)*\n"
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    values = data.get("values", [])
                    if len(values) > 1:
                        header = values[0]
                        
                        idx_tgl = next((i for i, h in enumerate(header) if "DITERIMA PUU" in str(h).upper()), 5)
                        idx_dari = next((i for i, h in enumerate(header) if "SURAT DARI" in str(h).upper() or "DARI" in str(h).upper()), 7)
                        idx_hal = next((i for i, h in enumerate(header) if "PERIHAL" in str(h).upper() or "HAL" in str(h).upper()), 9)
                        
                        # Filter out 2025 rows and baris kosong
                        # Gunakan idx_dari (bukan hardcoded 7) untuk mengecek ketersediaan data
                        rows = []
                        for r in values[1:]:
                            val_dari = str(r[idx_dari]).strip() if len(r) > idx_dari else ""
                            if val_dari and val_dari.lower() != "null":
                                tgl_val = r[idx_tgl] if len(r) > idx_tgl else ""
                                dt = parse_indonesian_date(tgl_val)
                                if dt.year != 2025 and dt != datetime.min:
                                    rows.append(r)
                        
                        # Sort by Tgl Diterima PUU
                        rows.sort(key=lambda x: parse_indonesian_date(x[idx_tgl] if len(x) > idx_tgl else ""), reverse=True)
                        
                        latest = rows[:limit_per_ns]
                        
                        if not latest:
                            report += "   _Tidak ada disposisi terbaru_\n"
                        for row in latest:
                            tgl_rec = row[idx_tgl] if len(row) > idx_tgl else "?"
                            dari = row[idx_dari] if len(row) > idx_dari else "Instansi ?"
                            pri = indent_hal(row[idx_hal] if len(row) > idx_hal else "-")
                            report += f"   • [{tgl_rec}] *{dari}*\n     📝 {pri}\n"
                    else:
                        report += "   _Data kosong_\n"
            except Exception as e:
                report += f"   ⚠️ Error loading data: {str(e)}\n"
        else:
            report += "   _Data disposisi belum tersinkron_\n"

        report += "\n"

        # 3. PRODUKSI PUU - Surat yang diproduksi/dikirim oleh Tim PUU (DARI = PUU)
        report += "*📤 SURAT PRODUKSI PUU (Internal)*\n"
        prod_file = os.path.join(STORAGE_DIR, "korespondensi_internal_pooling_data.json")

        if os.path.exists(prod_file):
            try:
                with open(prod_file) as f:
                    data = json.load(f)
                values = data.get("values", [])
                if len(values) > 1:
                    header = values[0]
                    idx_tgl  = next((i for i,h in enumerate(header) if "TANGGAL" in str(h).upper()), 2)
                    idx_dari = next((i for i,h in enumerate(header) if "DARI"    in str(h).upper()), 4)
                    idx_hal  = next((i for i,h in enumerate(header) if "HAL"     in str(h).upper()), 5)
                    idx_pos  = next((i for i,h in enumerate(header) if "POSISI"  in str(h).upper()), 6)

                    prod_rows = []
                    for r in values[1:]:
                        val_dari = str(r[idx_dari]).strip().upper() if len(r) > idx_dari else ""
                        if "PUU" in val_dari:
                            tgl_val = r[idx_tgl] if len(r) > idx_tgl else ""
                            dt = parse_indonesian_date(tgl_val)
                            if dt.year != 2025 and dt != datetime.min:
                                prod_rows.append(r)

                    prod_rows.sort(
                        key=lambda x: parse_indonesian_date(x[idx_tgl] if len(x) > idx_tgl else ""),
                        reverse=True
                    )
                    latest = prod_rows[:limit_per_ns]

                    if not latest:
                        report += "   _Belum ada surat produksi PUU_\n"
                    for row in latest:
                        tgl = row[idx_tgl] if len(row) > idx_tgl else "?"
                        hal = indent_hal(row[idx_hal] if len(row) > idx_hal else "-")
                        pos = row[idx_pos] if len(row) > idx_pos else "-"
                        report += f"   • [{tgl}]\n     📤 {hal}\n     📍 Kode: `{pos}`\n"
                else:
                    report += "   _Data kosong_\n"
            except Exception as e:
                report += f"   ⚠️ Error: {str(e)}\n"
        else:
            report += "   _Data belum tersinkron_\n"

        return report

    def get_puu_production(self, limit: int = 10, year: int = 2026) -> str:
        """Daftar lengkap surat yang diproduksi Tim PUU untuk command /surat_keluar."""
        prod_file = os.path.join(STORAGE_DIR, "korespondensi_internal_pooling_data.json")
        report = f"📤 *SURAT PRODUKSI PUU — {year}*\n"
        report += f"_(surat yang dikirim dari Tim PUU)_\n\n"

        if not os.path.exists(prod_file):
            return report + "   _Data belum tersinkron_\n"

        try:
            with open(prod_file) as f:
                data = json.load(f)
            values = data.get("values", [])
            if len(values) <= 1:
                return report + "   _Data kosong_\n"

            header = values[0]
            idx_tgl  = next((i for i,h in enumerate(header) if "TANGGAL" in str(h).upper()), 2)
            idx_dari = next((i for i,h in enumerate(header) if "DARI"    in str(h).upper()), 4)
            idx_hal  = next((i for i,h in enumerate(header) if "HAL"     in str(h).upper()), 5)
            idx_pos  = next((i for i,h in enumerate(header) if "POSISI"  in str(h).upper()), 6)

            prod_rows = []
            for r in values[1:]:
                val_dari = str(r[idx_dari]).strip().upper() if len(r) > idx_dari else ""
                if "PUU" in val_dari:
                    tgl_val = r[idx_tgl] if len(r) > idx_tgl else ""
                    dt = parse_indonesian_date(tgl_val)
                    if dt.year == year:
                        prod_rows.append((dt, r))

            prod_rows.sort(key=lambda x: x[0], reverse=True)

            report += f"Total: *{len(prod_rows)} surat* di tahun {year}\n\n"

            for dt, row in prod_rows[:limit]:
                tgl = row[idx_tgl] if len(row) > idx_tgl else "?"
                hal = indent_hal(row[idx_hal] if len(row) > idx_hal else "-")
                pos = row[idx_pos] if len(row) > idx_pos else "-"
                report += f"   • [{tgl}]\n     📤 {hal}\n     📍 Kode: `{pos}`\n"

            if len(prod_rows) > limit:
                report += f"\n_...dan {len(prod_rows)-limit} surat lainnya._\n"
                report += "_Gunakan /surat\\_keluar <bulan> untuk filter lebih spesifik._\n"

        except Exception as e:
            report += f"⚠️ Error: {str(e)}\n"

        return report

    def count_letters_by_period(
        self,
        bulan: Optional[int] = None,
        tahun: int = 2026,
        tipe: str = "masuk"
    ) -> Dict[str, Any]:
        """
        Hitung SEMUA surat untuk periode tertentu — tanpa limit.

        Args:
            bulan: Nomor bulan 1-12. None = semua bulan.
            tahun: Tahun (default 2026)
            tipe: 'masuk'    = disposisi eksternal PUU
                  'keluar'   = surat produksi Tim PUU
                  'internal' = semua surat yang posisi di PUU (pooling internal)

        Returns:
            Dict: total, bulan, tahun, detail (list lengkap)
        """
        bulan_names = {
            1:'Januari', 2:'Februari', 3:'Maret', 4:'April', 5:'Mei', 6:'Juni',
            7:'Juli', 8:'Agustus', 9:'September', 10:'Oktober', 11:'November', 12:'Desember'
        }

        # Pilih file sumber berdasarkan tipe
        if tipe == "masuk":
            file_path = os.path.join(STORAGE_DIR, "korespondensi_sekretariat_dispo_puu_data.json")
        else:
            # keluar dan internal keduanya dari pooling
            file_path = os.path.join(STORAGE_DIR, "korespondensi_internal_pooling_data.json")

        if not os.path.exists(file_path):
            return {"total": 0, "error": "File data tidak ditemukan", "tipe": tipe}

        try:
            with open(file_path) as f:
                data = json.load(f)
            values = data.get("values", [])
            if len(values) <= 1:
                return {"total": 0, "tipe": tipe, "tahun": tahun}

            header = values[0]

            if tipe == "masuk":
                idx_tgl  = next((i for i,h in enumerate(header) if "DITERIMA PUU" in str(h).upper()), 5)
                idx_dari = next((i for i,h in enumerate(header) if "SURAT DARI"   in str(h).upper() or "DARI" in str(h).upper()), 7)
                idx_hal  = next((i for i,h in enumerate(header) if "PERIHAL"      in str(h).upper() or "HAL"  in str(h).upper()), 9)
            else:
                # keluar & internal: dari pooling
                idx_tgl  = next((i for i,h in enumerate(header) if "TANGGAL" in str(h).upper()), 2)
                idx_dari = next((i for i,h in enumerate(header) if "DARI"    in str(h).upper()), 4)
                idx_hal  = next((i for i,h in enumerate(header) if "HAL"     in str(h).upper()), 5)
                idx_pos  = next((i for i,h in enumerate(header) if "POSISI"  in str(h).upper()), 6)

            matched = []
            for row in values[1:]:
                # Validasi baris tidak kosong
                val_identitas = row[idx_dari] if len(row) > idx_dari else ""
                if not str(val_identitas).strip() or str(val_identitas).strip().lower() == "null":
                    continue

                # Filter berdasarkan tipe
                if tipe == "keluar":
                    # Hanya baris yang DARI-nya mengandung PUU
                    if "PUU" not in str(val_identitas).upper():
                        continue
                elif tipe == "internal":
                    # Hanya baris yang POSISI-nya mengandung PUU
                    val_pos = str(row[idx_pos]).upper() if len(row) > idx_pos else ""
                    if "PUU" not in val_pos:
                        continue

                tgl_val = row[idx_tgl] if len(row) > idx_tgl else ""
                dt = parse_indonesian_date(tgl_val)

                if dt == datetime.min or dt.year != tahun:
                    continue
                if bulan is not None and dt.month != bulan:
                    continue

                dari    = str(row[idx_dari]).strip() if len(row) > idx_dari else "-"
                perihal = str(row[idx_hal]).strip()  if len(row) > idx_hal  else "-"

                matched.append({
                    "tanggal": tgl_val,
                    "tanggal_parsed": dt.strftime("%d %B %Y"),
                    "dari": dari,
                    "perihal": perihal[:150],
                })

            # Urutkan terbaru ke terlama
            matched.sort(key=lambda x: parse_indonesian_date(x["tanggal"]), reverse=True)

            bulan_label = bulan_names.get(bulan, "semua bulan") if bulan else "semua bulan"

            return {
                "total": len(matched),
                "tipe": tipe,
                "bulan": bulan_label,
                "tahun": tahun,
                "detail": matched,
            }

        except Exception as e:
            return {"total": 0, "error": str(e), "tipe": tipe}

    def search_letters(self, query: str, namespace: Optional[str] = None) -> List[Dict]:
        """Search letters locally for high-speed bot interaction."""
        if not query:
            return []
            
        # 1. Clean and normalize query
        original_query = query.lower().strip()
        target_query = original_query
        
        # Remove common Indonesian prefixes that users/LLM might include
        prefixes = ["perihal ", "hal ", "cari ", "tentang ", "surat "]
        for prefix in prefixes:
            if target_query.startswith(prefix):
                target_query = target_query[len(prefix):].strip()
        
        # Split into keywords for fallback search
        keywords = [k for k in target_query.split() if len(k) > 2] # ignore very short words
        
        results = []
        
        targets_to_search = self.targets
        if namespace:
            targets_to_search = [t for t in self.targets if t['namespace'] == namespace]
            
        for target in targets_to_search:
            ns = target['namespace']
            file_path = os.path.join(STORAGE_DIR, f"{ns}_data.json")
            
            if not os.path.exists(file_path):
                continue
            
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    values = data.get('values', [])
                    
                if not values:
                    continue
                    
                header = values[0]
                # Identify Hal/Perihal column
                # Identify critical columns
                idx_hal = -1
                idx_no = [] # Let's find all number-related columns
                for i, h in enumerate(header):
                    h_upper = str(h).upper()
                    if h_upper in ("HAL", "PERIHAL") or ("HAL " in h_upper) or (" PERIHAL" in h_upper):
                        idx_hal = i
                    if any(x in h_upper for x in ["NOMOR", "NO", "ND", "KODE", "REF"]):
                        idx_no.append(i)
                        
                for row_idx, row in enumerate(values[1:]):
                    # Combine all row data for general search
                    row_str = " ".join([str(cell) for cell in row]).lower()
                    
                    # 1. Primary Check: Exact substring match (with or without prefix)
                    is_match = (target_query in row_str) or (original_query in row_str)
                    
                    # 2. Secondary Check: Keyword match (all keywords must exist in the row)
                    if not is_match and keywords:
                        is_match = all(k in row_str for k in keywords)
                    
                    if is_match:
                        # Priority tracking
                        match_on_hal = False
                        match_on_no = False
                        
                        if idx_hal != -1 and len(row) > idx_hal:
                            hal_val = str(row[idx_hal]).lower()
                            if (target_query and target_query in hal_val) or (keywords and all(k in hal_val for k in keywords)):
                                match_on_hal = True
                        
                        for idx in idx_no:
                            if idx < len(row):
                                no_val = str(row[idx]).lower()
                                if target_query in no_val or any(k in no_val for k in keywords):
                                    match_on_no = True
                                    break
                                
                        results.append({
                            "direktorat": target['name'],
                            "row_data": row,
                            "header": header,
                            "spreadsheet_id": target['spreadsheet_id'],
                            "row_num": row_idx + 2,
                            "match_on_hal": match_on_hal,
                            "match_on_no": match_on_no
                        })
            except Exception as e:
                logger.error(f"Error searching in {ns}: {e}")
                    
        # Sort: priority to NO matches, then HAL matches, then limit results
        results.sort(key=lambda x: (x.get("match_on_no", False), x.get("match_on_hal", False)), reverse=True)
        return results[:25] # Limit total search results for LLM efficiency

    def search_by_position(self, query: str) -> List[Dict]:
        """
        Search for letters based on their current POSITION or DISPOSISI.
        Supports flexible queries (Unit name, Person name, etc.)
        """
        import re
        query_clean = query.lower().strip()
        
        # Mapping common queries to recognized Units
        query_map = {
            "sekretaris": "SES",
            "sekretariat": "SES",
            "umum": "BU",
            "kepegawaian": "BU",
            "keuangan": "KEU",
            "perencanaan": "PRC",
            "hukum": "PUU",
            "perundang": "PUU",
            "perundang-undangan": "PUU",
            "undangan": "PUU",
            "peipd": "PEIPD"
        }
        target_unit = query_map.get(query_clean)
        
        results = []
        internal_ns = "korespondensi_internal_pooling"
        target_meta = next((t for t in self.targets if t['namespace'] == internal_ns), None)
        if not target_meta: return []

        file_path = os.path.join(STORAGE_DIR, f"{internal_ns}_data.json")
        if not os.path.exists(file_path): return []
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                values = data.get('values', [])
            
            if not values: return []
            header = values[0]
            
            # Find indices
            idx_pos = next((i for i, h in enumerate(header) if "POSISI" in str(h).upper()), 6)
            idx_dispo = next((i for i, h in enumerate(header) if "DISPOSISI" in str(h).upper()), 7)
            idx_dari = next((i for i, h in enumerate(header) if "DARI" in str(h).upper()), 4)

            for row_idx, row in enumerate(values[1:]):
                pos_raw = str(row[idx_pos]) if len(row) > idx_pos else ""
                dispo_raw = str(row[idx_dispo]) if len(row) > idx_dispo else ""
                dari_raw = str(row[idx_dari]) if len(row) > idx_dari else ""
                
                # Use our new powerful parser
                timeline = parse_posisi_timeline(pos_raw, sender=dari_raw)
                dispo_info = translate_disposisi(dispo_raw, sender=dari_raw)
                
                is_match = False
                
                # Check 1: Match CURRENT position unit
                if timeline:
                    last_ev = timeline[-1]
                    if target_unit and last_ev['unit'] == target_unit:
                        is_match = True
                    elif query_clean in last_ev['unit'].lower():
                        is_match = True
                    # Check 2: Match person/notes in last step (e.g., "Andin")
                    elif query_clean in last_ev.get('notes', '').lower():
                        is_match = True
                
                # Check 3: Match DISPOSISI forwarding
                if not is_match:
                    if target_unit and target_unit in [t.upper() for t in dispo_info.get("forwarded_to_list", [])]:
                        is_match = True
                    elif query_clean in str(dispo_info.get("forwarded_to_list", [])).lower():
                        is_match = True
                
                # Check 4: Full-text fallback (last resort)
                if not is_match and (query_clean in pos_raw.lower() or query_clean in dispo_raw.lower()):
                    is_match = True
                
                if is_match:
                    results.append({
                        "direktorat": target_meta['name'],
                        "row_data": row,
                        "header": header,
                        "spreadsheet_id": target_meta['spreadsheet_id'],
                        "row_num": row_idx + 2,
                        "has_code": bool(timeline)
                    })
            
            # Sort: prioritaskan data terbaru (berasumsi row terakhir adalah terbaru)
            results = results[::-1] # Reverse to get latest entries first
            
        except Exception as e:
            logger.error(f"search_by_position flexible error: {e}")
                    
        return results

    def _search_internal_by_day_month(self, day: int, month: int) -> List[Dict]:
        """
        Cari surat internal pooling berdasarkan tanggal (hari/bulan)
        dengan filter posisi mengandung PUU.

        Contoh query natural yang ditangani upstream:
        - "PUU 27/3" -> semua surat internal PUU tanggal 27 Maret.
        """
        internal_ns = "korespondensi_internal_pooling"
        target = next((t for t in self.targets if t['namespace'] == internal_ns), None)
        if not target:
            return []

        file_path = os.path.join(STORAGE_DIR, f"{internal_ns}_data.json")
        if not os.path.exists(file_path):
            return []

        results = []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                values = data.get('values', [])

            if not values:
                return []

            header = values[0]
            idx_tgl = next((i for i, h in enumerate(header) if "TANGGAL" in str(h).upper()), 2)
            idx_pos = next((i for i, h in enumerate(header) if "POSISI" in str(h).upper()), 6)

            for row_idx, row in enumerate(values[1:]):
                if len(row) <= max(idx_tgl, idx_pos):
                    continue

                pos_val = str(row[idx_pos]).upper()
                if "PUU" not in pos_val:
                    continue

                tgl_raw = row[idx_tgl]
                dt = parse_indonesian_date(tgl_raw)
                if dt == datetime.min:
                    continue

                if dt.day == day and dt.month == month:
                    results.append({
                        "direktorat": target['name'],
                        "row_data": row,
                        "header": header,
                        "spreadsheet_id": target['spreadsheet_id'],
                        "row_num": row_idx + 2,
                        "has_code": True,
                        "match_type": "date_fallback"
                    })

            # Urutkan terbaru dulu
            results.sort(
                key=lambda x: parse_indonesian_date(
                    x['row_data'][idx_tgl] if len(x['row_data']) > idx_tgl else ""
                ),
                reverse=True
            )
        except Exception as e:
            logger.error(f"_search_internal_by_day_month error: {e}")

        return results

# Helper for bot integration
def format_search_results(results: List[Dict], query: str) -> str:
    if not results:
        return f"🔍 Tidak ditemukan hasil untuk: *{query}*"
    
    output = f"🔍 *HASIL PENCARIAN*\nInput: `{query}` ({len(results)} temuan)\n\n"
    
    for res in results[:10]: # Tampilkan sampai 10 hasil
        data = res['row_data']
        header = res.get('header', [])
        has_code = res.get('has_code', False)
        match_on_hal = res.get('match_on_hal', False)
        
        fields = {}
        for i, h in enumerate(header):
            if i < len(data):
                h_upper = str(h).upper()
                # Priority labels
                if h_upper in ["TGL SURAT", "TANGGAL SURAT"]: fields["tgl"] = data[i]
                elif h_upper in ["TGL", "TANGGAL"]: fields["tgl"] = fields.get("tgl", data[i])
                elif "TGL" in h_upper or "TANGGAL" in h_upper: fields["tgl"] = fields.get("tgl", data[i])
                
                if h_upper in ["PERIHAL", "HAL", "ISI"]: fields["hal"] = data[i]
                elif any(x in h_upper for x in ["PERIHAL", "HAL", "ISI"]): fields["hal"] = fields.get("hal", data[i])
                
                if h_upper in ["SURAT DARI", "DARI", "PENGIRIM"]: fields["dari"] = data[i]
                elif any(x in h_upper for x in ["DARI", "SUMBER"]): fields["dari"] = fields.get("dari", data[i])
                elif "KELUAR" in h_upper: fields["dari"] = fields.get("dari", "PUU") # Default for Surat Keluar
                
                if h_upper in ["NOMOR SURAT", "NOMOR", "NO", "REF", "ND"]: fields["no"] = data[i]
                elif any(x in h_upper for x in ["NOMOR", "NO", "ND", "SURAT"]): fields["no"] = fields.get("no", data[i])
                
                if h_upper in ["POSISI", "STATUS"]: fields["pos"] = data[i]
                elif "POS" in h_upper or "STATUS" in h_upper: fields["pos"] = fields.get("pos", data[i])
                
                if h_upper in ["DISPOSISI", "ARAHAN SES", "ARAHAN"]: fields["dispo"] = data[i]
                elif "DISPO" in h_upper or "ARAHAN" in h_upper: fields["dispo"] = fields.get("dispo", data[i])

        tgl = fields.get("tgl", "N/A")
        hal = fields.get("hal", "N/A")
        dari = fields.get("dari", "N/A")
        pos = fields.get("pos", "N/A")
        no = fields.get("no", "N/A")

        # Icon logic: 📝 jika match di perihal, 🏷️ jika match kode, 📍 jika umum
        if match_on_hal:
            badge = "📝 "
        elif has_code:
            badge = "🏷️ "
        else:
            badge = "📍 "
            
        # Format Timeline secara visual jika barisnya panjang
        timeline = parse_posisi_timeline(pos, sender=dari)
        loop_count = len([ev for ev in timeline if "KOREKSI" in ev['action'] or "REVISI" in ev['action']])
        
        if len(timeline) > 1:
            # Contoh: 🔄 SES (2/1) -> BU (5/1) -> SES (7/1)
            steps = []
            for ev in timeline[-3:]:
                # Build part: [ACTION] UNIT (DATE TIME)
                display_unit = ev['unit']
                display_action = ev['action'] if ev['action'] not in ["UPDATE", "POSITION_CHECK"] else ""
                
                part = f"*{display_unit}*"
                if display_action: part = f"_{display_action}_ {part}"
                
                time_str = f" {ev['time']}" if ev.get('time') else ""
                part += f" ({ev['date']}{time_str})"
                
                if ev.get('notes'): part += f" _{ev['notes']}_"
                steps.append(part)
            
            path_str = " ➔ ".join(steps)
            if len(timeline) > 3: path_str = "... ➔ " + path_str
            
            # Bottleneck Warning Detection
            warning_msg = ""
            if loop_count >= 3:
                warning_msg = f"⚠️ *PERINGATAN:* Frekuensi perbaikan tinggi ({loop_count} kali koreksi). Kemungkinan ada kendala substansi.\n"
            elif len(timeline) >= 6:
                warning_msg = "🐢 *BOTTLENECK:* Proses surat sudah melalui 6+ tahapan, segera monitor perkembangan.\n"
                
            output += f"📍 *Status: {pos}*\n"
            if warning_msg: output += warning_msg
            output += f"🛤️ {path_str}\n"
        else:
            output += f"📍 *Status: {pos}*\n"
            
        # Decode DISPOSISI
        dispo_raw = fields.get("dispo")
        if dispo_raw:
            info = translate_disposisi(dispo_raw, sender=dari)
            if info["priority"] != "NORMAL":
                output += f"🚨 *{info['priority']}*\n"
            
            if info["forwarded_to_list"]:
                recipients = " & ".join(info["forwarded_to_list"])
                output += f"↪️ *Forwarded:* From {info['forwarded_from']} to {recipients}\n"
                if "priority_reason" in info:
                    output += f"💬 _{info['priority_reason']}_\n"
            
            output += f"📥 *Arahan:* _{dispo_raw}_\n"

        output += f"📅 `{tgl}` | 🏢 *{dari}*\n"
        output += f"🔢 *No:* `{no}`\n"
        output += f"📄 Hal: {hal}\n"
        output += f"🔗 [Buka Spreadsheet](https://docs.google.com/spreadsheets/d/{res['spreadsheet_id']}/edit#range={res['row_num']}:{res['row_num']})\n\n"
        
    if len(results) > 10:
        output += f"_...dan {len(results)-10} hasil lainnya._"
        
    return output

if __name__ == "__main__":
    db = CorrespondenceDashboard()
    print(db.get_recent_summary())
