"""
Long-Term Memory System untuk MCP Server
PostgreSQL 16 + pgvector dengan hybrid search (semantic + keyword)
Compatible dengan psycopg v3 (async)
"""
import psycopg
import psycopg_pool
import json
import subprocess
import os
import sys
from typing import Dict, Any, List
import asyncio

# Database connection parameters
DB_PARAMS = {
    'host': 'host.docker.internal' if os.path.exists("/.dockerenv") else 'localhost',
    'dbname': 'mcp',
    'user': 'aseps',
    'password': 'secure123',
    'autocommit': True
}

# Async Connection Pool
pool = psycopg_pool.AsyncConnectionPool(min_size=2, max_size=10, kwargs=DB_PARAMS, open=False)

async def get_embedding(text: str) -> List[float]:
    """
    Dapatkan embedding via Ollama dengan fallback aman
    Returns zero vector jika Ollama tidak tersedia
    """
    try:
        # Panggil API Ollama untuk embedding
        proc = await asyncio.create_subprocess_exec(
            "curl", "-s", "http://localhost:11434/api/embeddings",
            "-d", json.dumps({
                "model": "all-minilm",
                "prompt": text[:500]  # Limit text length
            }),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            response_data = json.loads(stdout)
            return response_data.get("embedding", [0.0] * 384)
        else:
            print(f"Ollama API error: {stderr.decode()}", file=sys.stderr)
            return [0.0] * 384

    except Exception as e:
        print(f"⚠️  Embedding error: {str(e)}, menggunakan fallback", file=sys.stderr)
        return [0.0] * 384

async def memory_save(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simpan memori ke PostgreSQL dengan vector embedding
    """
    try:
        key = args["key"]
        content = args["content"]
        metadata = args.get("metadata", {})

        print(f"📝 Generating embedding for memory: {key}", file=sys.stderr)
        embedding = await get_embedding(content)

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                INSERT INTO memories (key, content, metadata, embedding)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """, (key, content, json.dumps(metadata), embedding))
                memory_id = await cur.fetchone()
                memory_id = memory_id[0]

        print(f"✅ Memory berhasil disimpan dengan ID: {memory_id}", file=sys.stderr)
        return {
            "success": True,
            "message": f"✅ Memory '{key}' disimpan ke PostgreSQL 16",
            "memory_id": str(memory_id)
        }

    except Exception as e:
        error_msg = f"Database error: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        return {"success": False, "error": error_msg}

async def memory_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cari memori dengan hybrid, semantic, atau keyword search
    """
    try:
        query = args["query"]
        limit = min(args.get("limit", 3), 10)
        strategy = args.get("strategy", "hybrid")

        query_emb = await get_embedding(query)

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                if strategy == "semantic":
                    await cur.execute("""
                    SELECT key, content, COALESCE(metadata, '{}'), created_at, (1 - (embedding <=> %s)) as score
                    FROM memories
                    ORDER BY score DESC
                    LIMIT %s
                    """, (query_emb, limit))
                elif strategy == "keyword":
                    await cur.execute("""
                    SELECT key, content, COALESCE(metadata, '{}'), created_at, ts_rank(to_tsvector('indonesian', content), websearch_to_tsquery('indonesian', %s)) AS score
                    FROM memories
                    WHERE to_tsvector('indonesian', content) @@ websearch_to_tsquery('indonesian', %s)
                    ORDER BY score DESC
                    LIMIT %s
                    """, (query, query, limit))
                else: # hybrid
                    await cur.execute("""
                    SELECT key, content, COALESCE(metadata, '{}'), created_at,
                        0.6 * (1 - (embedding <=> %s)) +
                        0.4 * ts_rank(to_tsvector('indonesian', content), websearch_to_tsquery('indonesian', %s)) AS score
                    FROM memories
                    WHERE to_tsvector('indonesian', content) @@ websearch_to_tsquery('indonesian', %s)
                       OR embedding <=> %s < 0.6
                    ORDER BY score DESC
                    LIMIT %s
                    """, (query_emb, query, query, query_emb, limit))

                results = []
                for row in await cur.fetchall():
                    metadata = row[2] if isinstance(row[2], dict) else json.loads(row[2] or "{}")
                    results.append({
                        "key": row[0],
                        "content": row[1],
                        "metadata": metadata,
                        "created_at": row[3].isoformat() if row[3] else "",
                        "score": round(float(row[4]), 3)
                    })
                return {"success": True, "results": results if results else []}
    except Exception as e:
        return {"success": False, "error": f"Search: {str(e)}"}

async def memory_list(args: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    List semua memories dengan pagination
    """
    try:
        limit = min(args.get("limit", 10) if args else 10, 50)
        offset = max(args.get("offset", 0) if args else 0, 0)

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM memories")
                total = await cur.fetchone()
                total = total[0]

                await cur.execute("""
                SELECT id, key, content, metadata, created_at
                FROM memories
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """, (limit, offset))

                memories = []
                for row in await cur.fetchall():
                    memory_id, key, content, metadata, created_at = row
                    metadata = json.loads(metadata) if isinstance(metadata, str) else metadata
                    memories.append({
                        "id": str(memory_id),
                        "key": key,
                        "content": content,
                        "metadata": metadata or {},
                        "created_at": created_at.isoformat() if created_at else None
                    })

        return {
            "success": True,
            "memories": memories,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        error_msg = f"List error: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        return {"success": False, "error": error_msg}

async def memory_delete(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hapus memori berdasarkan ID atau key
    """
    try:
        memory_id = args.get("id")
        key = args.get("key")

        if not memory_id and not key:
            return {"success": False, "error": "Either 'id' or 'key' is required"}

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                if memory_id:
                    await cur.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
                    deleted_count = cur.rowcount
                elif key:
                    await cur.execute("DELETE FROM memories WHERE key = %s", (key,))
                    deleted_count = cur.rowcount

        if deleted_count > 0:
            return {"success": True, "message": f"✅ Deleted {deleted_count} memory/ies"}
        else:
            return {"success": False, "error": "Memory not found"}

    except Exception as e:
        error_msg = f"Delete error: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        return {"success": False, "error": error_msg}