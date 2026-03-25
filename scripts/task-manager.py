#!/usr/bin/env python3
"""
Task Manager — Utility untuk mengelola task lifecycle

Usage:
    task-manager.py list
    task-manager.py status <task-num>
    task-manager.py verify <task-num>
    task-manager.py audit
    task-manager.py create-status <task-num>
    task-manager.py update-status <task-num> --status <STATUS>
"""

import argparse
import sys
import os
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/home/aseps/MCP")
TASKS_DIR = BASE_DIR / "tasks"
STATUS_DIR = TASKS_DIR / "status"
DOCS_DIR = BASE_DIR / "docs"


def get_task_file(task_num: int) -> Path:
    """Find task file by number."""
    pattern = f"TASK-{task_num:03d}-*.md"
    
    # Search in active, backlog, completed
    for subdir in ["active", "backlog", "completed"]:
        dir_path = TASKS_DIR / subdir
        if dir_path.exists():
            matches = list(dir_path.glob(pattern))
            if matches:
                return matches[0]
    return None


def get_status_file(task_num: int) -> Path:
    """Get status file path."""
    return STATUS_DIR / f"TASK-{task_num:03d}-status.md"


def list_tasks():
    """List all tasks with their status."""
    print("=" * 60)
    print("TASK LIST")
    print("=" * 60)
    
    for subdir, label in [("backlog", "📋 BACKLOG"), 
                          ("active", "🔨 ACTIVE"), 
                          ("completed", "✅ COMPLETED")]:
        dir_path = TASKS_DIR / subdir
        if not dir_path.exists():
            continue
            
        files = sorted(dir_path.glob("TASK-*.md"))
        if files:
            print(f"\n{label}:")
            for f in files:
                # Extract task number and name
                match = re.match(r"TASK-(\d+)-(.+)\.md", f.name)
                if match:
                    num, name = match.groups()
                    name = name.replace("-", " ")
                    print(f"  TASK-{num}: {name}")


def show_status(task_num: int):
    """Show detailed status of a task."""
    task_file = get_task_file(task_num)
    status_file = get_status_file(task_num)
    
    print(f"=" * 60)
    print(f"TASK-{task_num:03d} STATUS")
    print(f"=" * 60)
    
    if task_file:
        print(f"\n📄 Task File: {task_file.relative_to(BASE_DIR)}")
        
        # Read and display key info
        content = task_file.read_text()
        
        # Extract title
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            print(f"   Title: {title_match.group(1)}")
        
        # Extract status from task file
        status_match = re.search(r"\*\*Status:\*\*\s*(\w+)", content)
        if status_match:
            print(f"   Declared Status: {status_match.group(1)}")
    else:
        print(f"\n❌ Task file not found")
    
    if status_file.exists():
        print(f"\n📊 Status File: {status_file.relative_to(BASE_DIR)}")
        content = status_file.read_text()
        
        # Extract current status
        status_match = re.search(r"## Current Status:\s*(.+)", content)
        if status_match:
            print(f"   Current Status: {status_match.group(1).strip()}")
        
        # Extract last updated
        updated_match = re.search(r"\*\*Last Updated:\*\*\s*(.+)", content)
        if updated_match:
            print(f"   Last Updated: {updated_match.group(1).strip()}")
    else:
        print(f"\n⚠️  Status file not found (run: task-manager.py create-status {task_num})")


def create_status_file(task_num: int):
    """Create a new status file for a task."""
    task_file = get_task_file(task_num)
    if not task_file:
        print(f"❌ Task file TASK-{task_num:03d} not found")
        return
    
    status_file = get_status_file(task_num)
    status_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract info from task file
    content = task_file.read_text()
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else f"TASK-{task_num:03d}"
    
    # Get current date
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    status_content = f"""# TASK-{task_num:03d} Status

**Task:** [{title}](../active/{task_file.name})  
**Last Updated:** {now}  
**Updated By:** agent

---

## Current Status: BACKLOG

## Progress Checklist
- [ ] Subtask A
- [ ] Subtask B
- [ ] Subtask C

## Verification
| Aspek | Status | Detail |
|-------|--------|--------|
| Code | ⏳ | Belum dimulai |
| Tests | ⏳ | Belum dimulai |
| Docs | ⏳ | Belum dimulai |

## Blockers
None.

## Next Steps
1. Pindahkan task ke folder `active/`
2. Update status ke ACTIVE
3. Mulai implementasi
"""
    
    status_file.write_text(status_content)
    print(f"✅ Created status file: {status_file.relative_to(BASE_DIR)}")


