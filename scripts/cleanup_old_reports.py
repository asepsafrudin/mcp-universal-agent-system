#!/usr/bin/env python3
"""
Cleanup Script untuk Old Reports
Menghapus audit reports dan quality reports yang lebih dari 7 hari
"""

import os
import sys
import glob
from datetime import datetime, timedelta
import argparse

def cleanup_old_reports(dry_run=True, days_old=7):
    """
    Cleanup old audit and quality reports
    
    Args:
        dry_run: Jika True, hanya menampilkan files yang akan dihapus
        days_old: Hapus files yang lebih tua dari N hari
    """
    # Get script directory (MCP root)
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Patterns untuk files yang akan dihapus
    patterns = [
        os.path.join(script_dir, "crew/mcp_server_audit_*.json"),
        os.path.join(script_dir, "quality_report_*.json"),
        os.path.join(script_dir, "crew/*.log.txt"),
    ]
    
    # Cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    files_to_delete = []
    total_size = 0
    
    # Find all matching files
    for pattern in patterns:
        for filepath in glob.glob(pattern):
            # Check file modification time
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            if file_mtime < cutoff_date:
                file_size = os.path.getsize(filepath)
                files_to_delete.append((filepath, file_size, file_mtime))
                total_size += file_size
    
    # Sort by modification time
    files_to_delete.sort(key=lambda x: x[2])
    
    # Display results
    if not files_to_delete:
        print(f"✅ No files older than {days_old} days found.")
        return 0
    
    print(f"{'🔍 DRY RUN - ' if dry_run else ''}Found {len(files_to_delete)} files to delete:")
    print(f"Total size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print()
    
    for filepath, size, mtime in files_to_delete:
        age_days = (datetime.now() - mtime).days
        print(f"  {'[DRY RUN] ' if dry_run else ''}📄 {os.path.basename(filepath)}")
        print(f"     Size: {size:,} bytes | Age: {age_days} days | Modified: {mtime.strftime('%Y-%m-%d %H:%M')}")
    
    # Delete files if not dry run
    if not dry_run:
        print()
        deleted_count = 0
        for filepath, size, mtime in files_to_delete:
            try:
                os.remove(filepath)
                deleted_count += 1
                print(f"  ✅ Deleted: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"  ❌ Failed to delete {os.path.basename(filepath)}: {e}")
        
        print()
        print(f"✅ Cleanup completed! Deleted {deleted_count}/{len(files_to_delete)} files.")
        print(f"   Freed up {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    else:
        print()
        print("🔍 This was a DRY RUN. No files were deleted.")
        print("   Run with --execute to actually delete these files.")
    
    return len(files_to_delete)

def main():
    parser = argparse.ArgumentParser(
        description="Cleanup old audit and quality reports from MCP project"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete files (default is dry-run mode)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Delete files older than N days (default: 7)"
    )
    
    args = parser.parse_args()
    
    print("🧹 MCP Project Cleanup Script")
    print("=" * 60)
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print(f"Delete files older than: {args.days} days")
    print("=" * 60)
    print()
    
    count = cleanup_old_reports(dry_run=not args.execute, days_old=args.days)
    
    return 0 if count >= 0 else 1

if __name__ == "__main__":
    sys.exit(main())
