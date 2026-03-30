#!/usr/bin/env python3
"""
Enhanced PUU Posisi Analysis - Versi 2.0
Fitur baru:
- Delay calculation (masuk -> PUU)
- Robust date parsing & sorting
- CSV export
- Summary stats JSON
- CLI options
"""

import json
import re
import csv
import argparse
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, List, Any
import pandas as pd  # Untuk CSV handling & stats

POOLING_FILE = "storage/admin_data/korespondensi/korespondensi_internal_pooling_data.json"
OUTPUT_FILTERED = "storage/admin_data/korespondensi/puu_posisi_filtered.json"
OUTPUT_SUMMARY = "storage/admin_data/korespondensi/puu_analysis_summary.json"
OUTPUT_CSV = "storage/admin_data/korespondensi/puu_posisi_analysis.csv"

def parse_indonesian_date(date_str: str, base_year: int = 2026) -> datetime:
    """Parse Indonesian date format with fallback to base_year"""
    if not date_str:
        return datetime.min.replace(year=1900)
    
    try:
        val = str(date_str).strip().upper()
        months_map = {
            'JAN':1, 'FEB':2, 'MAR':3, 'APR':4, 'MEI':5, 'JUN':6, 'JUL':7, 'AGU':8,
            'SEP':9, 'OKT':10, 'NOV':11, 'DES':12, 'JANUARI':1, 'FEBRUARI':2, 'MARET':3,
            'APRIL':4, 'JUNI':6, 'JULI':7, 'AGUSTUS':8, 'SEPTEMBER':9, 'OKTOBER':10,
            'NOVEMBER':11, 'DESEMBER':12
        }
        
        for mon_name, mon_num in months_map.items():
            val = val.replace(mon_name, str(mon_num))
        
        # Clean to dd/mm or mm/dd
        clean = re.sub(r'[^\d/]', '/', val)
        clean = re.sub(r'/+', '/', clean).strip('/')
        
        # Try common formats
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%d/%m", "%m/%d"):
            try:
                dt = datetime.strptime(clean, fmt)
                if dt.year == 1900:  # No year
                    dt = dt.replace(year=base_year)
                return dt
            except ValueError:
                continue
                
    except Exception:
        pass
    
    return datetime(1900, 1, 1)

def extract_puu_info(pos_str: str) -> Dict[str, Any]:
    """Enhanced PUU extraction: all dates after PUU, latest date, full context"""
    pos_upper = pos_str.upper()
    puu_matches = re.finditer(r'PUU\s*[^\d]*(\d{1,2}/\d{1,2})', pos_upper)
    puu_dates = [match.group(1) for match in puu_matches]
    all_dates = re.findall(r'(\d{1,2}/\d{1,2})', pos_str)
    
    latest_puu_date_str = puu_dates[-1] if puu_dates else None
    latest_puu_dt = parse_indonesian_date(latest_puu_date_str) if latest_puu_date_str else datetime(1900, 1, 1)
    
    return {
        'puu_codes': puu_dates,
        'all_dates': all_dates[:5],
        'latest_puu_date_str': latest_puu_date_str,
        'latest_puu_date': latest_puu_dt,
        'puu_count': len(puu_dates),
        'posisi_raw': pos_str.strip()
    }

def analyze_delays(puu_data: List[Dict]) -> Dict[str, Any]:
    """Calculate processing delays and stats"""
    delays = []
    valid_rows = []
    
    for row in puu_data:
        masuk_date = parse_indonesian_date(row['tanggal'])
        puu_date = row['puu_info']['latest_puu_date']
        
        if masuk_date > datetime(2025, 1, 1) and puu_date > datetime(2025, 1, 1):
            delay = (puu_date - masuk_date).days
            delays.append(delay)
            valid_rows.append(row)
    
    if not delays:
        return {'avg_delay': 0, 'max_delay': 0, 'min_delay': 0, 'total_valid': 0}
    
    return {
        'avg_delay_days': round(sum(delays) / len(delays), 1),
        'max_delay_days': max(delays),
        'min_delay_days': min(delays),
        'total_valid_rows': len(delays),
        'delays': delays
    }

