import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5433")),
    "dbname": os.getenv("PG_DATABASE", "mcp_knowledge"),
    "user": os.getenv("PG_USER", "mcp_user"),
    "password": os.getenv("PG_PASSWORD", "mcp_password_2024"),
}

conn_str = " ".join([f"{k}={v}" for k, v in DB_CONFIG.items()])

with psycopg.connect(conn_str, row_factory=dict_row) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM surat_masuk_puu_internal LIMIT 1")
        row = cur.fetchone()
        print(f"Row type: {type(row)}")
        print(f"Row: {row}")
