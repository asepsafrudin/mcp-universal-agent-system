import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any

# Root Path
PROJECT_ROOT = "/home/aseps/MCP"
POOLING_JSON = os.path.join(PROJECT_ROOT, "storage/admin_data/korespondensi/korespondensi_internal_pooling_data.json")

def parse_full_timeline(posisi_str: str) -> List[Dict[str, Any]]:
    """
    Parses a complex position string into a list of timeline events.
    Example: 'SES 2/1 KOREKSI 5/1 TTD 7/1'
    -> [ {'unit': 'SES', 'date': '2/1', 'action': 'ENTER'}, 
         {'unit': 'SES', 'date': '5/1', 'action': 'KOREKSI'},
         {'unit': 'SES', 'date': '7/1', 'action': 'TTD'} ]
    """
    if not posisi_str or str(posisi_str).lower() == 'null':
        return []

    # Units and keywords mapping based on organizational structure
    units = ["SES", "BU", "KEU", "PRC", "PUU", "DIRJEN", "UMUM"]
    actions = ["KOREKSI", "TTD", "PARAF", "REVISI", "PROSES", "KIRIM", "SELESAI", "DJ", "ND"]
    
    # Normalize
    pos_str = str(posisi_str).upper().replace("-", "/").strip()
    
    # Regex to find tokens: either a unit, a date (d/m), or an action
    # This is a heuristic approach
    pattern = re.compile(r'([A-Z]+|\d{1,2}/\d{1,2})')
    tokens = pattern.findall(pos_str)
    
    timeline = []
    current_unit = "UNKNOWN"
    current_date = None
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # 1. Is it a Unit?
        if token in units:
            current_unit = token
            # Check if next token is a date
            if i + 1 < len(tokens) and re.match(r'\d{1,2}/\d{1,2}', tokens[i+1]):
                current_date = tokens[i+1]
                timeline.append({
                    "unit": current_unit,
                    "date": current_date,
                    "action": "POSITION_CHECK"
                })
                i += 2
                continue
            else:
                # Just unit changed
                i += 1
                continue
                
        # 2. Is it a Date without a preceding Unit?
        elif re.match(r'\d{1,2}/\d{1,2}', token):
            current_date = token
            # If we don't have an action before this, it's a date-only update
            timeline.append({
                "unit": current_unit,
                "date": current_date,
                "action": "UPDATE"
            })
            i += 1
            continue
            
        # 3. Is it an Action?
        elif token in actions:
            action = token
            # Check if followed by date
            if i + 1 < len(tokens) and re.match(r'\d{1,2}/\d{1,2}', tokens[i+1]):
                current_date = tokens[i+1]
                timeline.append({
                    "unit": current_unit,
                    "date": current_date,
                    "action": action
                })
                i += 2
                continue
            else:
                # Action without date (usually last known date apply)
                timeline.append({
                    "unit": current_unit,
                    "date": current_date,
                    "action": action
                })
                i += 1
                continue
        else:
            i += 1 # Skip unknown tokens
            
    return timeline

def analyze_database():
    if not os.path.exists(POOLING_JSON):
        print("Data files not found.")
        return

    with open(POOLING_JSON, 'r') as f:
        data = json.load(f)
    
    values = data.get('values', [])
    if len(values) <= 1:
        return
        
    header = values[0]
    rows = values[1:]
    
    # Indices
    idx_uid = 0
    idx_hal = 5
    idx_pos = 6
    
    analysis_results = []
    
    for r in rows:
        if len(r) <= idx_pos: continue
        
        uid = r[idx_uid]
        hal = r[idx_hal]
        pos_raw = r[idx_pos]
        
        timeline = parse_full_timeline(pos_raw)
        
        if timeline:
            # Determine total duration (if dates are parseable)
            # Find current stage (last event unit)
            # Find status (done or not)
            
            entry = {
                "id": uid,
                "hal": hal,
                "raw_pos": pos_raw,
                "current_unit": timeline[-1]['unit'] if timeline else "UNKNOWN",
                "events_count": len(timeline),
                "timeline": timeline,
                "is_done": any(ev['action'] in ['SELESAI', 'TTD', 'DJ'] for ev in timeline)
            }
            analysis_results.append(entry)

    # Print a small sample for summary
    print(f"Total analyzed rows: {len(analysis_results)}")
    print("\n--- SAMPLE TIMELINE ANALYSIS ---")
    for item in analysis_results[:3]:
        print(f"\nID: {item['id']}")
        print(f"Hal: {item['hal'][:50]}...")
        print(f"Path: {' -> '.join([f'({ev[u'unit']}:{ev[u'action']}@{ev[u'date']})' for ev in item['timeline']])}")
        print(f"Summary: Currently at {item['current_unit']}, Total Steps: {item['events_count']}")

    # Save logic for LLM ingestion later
    output_path = os.path.join(PROJECT_ROOT, "storage/admin_data/korespondensi/puu_timeline_analysis.json")
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    print(f"\nAnalysis saved to: {output_path}")

if __name__ == "__main__":
    analyze_database()
