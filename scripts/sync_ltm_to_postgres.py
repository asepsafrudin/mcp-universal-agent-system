#!/usr/bin/env python3
"""
Sync LTM Memory from .ltm_memory.json to PostgreSQL
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

# Database config
DB_CONFIG = {
    "host": os.getenv("POSTGRES_SERVER", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5433"),
    "database": os.getenv("POSTGRES_DB", "mcp_knowledge"),
    "user": os.getenv("POSTGRES_USER", "mcp_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "")
}

LTM_FILE = Path("/home/aseps/MCP/.ltm_memory.json")


def sync_ltm_to_postgres():
    """Sync LTM data to PostgreSQL"""
    if not LTM_FILE.exists():
        print(f"❌ LTM file not found: {LTM_FILE}")
        return False
    
    # Read LTM file
    with open(LTM_FILE, 'r') as f:
        ltm_data = json.load(f)
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Extract main session data
        session_id = ltm_data.get('session_id', 'default_session')
        project = ltm_data.get('project', 'MCP Unified')
        status = ltm_data.get('status', 'ACTIVE')
        timestamp = ltm_data.get('timestamp', datetime.now().isoformat())
        
        # Prepare data for insert
        data = {
            'session_id': session_id,
            'project': project,
            'status': status,
            'timestamp': timestamp,
            'data': ltm_data
        }
        
        # Insert or update
        cursor.execute("""
            INSERT INTO ltm_memory (session_id, project, status, timestamp, data)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET
                project = EXCLUDED.project,
                status = EXCLUDED.status,
                timestamp = EXCLUDED.timestamp,
                data = EXCLUDED.data,
                updated_at = CURRENT_TIMESTAMP
        """, (session_id, project, status, timestamp, Json(ltm_data)))
        
        conn.commit()
        print(f"✅ LTM data synced to PostgreSQL")
        print(f"   Session: {session_id}")
        print(f"   Project: {project}")
        print(f"   Status: {status}")
        print(f"   Timestamp: {timestamp}")
        
        # Also insert telegram bot activation as separate entry
        if 'telegram_bot_activation_2026_03_03' in ltm_data:
            telegram_data = ltm_data['telegram_bot_activation_2026_03_03']
            cursor.execute("""
                INSERT INTO ltm_memory (session_id, project, status, timestamp, data)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE SET
                    project = EXCLUDED.project,
                    status = EXCLUDED.status,
                    timestamp = EXCLUDED.timestamp,
                    data = EXCLUDED.data,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                'telegram_bot_activation_2026_03_03',
                'Telegram Bot MCP',
                telegram_data.get('status', 'ACTIVE'),
                telegram_data.get('timestamp', datetime.now().isoformat()),
                Json(telegram_data)
            ))
            conn.commit()
            print(f"✅ Telegram bot activation synced separately")
        
        return True
        
    except Exception as e:
        print(f"❌ Error syncing LTM: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def verify_sync():
    """Verify LTM data in database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT session_id, project, status, timestamp, updated_at
            FROM ltm_memory
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        print("\n📊 LTM Database Contents:")
        print("-" * 80)
        for row in rows:
            print(f"Session: {row[0]}")
            print(f"  Project: {row[1]}")
            print(f"  Status: {row[2]}")
            print(f"  Timestamp: {row[3]}")
            print(f"  Updated: {row[4]}")
            print("-" * 80)
        
        return len(rows) > 0
        
    except Exception as e:
        print(f"❌ Error verifying: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("🔄 Syncing LTM to PostgreSQL...")
    print("=" * 50)
    
    if sync_ltm_to_postgres():
        print("\n🔍 Verifying sync...")
        verify_sync()
        print("\n✅ LTM Sync completed successfully!")
    else:
        print("\n❌ LTM Sync failed!")
        sys.exit(1)
