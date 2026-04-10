# Agent Knowledge Database Integration

Dokumentasi lengkap untuk koneksi AI Agent dengan Database Knowledge menggunakan PostgreSQL + pgvector.

## 📋 Overview

Sistem ini menyediakan koneksi antara AI Agent dengan database knowledge untuk:
- **Semantic Search** - Pencarian berbasis makna/vektor
- **RAG (Retrieval-Augmented Generation)** - Retrieval context untuk LLM
- **Multi-Source Knowledge** - File-based KB + Database KB
- **Namespace Isolation** - Multi-project support
- **Namespace Discovery** - Integrasi dengan NamespaceManager (`shared_*`)

## 🏗️ Architecture

```
┌─────────────────┐
│   AI Agent      │
│  (Legal Agent)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  AgentKnowledgeBridge       │  ← Unified Interface
│  (agents/profiles/legal/    │
│   connectors/agent_knowledge│
│   _bridge.py)               │
└────────┬────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌──────────────┐
│KBConnec│  │DBKnowledge   │
│tor     │  │Connector     │
│(File)  │  │(PostgreSQL)  │
└────────┘  └──────┬───────┘
                   │
                   ▼
           ┌───────────────┐
           │  RAG Engine   │
           └───────┬───────┘
                   │
                   ▼
           ┌───────────────┐
           │  PGVector     │
           │  (PostgreSQL) │
           └───────────────┘
```

## 🚀 Quick Start

### 1. Basic Database Connector

```python
from agents.profiles.legal.connectors import DBKnowledgeConnector

# Create connector
connector = DBKnowledgeConnector()

# Initialize
await connector.initialize()

# Add document
await connector.add_document(
    doc_id="uu_23_2014_pasal_1",
    content="Desa adalah kesatuan masyarakat hukum...",
    metadata={"type": "regulation", "year": 2014},
    namespace="legal_uu_desa"
)

# Query
result = await connector.query(
    query="apa itu desa?",
    namespace="legal_uu_desa",
    top_k=5
)

print(result.context)  # Retrieved context
print(result.sources)  # Source documents
```

### 2. Unified Knowledge Bridge

```python
from agents.profiles.legal.connectors import (
    AgentKnowledgeBridge,
    KnowledgeSource,
    get_knowledge_bridge
)

# Use singleton instance
bridge = get_knowledge_bridge()
await bridge.initialize()

# Query from multiple sources
result = await bridge.query(
    query="apa itu desa?",
    sources=[KnowledgeSource.DATABASE, KnowledgeSource.FILE_BASED],
    namespace="legal_uu_desa"
)

# Query lintas namespace (akses difilter via NamespaceManager)
result_multi_ns = await bridge.query(
    query="kewenangan desa",
    sources=[KnowledgeSource.DATABASE],
    namespaces=["shared_legal", "legal_regulations"],
    top_k=5
)

# Gabungan DB + DMS dengan filter DMS (lihat dms_connector untuk kunci filter)
result_with_dms = await bridge.query(
    query="peraturan desa",
    sources=[KnowledgeSource.DATABASE, KnowledgeSource.DMS],
    namespace="legal_regulations",
    dms_filters={"jenis_dokumen": "Undang-Undang", "tahun": "2023"},
    top_k=5
)

# Get context for LLM
llm_context = await bridge.get_context_for_llm(
    query="bagaimana desa menyelenggarakan pemerintahan?",
    namespace="legal_uu_desa"
)
```

## 📦 Components

### 1. DBKnowledgeConnector

Connector untuk PostgreSQL/pgvector database.

**Features:**
- Semantic search dengan vector similarity
- Namespace isolation
- Document CRUD operations
- Regulation document support

**Methods:**

| Method | Description |
|--------|-------------|
| `initialize()` | Initialize database connection |
| `query()` | Query knowledge base |
| `add_document()` | Add document to KB |
| `add_regulation_document()` | Add regulation with metadata |
| `search_regulations()` | Search with filters |
| `get_context_for_llm()` | Get context untuk LLM |
| `list_documents()` | List documents in namespace |
| `delete_document()` | Delete document |

### 2. AgentKnowledgeBridge

Unified interface untuk multiple knowledge sources.

**Features:**
- Query multiple sources (file + database + DMS)
- Automatic result aggregation
- Citation tracking
- Unified context assembly
- Namespace-aware query (single namespace + cross-namespace)
- Namespace discovery via NamespaceManager
- Optional `dms_filters` pada `query()` / `get_context_for_llm()` untuk mempersempit hasil DMS

**Methods:**

| Method | Description |
|--------|-------------|
| `query()` | Query multiple sources (opsional `dms_filters`) |
| `query_database()` | Query database only |
| `query_file_kb()` | Query file-based KB only |
| `query_dms()` | Query DMS only |
| `add_to_database()` | Add document to DB |
| `add_regulation()` | Add regulation to DB |
| `get_context_for_llm()` | Get optimized LLM context (opsional `dms_filters`) |
| `list_namespaces()` | List accessible namespaces |
| `get_namespace_info()` | Get metadata for one namespace |
| `verify_spm_classification()` | Verify SPM (file KB) |

