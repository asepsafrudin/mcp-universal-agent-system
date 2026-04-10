# 06-database — Database Documentation

Dokumentasi schema, migrasi, dan operasional database untuk MCP Unified Server.

## 📋 Konten

| File | Deskripsi |
|------|-----------|
| [`DATABASE_INVESTIGATION.md`](./DATABASE_INVESTIGATION.md) | Investigasi dan analisis database |
| [`memory_namespace_migration.md`](./memory_namespace_migration.md) | Migrasi schema memory namespace |
| [`agent-db-access-notes.md`](./agent-db-access-notes.md) | Catatan akses database untuk agent IDE/OpenHands |
| [`agent-db-debug-checklist.md`](./agent-db-debug-checklist.md) | Checklist debug cepat saat koneksi DB bermasalah |
| [`agent-startup-matrix.md`](./agent-startup-matrix.md) | Ringkasan agent/runtime, env, dan DB target |

## 🗄️ Database Stack

### PostgreSQL + pgvector

**Purpose**: Long-term memory dengan semantic search

**Schema**:
```sql
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    key TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    namespace TEXT NOT NULL DEFAULT 'default',
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX memories_namespace_idx ON memories (namespace);
CREATE INDEX memories_namespace_key_idx ON memories (namespace, key);
```

### Redis

**Purpose**: Working memory untuk session state

**Data Types**:
- **String**: Simple key-value
- **Hash**: Structured session data
- **List**: Task queues
- **Set**: Unique tags/categories

## 🔧 Namespace Isolation

### Schema Isolation

Setiap project menggunakan namespace terpisah:

```python
# Save memory dengan namespace
memory_save(
    key="project_config",
    content="...",
    namespace="project_alpha"
)

# Search dalam namespace
memory_search(
    query="configuration",
    namespace="project_alpha"
)
```

### Migration

Migrasi dari schema tanpa namespace:

```sql
ALTER TABLE memories ADD COLUMN namespace TEXT NOT NULL DEFAULT 'default';
CREATE INDEX memories_namespace_idx ON memories (namespace);
CREATE INDEX memories_namespace_key_idx ON memories (namespace, key);
```

📄 Detail: [`memory_namespace_migration.md`](./memory_namespace_migration.md)

## 🤖 Agent Runtime Access

Jika agent IDE atau OpenHands perlu mengakses knowledge base / PostgreSQL:

- Pastikan env runtime menyertakan `PG_HOST`, `PG_PORT`, `PG_DATABASE`, `PG_USER`, `PG_PASSWORD`, dan `DATABASE_URL`
- Jangan asumsi sandbox punya akses ke `localhost` host machine
- Gunakan resource observability `mcp://openhands/task/env-context` untuk melihat snapshot env task aktif
- Lihat juga catatan operasional di [`agent-db-access-notes.md`](./agent-db-access-notes.md)

## 📊 Investigation Results

Hasil investigasi database:

- Connection pooling
- Query optimization
- Index strategy
- Backup procedures

📄 Detail: [`DATABASE_INVESTIGATION.md`](./DATABASE_INVESTIGATION.md)

## 🚀 Operations

### Backup

```bash
# PostgreSQL backup
pg_dump -U aseps -d mcp > backup_$(date +%Y%m%d).sql

# Redis backup
redis-cli SAVE
cp /var/lib/redis/dump.rdb backup/redis_$(date +%Y%m%d).rdb
```

### Restore

```bash
# PostgreSQL restore
psql -U aseps -d mcp < backup_YYYYMMDD.sql

# Redis restore
cp backup/redis_YYYYMMDD.rdb /var/lib/redis/dump.rdb
redis-cli RESTORE
```

## 📖 Related Documentation

- **Architecture** → [`../02-architecture/`](../02-architecture/)
- **Operations** → [`../04-operations/`](../04-operations/)
- **Getting Started** → [`../01-getting-started/`](../01-getting-started/)