def update_status(task_num: int, new_status: str, sync_ltm: bool = True):
    """Update task status dengan optional LTM sync."""
    status_file = get_status_file(task_num)
    
    if not status_file.exists():
        print(f"❌ Status file not found. Run: task-manager.py create-status {task_num}")
        return
    
    content = status_file.read_text()
    
    # Update status line
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = re.sub(
        r"## Current Status: .+",
        f"## Current Status: {new_status.upper()}",
        content
    )
    content = re.sub(
        r"\*\*Last Updated:\*\* .+",
        f"**Last Updated:** {now}",
        content
    )
    
    status_file.write_text(content)
    print(f"✅ Updated TASK-{task_num:03d} status to: {new_status.upper()}")
    
    # Auto-sync LTM setelah status update
    if sync_ltm:
        print("\n🔄 Syncing LTM...")
        sync_result = os.system("cd /home/aseps/MCP && python3 scripts/sync_ltm_tasks.py --quick-sync > /dev/null 2>&1")
        if sync_result == 0:
            print("✅ LTM synced successfully")
        else:
            print("⚠️  LTM sync failed (non-critical)")


def sync_ltm(full_sync: bool = False):
    """Sync tasks to LTM database."""
    print("=" * 60)
    print("LTM SYNC")
    print("=" * 60)
    
    cmd = "cd /home/aseps/MCP && python3 scripts/sync_ltm_tasks.py"
    if full_sync:
        cmd += " --full-sync --verify"
    else:
        cmd += " --quick-sync"
    
    result = os.system(cmd)
    
    if result == 0:
        print("\n✅ LTM sync completed")
    else:
        print("\n❌ LTM sync failed")


def audit_tasks():
    """Audit all tasks for inconsistencies."""
    print("=" * 60)
    print("TASK AUDIT REPORT")
    print("=" * 60)
    
    issues = []
    
    # Check all task files
    for subdir in ["backlog", "active", "completed"]:
        dir_path = TASKS_DIR / subdir
        if not dir_path.exists():
            continue
            
        for task_file in dir_path.glob("TASK-*.md"):
            match = re.match(r"TASK-(\d+)-.+\.md", task_file.name)
            if not match:
                continue
                
            task_num = int(match.group(1))
            content = task_file.read_text()
            
            # Check declared status
            declared_match = re.search(r"\*\*Status:\*\*\s*(\w+)", content)
            declared_status = declared_match.group(1) if declared_match else "UNKNOWN"
            
            # Check if status file exists
            status_file = get_status_file(task_num)
            if not status_file.exists():
                issues.append(f"TASK-{task_num:03d}: Missing status file")
                continue
            
            # Check status file content
            status_content = status_file.read_text()
            status_match = re.search(r"## Current Status:\s*(.+)", status_content)
            current_status = status_match.group(1).strip() if status_match else "UNKNOWN"
            
            # Compare
            if declared_status.upper() != current_status.upper():
                issues.append(
                    f"TASK-{task_num:03d}: Status mismatch "
                    f"(task: {declared_status}, status: {current_status})"
                )
    
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ No issues found. All tasks are consistent.")


def main():
    parser = argparse.ArgumentParser(description="Task Manager Utility")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # list command
    subparsers.add_parser("list", help="List all tasks")
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show task status")
    status_parser.add_argument("task_num", type=int, help="Task number")
    
    # create-status command
    create_parser = subparsers.add_parser("create-status", help="Create status file")
    create_parser.add_argument("task_num", type=int, help="Task number")
    
    # update-status command
    update_parser = subparsers.add_parser("update-status", help="Update task status")
    update_parser.add_argument("task_num", type=int, help="Task number")
    update_parser.add_argument("--status", required=True, 
                              choices=["BACKLOG", "ACTIVE", "BLOCKED", "COMPLETED"],
                              help="New status")
    
    # audit command
    subparsers.add_parser("audit", help="Audit tasks for inconsistencies")
    
    # sync-ltm command
    sync_parser = subparsers.add_parser("sync-ltm", help="Sync tasks to LTM database")
    sync_parser.add_argument("--full", action="store_true", help="Run full sync with verification")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_tasks()
    elif args.command == "status":
        show_status(args.task_num)
    elif args.command == "create-status":
        create_status_file(args.task_num)
    elif args.command == "update-status":
        update_status(args.task_num, args.status)
    elif args.command == "audit":
        audit_tasks()
    elif args.command == "sync-ltm":
        sync_ltm(full_sync=args.full)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
