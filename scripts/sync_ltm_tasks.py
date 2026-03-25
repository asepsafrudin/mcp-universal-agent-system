#!/usr/bin/env python3
"""
LTM Task Sync Script

Script untuk mensinkronisasikan status task dari tasks/ folder ke LTM database.
Menjaga agar LTM selalu real-time dan akurat.

Usage:
    python3 sync_ltm_tasks.py [--scan-only] [--update-project-memories] [--update-ltm-memory] [--update-memories] [--quick-sync] [--verify]

Features:
    1. Scan task files dari tasks/active/, tasks/completed/, tasks/backlog/
    2. Parse metadata dan progress dari setiap task
    3. Update LTM tables: project_memories, ltm_memory, memories
    4. Verifikasi konsistensi data
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Database connection
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_SERVER", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "mcp"),
    "user": os.getenv("POSTGRES_USER", "aseps"),
    "password": os.getenv("POSTGRES_PASSWORD", "secure123")
}

TASKS_DIR = Path("/home/aseps/MCP/tasks")


class TaskParser:
    """Parser untuk task markdown files."""
    
    @staticmethod
    def parse_task_file(filepath: Path) -> Optional[Dict[str, Any]]:
        """Parse task file dan extract metadata."""
        if not filepath.exists():
            return None
        
        content = filepath.read_text(encoding='utf-8')
        
        # Extract task ID dan nama
        task_id_match = re.search(r'TASK-(\d+)', filepath.name)
        task_id = f"TASK-{task_id_match.group(1)}" if task_id_match else filepath.stem
        
        # Parse header metadata
        metadata = {
            "id": task_id,
            "filename": filepath.name,
            "path": str(filepath),
            "status": "UNKNOWN",
            "priority": "MEDIUM",
            "progress": 0,
            "title": "",
            "created": None,
            "updated": None,
            "assignee": None,
            "category": filepath.parent.name  # active, completed, backlog
        }
        
        # Extract status
        status_match = re.search(r'\*\*Status:\*\*\s*(\w+)', content, re.IGNORECASE)
        if status_match:
            metadata["status"] = status_match.group(1).upper()
        
        # Extract priority
        priority_match = re.search(r'\*\*Priority\*\*:\s*(\w+)', content, re.IGNORECASE)
        if priority_match:
            metadata["priority"] = priority_match.group(1).upper()
        
        # Extract progress dari progress checklist atau Phase
        progress_patterns = [
            r'(\d+)%\s*complete',
            r'Progress:\s*(\d+)%',
            r'(\d+)/\d+\s*subtasks',
        ]
        for pattern in progress_patterns:
            progress_match = re.search(pattern, content, re.IGNORECASE)
            if progress_match:
                metadata["progress"] = int(progress_match.group(1))
                break
        
        # Extract title dari heading #
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        
        # Extract dates
        created_match = re.search(r'\*\*Created\*\*:\s*(\d{4}-\d{2}-\d{2})', content)
        if created_match:
            metadata["created"] = created_match.group(1)
        
        updated_match = re.search(r'\*\*Last Updated\*\*:\s*(\d{4}-\d{2}-\d{2})', content)
        if updated_match:
            metadata["updated"] = updated_match.group(1)
        
        # Extract assignee
        assignee_match = re.search(r'\*\*Assignee\*\*:\s*(.+?)\n', content)
        if assignee_match:
            metadata["assignee"] = assignee_match.group(1).strip()
        
        # Count subtasks
        total_subtasks = len(re.findall(r'- \[([ x])\]', content))
        completed_subtasks = len(re.findall(r'- \[x\]', content))
        if total_subtasks > 0:
            metadata["progress"] = int((completed_subtasks / total_subtasks) * 100)
            metadata["subtasks_total"] = total_subtasks
            metadata["subtasks_completed"] = completed_subtasks
        
        return metadata
    
    @staticmethod
    def scan_all_tasks() -> Dict[str, List[Dict[str, Any]]]:
        """Scan semua task files."""
        tasks = {
            "active": [],
            "completed": [],
            "backlog": []
        }
        
        for category in tasks.keys():
            category_dir = TASKS_DIR / category
            if category_dir.exists():
                for task_file in sorted(category_dir.glob("TASK-*.md")):
                    task_data = TaskParser.parse_task_file(task_file)
                    if task_data:
                        tasks[category].append(task_data)
        
        return tasks


class LTMSync:
    """Sync tasks ke LTM database."""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect ke database."""
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
    
    def disconnect(self):
        """Disconnect dari database."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def update_project_memories(self, tasks: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Update project_memories table."""
        try:
            # Get active tasks summary
            active_tasks = tasks.get("active", [])
            completed_tasks = tasks.get("completed", [])
            
            # Build content
            content = {
                "engine": "MCP Task Manager",
                "status": "OPERATIONAL",
                "last_sync": datetime.now().isoformat(),
                "metrics": {
                    "active_tasks": len(active_tasks),
                    "completed_tasks": len(completed_tasks),
                    "total_tasks": len(active_tasks) + len(completed_tasks)
                },
                "current_tasks": [
                    f"{t['id']}: {t['title'][:50]} ({t['progress']}%)"
                    for t in active_tasks[:5]
                ]
            }
            
            # Update database
            self.cursor.execute("""
                INSERT INTO project_memories (project_name, memory_type, content, updated_at)
                VALUES ('MCP Unified Tasks', 'task_status', %s, CURRENT_TIMESTAMP)
                ON CONFLICT (project_name) DO UPDATE SET
                    content = EXCLUDED.content,
                    updated_at = CURRENT_TIMESTAMP
            """, (json.dumps(content),))
            
            self.conn.commit()
            print(f"✅ Updated project_memories: {len(active_tasks)} active, {len(completed_tasks)} completed")
            return True
            
        except Exception as e:
            print(f"❌ Error updating project_memories: {e}")
            self.conn.rollback()
            return False
    
    def update_ltm_memory(self, tasks: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Update ltm_memory table."""
        try:
            active_tasks = tasks.get("active", [])
            completed_tasks = tasks.get("completed", [])
            
            data = {
                "active_tasks": [
                    {
                        "id": t["id"],
                        "name": t["title"][:100],
                        "progress": t["progress"],
                        "status": t["status"],
                        "priority": t["priority"]
                    }
                    for t in active_tasks
                ],
                "completed_tasks": [
                    {
                        "id": t["id"],
                        "name": t["title"][:100],
                        "completed_at": t.get("updated", datetime.now().isoformat())
                    }
                    for t in completed_tasks[-5:]  # Last 5 completed
                ],
                "notes": [
                    f"Active: {len(active_tasks)} tasks in progress",
                    f"Completed: {len(completed_tasks)} tasks done",
                    f"Last sync: {datetime.now().isoformat()}"
                ],
                "last_sync": datetime.now().isoformat()
            }
            
            self.cursor.execute("""
                INSERT INTO ltm_memory (session_id, project, status, timestamp, data)
                VALUES ('mcp_task_sync', 'MCP Unified', 'ACTIVE', CURRENT_TIMESTAMP, %s)
                ON CONFLICT (session_id) DO UPDATE SET
                    project = EXCLUDED.project,
                    status = EXCLUDED.status,
                    timestamp = CURRENT_TIMESTAMP,
                    data = EXCLUDED.data
            """, (json.dumps(data),))
            
            self.conn.commit()
            print(f"✅ Updated ltm_memory: session 'mcp_task_sync'")
            return True
            
        except Exception as e:
            print(f"❌ Error updating ltm_memory: {e}")
            self.conn.rollback()
            return False
    
    def update_memories(self, tasks: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Update memories table."""
        try:
            active_tasks = tasks.get("active", [])
            
            for task in active_tasks[:3]:  # Top 3 active tasks
                content = f"""
Task {task['id']}: {task['title']}
Status: {task['status']} | Progress: {task['progress']}% | Priority: {task['priority']}
Location: {task['path']}
                """.strip()
                
                metadata = {
                    "task_id": task["id"],
                    "progress": task["progress"],
                    "status": task["status"],
                    "priority": task["priority"],
                    "category": task["category"],
                    "last_sync": datetime.now().isoformat()
                }
                
                self.cursor.execute("""
                    INSERT INTO memories (namespace, key, content, metadata)
                    VALUES ('mcp_tasks', %s, %s, %s)
                    ON CONFLICT (namespace, key) DO UPDATE SET
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        created_at = CURRENT_TIMESTAMP
                """, (task["id"], content, json.dumps(metadata)))
            
            # Update system overview
            system_content = f"""
MCP Task System Overview ({datetime.now().strftime('%Y-%m-%d %H:%M')})
Active Tasks: {len(active_tasks)}
Completed Tasks: {len(tasks.get('completed', []))}
Backlog: {len(tasks.get('backlog', []))}
            """.strip()
            
            self.cursor.execute("""
                INSERT INTO memories (namespace, key, content, metadata)
                VALUES ('mcp_system', 'task_overview', %s, %s)
                ON CONFLICT (namespace, key) DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    created_at = CURRENT_TIMESTAMP
            """, (system_content, json.dumps({"last_sync": datetime.now().isoformat()})))
            
            self.conn.commit()
            print(f"✅ Updated memories: {len(active_tasks)} task records")
            return True
            
        except Exception as e:
            print(f"❌ Error updating memories: {e}")
            self.conn.rollback()
            return False
    
    def quick_sync(self, tasks: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Quick sync - update only essential data."""
        try:
            # Update only ltm_memory dengan data minimal
            active_tasks = tasks.get("active", [])
            
            data = {
                "active_count": len(active_tasks),
                "top_task": active_tasks[0]["title"] if active_tasks else "None",
                "last_sync": datetime.now().isoformat()
            }
            
            self.cursor.execute("""
                UPDATE ltm_memory 
                SET data = data || %s::jsonb,
                    timestamp = CURRENT_TIMESTAMP
                WHERE session_id = 'mcp_task_sync'
            """, (json.dumps(data),))
            
            self.conn.commit()
            print(f"✅ Quick sync completed")
            return True
            
        except Exception as e:
            print(f"❌ Error quick sync: {e}")
            self.conn.rollback()
            return False
    
    def verify_sync(self) -> bool:
        """Verifikasi konsistensi data LTM."""
        try:
            checks = []
            
            # Check project_memories
            self.cursor.execute("""
                SELECT COUNT(*) as count FROM project_memories 
                WHERE project_name = 'MCP Unified Tasks'
            """)
            result = self.cursor.fetchone()
            checks.append(("project_memories", result["count"] > 0))
            
            # Check ltm_memory
            self.cursor.execute("""
                SELECT COUNT(*) as count FROM ltm_memory 
                WHERE session_id = 'mcp_task_sync'
            """)
            result = self.cursor.fetchone()
            checks.append(("ltm_memory", result["count"] > 0))
            
            # Check memories
            self.cursor.execute("""
                SELECT COUNT(*) as count FROM memories 
                WHERE namespace = 'mcp_tasks'
            """)
            result = self.cursor.fetchone()
            checks.append(("memories (mcp_tasks)", result["count"] > 0))
            
            # Check last update time
            self.cursor.execute("""
                SELECT MAX(updated_at) as last_update FROM project_memories
                WHERE project_name = 'MCP Unified Tasks'
            """)
            result = self.cursor.fetchone()
            last_update = result["last_update"]
            
            print("\n📊 LTM Sync Verification:")
            print("-" * 40)
            for name, status in checks:
                icon = "✅" if status else "❌"
                print(f"{icon} {name}: {'OK' if status else 'MISSING'}")
            
            if last_update:
                print(f"\n🕐 Last update: {last_update}")
            
            return all(status for _, status in checks)
            
        except Exception as e:
            print(f"❌ Error verifying sync: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Sync tasks to LTM database")
    parser.add_argument("--scan-only", action="store_true", help="Only scan task files")
    parser.add_argument("--update-project-memories", action="store_true", help="Update project_memories table")
    parser.add_argument("--update-ltm-memory", action="store_true", help="Update ltm_memory table")
    parser.add_argument("--update-memories", action="store_true", help="Update memories table")
    parser.add_argument("--quick-sync", action="store_true", help="Quick sync (minimal update)")
    parser.add_argument("--verify", action="store_true", help="Verify LTM sync")
    parser.add_argument("--full-sync", action="store_true", help="Run full sync (all tables)")
    
    args = parser.parse_args()
    
    print("🔄 LTM Task Sync")
    print("=" * 50)
    
    # Scan tasks
    print("\n📁 Scanning task files...")
    tasks = TaskParser.scan_all_tasks()
    
    total_tasks = sum(len(t) for t in tasks.values())
    print(f"   Found: {len(tasks['active'])} active, {len(tasks['completed'])} completed, {len(tasks['backlog'])} backlog")
    
    if args.scan_only:
        print("\n📋 Task Summary:")
        for category, task_list in tasks.items():
            print(f"\n{category.upper()}:")
            for task in task_list[:3]:  # Show top 3
                print(f"  - {task['id']}: {task['title'][:50]} ({task['progress']}%)")
        return
    
    # Connect to database
    sync = LTMSync()
    try:
        sync.connect()
        print("\n🗄️  Connected to database")
        
        # Determine what to sync
        if args.full_sync or not any([args.update_project_memories, args.update_ltm_memory, args.update_memories, args.quick_sync]):
            args.update_project_memories = True
            args.update_ltm_memory = True
            args.update_memories = True
        
        # Execute sync
        results = []
        
        if args.update_project_memories:
            print("\n📝 Updating project_memories...")
            results.append(sync.update_project_memories(tasks))
        
        if args.update_ltm_memory:
            print("\n🧠 Updating ltm_memory...")
            results.append(sync.update_ltm_memory(tasks))
        
        if args.update_memories:
            print("\n💾 Updating memories...")
            results.append(sync.update_memories(tasks))
        
        if args.quick_sync:
            print("\n⚡ Quick sync...")
            results.append(sync.quick_sync(tasks))
        
        if args.verify:
            print("\n🔍 Verifying sync...")
            results.append(sync.verify_sync())
        
        # Summary
        print("\n" + "=" * 50)
        if all(results):
            print("✅ LTM Sync completed successfully!")
        else:
            print("⚠️  LTM Sync completed with some errors")
            
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        sync.disconnect()
        print("\n🔌 Disconnected from database")


if __name__ == "__main__":
    main()