def main(args):
    print("🚀 ENHANCED PUU POSISI ANALYSIS v2.0")
    print("=" * 60)
    
    # Load pooling data
    print(f"📂 Loading {POOLING_FILE}...")
    with open(POOLING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    values = data['values'][1:]  # Skip header
    
    # Filter PUU rows
    puu_rows = []
    for row in values:
        if len(row) > 6:
            pos_raw = str(row[6])
            if 'PUU' in pos_raw.upper():
                masuk_dt = parse_indonesian_date(row[2] if len(row) > 2 else '')
                puu_info = extract_puu_info(pos_raw)
                
                puu_rows.append({
                    'unique_id': row[0],
                    'no_agenda': row[1] if len(row) > 1 else '',
                    'tanggal': row[2] if len(row) > 2 else '',
                    'tanggal_parsed': masuk_dt,
                    'nomor_nd': row[3] if len(row) > 3 else '',
                    'dari': row[4] if len(row) > 4 else '',
                    'hal': row[5] if len(row) > 5 else '',
                    'posisi_raw': pos_raw,
                    'disposisi': row[7] if len(row) > 7 else '',
                    'puu_info': puu_info
                })
    
    # Sort by latest PUU date DESC
    puu_rows.sort(key=lambda x: x['puu_info']['latest_puu_date'], reverse=True)
    
    print(f"✅ {len(puu_rows)} PUU rows dari {len(values)} total")
    
    # Analysis
    delay_stats = analyze_delays(puu_rows)
    dari_counter = Counter([r['dari'] for r in puu_rows])
    
    print("\n📊 SUMMARY STATS:")
    print(f"   Total PUU: {len(puu_rows)}")
    print(f"   Avg Delay: {delay_stats['avg_delay_days']} hari")
    print(f"   Max Delay: {delay_stats['max_delay_days']} hari")
    print(f"   Top DARI: {dari_counter.most_common(3)}")
    
    # Save filtered
    # Convert datetime to str for JSON serialization
    serializable_rows = []
    for row in puu_rows:
        serial_row = row.copy()
        if serial_row['tanggal_parsed'] and serial_row['tanggal_parsed'] != datetime(1900,1,1):
            serial_row['tanggal_parsed'] = serial_row['tanggal_parsed'].isoformat()
        else:
            serial_row['tanggal_parsed'] = None
            
        # Serialize puu_info latest_puu_date too
        puu_info = serial_row['puu_info'].copy()
        puu_dt = puu_info['latest_puu_date']
        if puu_dt and puu_dt != datetime(1900,1,1):
            puu_info['latest_puu_date'] = puu_dt.isoformat()
        else:
            puu_info['latest_puu_date'] = None
        serial_row['puu_info'] = puu_info
            
        serializable_rows.append(serial_row)
    
    output_data = {
        "metadata": {
            "total_puu_rows": len(puu_rows),
            "source_total": len(values),
            "avg_delay_days": delay_stats['avg_delay_days'],
            "max_delay_days": delay_stats['max_delay_days'],
            "filter": "POSISI contains 'PUU'",
            "created": datetime.now().isoformat(),
            "sorted_by": "latest_puu_date DESC"
        },
        "puu_posisi_data": serializable_rows
    }
    
    with open(OUTPUT_FILTERED, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 {OUTPUT_FILTERED} updated")
    
    # Save summary
    summary = {
        "timestamp": str(datetime.now()),
        "total_puu": len(puu_rows),
        "delay_stats": delay_stats,
        "top_dari": dari_counter.most_common(5),
        "top_hal_keywords": Counter(' '.join([r['hal'] for r in puu_rows]).lower().split()).most_common(5)
    }
    with open(OUTPUT_SUMMARY, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"💾 {OUTPUT_SUMMARY} generated")
    
    # CSV Export
    if args.csv:
        df = pd.DataFrame(puu_rows)
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"📊 {OUTPUT_CSV} exported ({len(puu_rows)} rows)")
    
    # Print top samples
    print("\n🏆 TOP 5 TERBARU (by PUU date):")
    for i, row in enumerate(puu_rows[:5], 1):
        print(f"{i}. ID: {row['unique_id']}")
        print(f"   📅 Masuk: {row['tanggal']} → PUU: {row['puu_info']['latest_puu_date_str']}")
        print(f"   ⏱️  Delay: {(row['puu_info']['latest_puu_date'] - row['tanggal_parsed']).days} hari")
        print(f"   👤 {row['dari'][:30]}...")
        print(f"   📄 {row['hal'][:60]}...")
        print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced PUU Analysis")
    parser.add_argument('--csv', action='store_true', help='Export CSV')
    parser.add_argument('--enhanced', action='store_true', help='Run full analysis (default)')
    args = parser.parse_args()
    
    main(args)