### 3. KnowledgeSource Enum

```python
class KnowledgeSource(Enum):
    FILE_BASED = "file"     # File-based JSON knowledge
    DATABASE = "database"   # PostgreSQL/pgvector
    DMS = "dms"             # Document Management System
    EXTERNAL = "external"   # External APIs
    ALL = "all"            # Query all sources
```

### 4. Namespace Model & Sharing

AgentKnowledgeBridge terintegrasi dengan `NamespaceManager` untuk:
- validasi namespace query
- akses daftar namespace yang tersedia
- metadata namespace (description, tags, access, document_count)

Default shared namespace yang tersedia:
- `shared_legal`
- `shared_admin`
- `shared_tech`
- `shared_general`

Contoh:

```python
# List namespace yang dapat diakses agent
namespaces = await bridge.list_namespaces(agent_id="legal_agent")

# Ambil info detail namespace
info = await bridge.get_namespace_info("shared_legal", agent_id="legal_agent")

# Query lintas namespace untuk retrieval gabungan
context = await bridge.get_context_for_llm(
    query="prosedur administrasi desa",
    namespaces=["shared_legal", "shared_admin"],
    top_k=5,
    agent_id="legal_agent"
)
```

### 5. Filter DMS (`dms_filters`)

Parameter opsional `dms_filters: dict[str, str]` diteruskan ke `DMSKnowledgeConnector.search()` saat sumber DMS ikut di-query (`KnowledgeSource.DMS` atau `KnowledgeSource.ALL`). Kunci yang didukung antara lain: `jenis_dokumen`, `instansi`, `tahun`, `category`, `source` (sesuai implementasi `_apply_filters` di `dms_connector.py`).

## ⚙️ Configuration

### Environment Variables

```bash
# PostgreSQL Configuration
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=mcp_knowledge
PG_USER=mcp_user
PG_PASSWORD=your_password

# Embedding Configuration
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768
OLLAMA_URL=http://localhost:11434

# RAG Configuration
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
RAG_MAX_CONTEXT=4000
```

### KnowledgeConfig

```python
from knowledge.config import get_knowledge_config

config = get_knowledge_config()
print(config.database_url)
print(config.embedding_dimension)
```

## 📚 Usage Examples

### Example 1: Legal Agent Query

```python
async def legal_agent_query(question: str):
    bridge = get_knowledge_bridge()
    await bridge.initialize()
    
    # Get context
    context = await bridge.get_context_for_llm(
        query=question,
        namespace="legal_regulations",
        top_k=5
    )
    
    # Build prompt with context
    prompt = f"""Berdasarkan informasi berikut:
    
{context['context']}

Jawablah pertanyaan: {question}

Sertakan referensi yang relevan."""
    
    # Send to LLM (simulated)
    response = await call_llm(prompt)
    
    # Add citations
    if context['citations']:
        response += "\n\n📚 Referensi:\n"
        for citation in context['citations']:
            response += f"- {citation}\n"
    
    return response
```

### Example 2: Batch Document Ingestion

```python
async def ingest_regulation(regulation_data: dict):
    bridge = get_knowledge_bridge()
    await bridge.initialize()
    
    # Ingest each pasal
    for pasal in regulation_data['pasal']:
        await bridge.add_regulation(
            regulation_id=regulation_data['id'],
            title=regulation_data['title'],
            content=pasal['content'],
            regulation_type=regulation_data['type'],
            year=regulation_data['year'],
            pasal=pasal['number'],
            namespace="legal_regulations"
        )
    
    print(f"✅ Ingested {len(regulation_data['pasal'])} pasal")
```

### Example 3: Multi-Source Search

```python
async def comprehensive_search(query: str):
    bridge = get_knowledge_bridge()
    await bridge.initialize()
    
    # Search all sources
    result = await bridge.query(
        query=query,
        sources=[KnowledgeSource.ALL],
        namespace="legal_uu_desa",
        top_k=5
    )
    
    print(f"Database results: {len(result.db_results)}")
    print(f"File KB results: {len(result.file_results)}")
    print(f"DMS results: {len(result.dms_results)}")
    print(f"Citations: {result.citations}")
    
    return result
```

## 🗺️ Topologi Database RAG

Berikut adalah gambaran topologi dan alur data untuk sistem RAG yang menggunakan PostgreSQL + pgvector.

### Alur Data Ingestion (Penyimpanan)

```
Dokumen/Teks
      │
      ▼
┌───────────────────────┐
│ AgentKnowledgeBridge  │
│ (add_document)        │
└──────────┬────────────┘
           │ 1. Konten dikirim
           ▼
┌───────────────────────┐
│     RAG Engine        │
└──────────┬────────────┘
           │ 2. Minta embedding
           ▼
┌───────────────────────┐
│  Ollama Service       │
│ (nomic-embed-text)    │
└──────────┬────────────┘
           │ 3. Vector (768 dim) dikembalikan
           ▼
┌───────────────────────┐
│     RAG Engine        │
└──────────┬────────────┘
           │ 4. Simpan ke Database
           ▼
┌───────────────────────────────────────────────┐
│ PostgreSQL (DB: mcp_knowledge)                │
│                                               │
│  INSERT INTO knowledge_documents (             │
│    id, content, embedding, metadata, namespace│
│  ) VALUES (...)                               │
│                                               │
└───────────────────────────────────────────────┘
```

