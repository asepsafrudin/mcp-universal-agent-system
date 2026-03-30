# Agent Knowledge Database Integration

Dokumentasi lengkap untuk koneksi AI Agent dengan Database Knowledge menggunakan PostgreSQL + pgvector.

## 📋 Overview

Sistem ini menyediakan koneksi antara AI Agent dengan database knowledge untuk:
- **Semantic Search** - Pencarian berbasis makna/vektor
- **RAG (Retrieval-Augmented Generation)** - Retrieval context untuk LLM
- **Multi-Source Knowledge** - File-based KB + Database KB
- **Namespace Isolation** - Multi-project support

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
- Query multiple sources (file + database)
- Automatic result aggregation
- Citation tracking
- Unified context assembly

**Methods:**

| Method | Description |
|--------|-------------|
| `query()` | Query multiple sources |
| `query_database()` | Query database only |
| `query_file_kb()` | Query file-based KB only |
| `add_to_database()` | Add document to DB |
| `add_regulation()` | Add regulation to DB |
| `get_context_for_llm()` | Get optimized LLM context |
| `verify_spm_classification()` | Verify SPM (file KB) |

### 3. KnowledgeSource Enum

```python
class KnowledgeSource(Enum):
    FILE_BASED = "file"     # File-based JSON knowledge
    DATABASE = "database"   # PostgreSQL/pgvector
    EXTERNAL = "external"   # External APIs
    ALL = "all"            # Query all sources
```

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
    print(f"Citations: {result.citations}")
    
    return result
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
