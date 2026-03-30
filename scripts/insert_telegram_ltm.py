#!/usr/bin/env python3
"""
Insert Telegram Bot Activation data to LTM PostgreSQL
"""

import json
import os
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


def insert_telegram_ltm():
    """Insert Telegram Bot LTM data"""
    if not LTM_FILE.exists():
        print(f"❌ LTM file not found: {LTM_FILE}")
        return False
    
    # Read LTM file
    with open(LTM_FILE, 'r') as f:
        ltm_data = json.load(f)
    
    # Check if telegram_bot_integration exists
    telegram_data = ltm_data.get('telegram_bot_integration', {})
    telegram_activation = ltm_data.get('telegram_bot_activation_2026_03_03', {})
    
    if not telegram_activation and not telegram_data:
        print("❌ No Telegram bot data found in LTM file")
        return False
    
    # Use activation data if available, otherwise use integration data
    data_to_insert = telegram_activation if telegram_activation else {
        'status': telegram_data.get('status', 'RUNNING'),
        'timestamp': telegram_data.get('timestamp', datetime.now().isoformat()),
        'summary': telegram_data.get('summary', 'Telegram Bot MCP'),
        'bot_details': telegram_data.get('bot_details', {}),
        'configuration': telegram_data.get('configuration', {}),
        'features_enabled': telegram_data.get('features', []),
        'commands_available': telegram_data.get('commands', [])
    }
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Insert telegram bot activation
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
            'Telegram Bot MCP AI Assistant',
            data_to_insert.get('status', 'COMPLETE - BOT RUNNING'),
            data_to_insert.get('timestamp', datetime.now().isoformat()),
            Json(data_to_insert)
        ))
        
        conn.commit()
        print(f"✅ Telegram Bot LTM data inserted to PostgreSQL")
        print(f"   Session: telegram_bot_activation_2026_03_03")
        print(f"   Project: Telegram Bot MCP AI Assistant")
        print(f"   Status: {data_to_insert.get('status', 'COMPLETE')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inserting Telegram LTM: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def verify_telegram_ltm():
    """Verify Telegram LTM data"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT session_id, project, status, timestamp, updated_at
            FROM ltm_memory
            WHERE session_id LIKE '%telegram%'
            ORDER BY timestamp DESC
        """)
        
        rows = cursor.fetchall()
        print("\n📊 Telegram Bot LTM in Database:")
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
    print("🤖 Inserting Telegram Bot LTM to PostgreSQL...")
    print("=" * 50)
    
    if insert_telegram_ltm():
        print("\n🔍 Verifying...")
        verify_telegram_ltm()
        print("\n✅ Telegram Bot LTM saved successfully!")
    else:
        print("\n❌ Failed to save Telegram Bot LTM!")