### Alur Data Retrieval (Pencarian)

```
Query Pengguna
      │
      ▼
┌───────────────────────┐
│ AgentKnowledgeBridge  │
│ (query)               │
└──────────┬────────────┘
           │ 1. Query dikirim
           ▼
┌───────────────────────┐
│     RAG Engine        │
└──────────┬────────────┘
           │ 2. Minta embedding untuk query
           ▼
┌───────────────────────┐
│  Ollama Service       │
│ (nomic-embed-text)    │
└──────────┬────────────┘
           │ 3. Vector query dikembalikan
           ▼
┌───────────────────────┐
│     RAG Engine        │
└──────────┬────────────┘
           │ 4. Cari di Database menggunakan vector
           ▼
┌───────────────────────────────────────────────┐
│ PostgreSQL (DB: mcp_knowledge)                │
│                                               │
│  SELECT content, metadata FROM                │
│  knowledge_documents                          │
│  WHERE namespace = ?                          │
│  ORDER BY embedding <=> query_vector LIMIT ?  │
│                                               │
└───────────────────────────────────────────────┘
           │ 5. Konteks & sumber dokumen dikembalikan
           ▼
      Hasil
```

### Struktur Tabel Inti

- **Tabel**: `knowledge_documents`
- **Indeks Vektor**: HNSW (Hierarchical Navigable Small World) untuk pencarian kemiripan kosinus (`vector_cosine_ops`) yang cepat.

```
+-------------+-------------------------+------------------------------------------+
| Nama Kolom  | Tipe Data               | Deskripsi                                |
+-------------+-------------------------+------------------------------------------+
| id          | TEXT                    | ID unik untuk dokumen (Primary Key)      |
| content     | TEXT                    | Isi teks dari dokumen yang disimpan      |
| embedding   | VECTOR(768)             | Vector embedding dari 'content'          |
| metadata    | JSONB                   | Data tambahan (mis. sumber, tipe, tahun) |
| namespace   | TEXT                    | Isolasi data antar proyek atau domain    |
| created_at  | TIMESTAMP               | Waktu pembuatan record                   |
+-------------+-------------------------+------------------------------------------+
```

## 🗄️ Database Schema

### knowledge_documents Table

```sql
CREATE TABLE knowledge_documents (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB DEFAULT '{}',
    namespace TEXT DEFAULT 'default',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_knowledge_namespace 
ON knowledge_documents(namespace);

CREATE INDEX idx_knowledge_embedding 
ON knowledge_documents 
USING hnsw (embedding vector_cosine_ops);
```

## 🔧 Prerequisites

1. **PostgreSQL dengan pgvector extension:**
   ```bash
   # Docker
   docker run -d \
     -e POSTGRES_PASSWORD=<set-in-centralized-env> \
     -p 5432:5432 \
     ankane/pgvector
   
   # Create extension
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Ollama untuk embeddings:**
   ```bash
   # Pull embedding model
   ollama pull nomic-embed-text
   
   # Verify
   ollama list
   ```

3. **Python dependencies:**
   ```bash
   pip install asyncpg pgvector
   ```

## 🧪 Testing

### Run Examples

```bash
cd /home/aseps/MCP/mcp-unified
python examples/agent_knowledge_example.py
```

### Test Database Connection

```python
import asyncio
from agents.profiles.legal.connectors import get_db_knowledge_connector

async def test_connection():
    connector = get_db_knowledge_connector()
    success = await connector.initialize()
    print(f"Connection: {'✅ OK' if success else '❌ Failed'}")
    await connector.close()

asyncio.run(test_connection())
```

## 📊 Performance Tips

1. **Use Namespaces** - Isolate projects untuk better performance
2. **Adjust top_k** - Balance antara recall dan speed
3. **Set similarity threshold** - Filter low-quality matches
4. **Use HNSW index** - Fast approximate search
5. **Batch insertions** - Reduce database round trips

## 🔒 Security Considerations

1. **Connection pooling** - Built-in asyncpg pool
2. **Namespace isolation** - Prevent cross-project access
3. **Input sanitization** - Safe query parameter handling
4. **Credential management** - Use environment variables

## 🐛 Troubleshooting

### Issue: Connection Failed
```
Error: connection refused
```
**Solution:** Check PostgreSQL running and credentials correct

### Issue: pgvector extension not found
```
Error: type "vector" does not exist
```
**Solution:** Run `CREATE EXTENSION IF NOT EXISTS vector;`

### Issue: Embedding generation failed
```
Error: embedding_generation_failed
```
**Solution:** Verify Ollama running and model available

## 📖 Further Reading

- [RAG Engine Documentation](../knowledge/rag_engine.py)
- [PGVector Store](../knowledge/stores/pgvector.py)
- [Knowledge Config](../knowledge/config.py)
- [Examples](../../examples/agent_knowledge_example.py)
