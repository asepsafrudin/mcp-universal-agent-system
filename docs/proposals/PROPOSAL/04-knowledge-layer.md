# 04 - Knowledge Layer

**RAG Implementation: pgvector PRIMARY + Zvec CACHE + Versioning**

---

## 1. Store Architecture

### 1.1 Primary-Cache Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE MANAGER                         │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Write Path                                         │   │
│  │  ┌─────────┐    ┌─────────────┐    ┌─────────┐     │   │
│  │  │ Ingest  │───→│  pgvector   │───→│  Query  │     │   │
│  │  │ Document│    │  (PRIMARY)  │    │  Result │     │   │
│  │  └─────────┘    └──────┬──────┘    └─────────┘     │   │
│  │                        │                          │   │
│  │              Async Warm Cache                      │   │
│  │                        ▼                          │   │
│  │                 ┌─────────────┐                   │   │
│  │                 │    Zvec     │                   │   │
│  │                 │   (CACHE)   │                   │   │
│  │                 └─────────────┘                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Read Path:                                                  │
│  1. Query Zvec cache (fast, local)                          │
│  2. Cache miss → Query pgvector (authoritative)             │
│  3. Warm cache dengan hasil query                           │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Configuration

```yaml
# config/knowledge.yaml
knowledge:
  stores:
    # PRIMARY: PostgreSQL (proven ACID durability)
    primary:
      type: pgvector
      host: "${POSTGRES_SERVER}"
      database: "${POSTGRES_DB}"
      table: "knowledge_vectors"
      embedding_dim: 768
      max_vectors: 10_000_000      # ~10M vectors supported
      max_size_gb: 100
      concurrent_connections: 20
    
    # CACHE: Alibaba Zvec (local, low-latency)
    cache:
      type: zvec
      path: "./cache/knowledge.zvec"
      embedding_dim: 768
      max_vectors: 100_000         # ~100K hot vectors
      ttl_hours: 24                # Auto-expire
      fallback_on_miss: true
    
  cache:
    enabled: true
    warmup_strategy: "async"      # Pre-populate cache on startup
    invalidation: "ttl"           # TTL-based invalidation
    
  failover:
    enabled: true
    auto_switch: false            # Don't auto-switch; cache is optional
    health_check_interval: 30
```

---

## 2. KnowledgeManager Implementation

```python
# knowledge/manager.py
import asyncio
from typing import Optional, List, Dict, Any
from knowledge.stores.pgvector import PgvectorStore
from knowledge.stores.zvec import ZvecStore
from knowledge.cache.warmer import CacheWarmer
from observability.logger import logger


class KnowledgeManager:
    """
    Dual-store knowledge manager with cache pattern.
    - pgvector: PRIMARY (authoritative source)
    - Zvec: CACHE (performance optimization)
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.primary: Optional[PgvectorStore] = None
        self.cache: Optional[ZvecStore] = None
        self._cache_lock = asyncio.Lock()  # ⭐ Thread-safe cache ops
        self._cache_available = False
        
    async def initialize(self):
        """Initialize both stores."""
        # Initialize PRIMARY (PostgreSQL) - required
        primary_config = self.config["stores"]["primary"]
        self.primary = PgvectorStore(
            host=primary_config["host"],
            database=primary_config["database"],
            table=primary_config.get("table", "knowledge_vectors"),
            embedding_dim=primary_config["embedding_dim"],
            max_connections=primary_config.get("concurrent_connections", 20)
        )
        await self.primary.initialize()
        logger.info("knowledge_primary_initialized", 
                   store="pgvector",
                   max_vectors=primary_config.get("max_vectors"))
        
        # Initialize CACHE (Zvec) - optional but recommended
        try:
            cache_config = self.config["stores"]["cache"]
            self.cache = ZvecStore(
                db_path=cache_config["path"],
                embedding_dim=cache_config["embedding_dim"],
                max_vectors=cache_config.get("max_vectors", 100_000)
            )
            await self.cache.connect()
            self._cache_available = True
            
            # Warm cache if enabled
            if self.config.get("cache", {}).get("warmup_strategy") == "async":
                asyncio.create_task(self._warm_cache())
            
            logger.info("knowledge_cache_initialized", 
                       store="zvec",
                       max_vectors=cache_config.get("max_vectors"))
        except Exception as e:
            logger.warning("knowledge_cache_unavailable", 
                          error=str(e),
                          fallback="primary_only")
    
    async def ingest(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Ingest documents to PRIMARY (pgvector).
        Cache will be warmed asynchronously.
        """
        # Always write to PRIMARY
        result = await self.primary.upsert(documents, namespace)
        logger.info("ingest_primary_success", 
                   count=len(documents), 
                   namespace=namespace)
        
        # Async cache warm if available
        if self._cache_available and self.cache:
            asyncio.create_task(
                self._warm_cache_with_documents(documents, namespace)
            )
        
        return {
            "success": True,
            "store": "primary",
            "count": len(documents),
            "namespace": namespace
        }
    
    async def query(
        self,
        query_text: str,
        namespace: str = "default",
        top_k: int = 5,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query dengan cache-first strategy.
        1. Try cache (Zvec) - fast, local
        2. Cache miss → query primary (pgvector)
        3. Warm cache dengan hasil
        """
        results = []
        
        # 1. Try cache first if available
        if use_cache and self._cache_available and self.cache:
            try:
                results = await self.cache.search(
                    query_text, namespace, top_k
                )
                if results:
                    logger.debug("cache_hit", 
                               query=query_text[:50],
                               results=len(results))
                    return results
                logger.debug("cache_miss", query=query_text[:50])
            except Exception as e:
                logger.warning("cache_query_failed", error=str(e))
        
        # 2. Query primary (authoritative)
        try:
            results = await self.primary.search(
                query_text, namespace, top_k
            )
            logger.debug("primary_query_success", 
                       results=len(results))
        except Exception as e:
            logger.error("primary_query_failed", error=str(e))
            raise KnowledgeError(f"Query failed: {str(e)}")
        
        # 3. Warm cache dengan hasil (fire-and-forget)
        if self._cache_available and results:
            asyncio.create_task(
                self._warm_cache_with_results(results, namespace)
            )
        
        return results
    
    async def _warm_cache(self):
        """Pre-populate cache dengan hot data."""
        # Implementation: Query recent/popular documents dari primary
        # dan masukkan ke cache
        pass
    
    async def _warm_cache_with_documents(
        self,
        documents: List[Dict],
        namespace: str
    ):
        """Add newly ingested documents to cache."""
        if not self.cache:
            return
        try:
            await self.cache.upsert(documents, namespace)
        except Exception as e:
            # ✅ FIXED: Log error, don't silent fail
            logger.error("cache_warm_failed", 
                        error=str(e),
                        namespace=namespace,
                        doc_count=len(documents))
    
    async def _warm_cache_with_results(
        self,
        results: List[Dict],
        namespace: str
    ):
        """Add query results to cache untuk future hits."""
        if not self.cache:
            return
        try:
            await self.cache.upsert(results, namespace)
        except Exception as e:
            logger.debug("cache_warm_failed", error=str(e))
```

---

## 3. Store Implementations

### 3.1 PgvectorStore (PRIMARY)

```python
# knowledge/stores/pgvector.py
import psycopg_pool
from typing import List, Dict, Any, Optional

class PgvectorStore:
    """
    PostgreSQL + pgvector as PRIMARY knowledge store.
    Proven ACID durability, concurrent access, enterprise-grade.
    """
    
    def __init__(
        self,
        host: str,
        database: str,
        table: str = "knowledge_vectors",
        embedding_dim: int = 768,
        max_connections: int = 20
    ):
        self.host = host
        self.database = database
        self.table = table
        self.embedding_dim = embedding_dim
        self.max_connections = max_connections
        self.pool: Optional[psycopg_pool.AsyncConnectionPool] = None
    
    async def initialize(self):
        """Initialize connection pool dan schema."""
        self.pool = psycopg_pool.AsyncConnectionPool(
            f"host={self.host} dbname={self.database}",
            min_size=5,
            max_size=self.max_connections
        )
        await self._create_schema()
    
    async def _create_schema(self):
        """Create pgvector extension dan table."""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table} (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        namespace TEXT NOT NULL DEFAULT 'default',
                        key TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB,
                        embedding vector({self.embedding_dim}),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(namespace, key)
                    )
                """)
                # Index untuk semantic search
                await cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self.table}_embedding_idx
                    ON {self.table} USING hnsw (embedding vector_cosine_ops)
                """)
    
    async def upsert(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """Insert atau update documents."""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                for doc in documents:
                    await cur.execute(f"""
                        INSERT INTO {self.table} 
                            (namespace, key, content, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (namespace, key) DO UPDATE SET
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding,
                            created_at = CURRENT_TIMESTAMP
                    """, (
                        namespace,
                        doc["key"],
                        doc["content"],
                        doc.get("metadata", {}),
                        doc.get("embedding")  # Pre-computed vector
                    ))
        return {"success": True, "upserted": len(documents)}
    
    async def search(
        self,
        query: str,
        namespace: str = "default",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Semantic search dengan cosine similarity."""
        # Get query embedding (via external service)
        query_embedding = await self._get_embedding(query)
        
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"""
                    SELECT key, content, metadata, 
                           (1 - (embedding <=> %s::vector)) as score
                    FROM {self.table}
                    WHERE namespace = %s
                    ORDER BY score DESC
                    LIMIT %s
                """, (query_embedding, namespace, top_k))
                
                results = []
                for row in await cur.fetchall():
                    results.append({
                        "key": row[0],
                        "content": row[1],
                        "metadata": row[2],
                        "score": float(row[3])
                    })
                return results
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector via external service (Ollama/OpenAI)."""
        # Delegated to embedding module
        from knowledge.embeddings.ollama import get_embedding
        return await get_embedding(text)
```

### 3.2 ZvecStore (CACHE)

```python
# knowledge/stores/zvec.py
from typing import List, Dict, Any, Optional

class ZvecStore:
    """
    Alibaba Zvec as local CACHE.
    Fast, low-latency, optional component.
    """
    
    def __init__(
        self,
        db_path: str,
        embedding_dim: int = 768,
        max_vectors: int = 100_000
    ):
        self.db_path = db_path
        self.embedding_dim = embedding_dim
        self.max_vectors = max_vectors
        self._client = None
    
    async def connect(self):
        """Initialize Zvec local database."""
        try:
            import zvec
            self._client = zvec.LocalDB(
                path=self.db_path,
                dim=self.embedding_dim
            )
        except ImportError:
            raise RuntimeError("Zvec not installed. Run: pip install zvec")
    
    async def upsert(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = "default"
    ) -> None:
        """Add documents to cache dengan namespace."""
        # Check cache size limit
        current_count = self._client.count()
        if current_count + len(documents) > self.max_vectors:
            # Evict oldest entries (LRU)
            self._evict_oldest(len(documents))
        
        for doc in documents:
            self._client.add(
                id=f"{namespace}:{doc['key']}",
                text=doc["content"],
                metadata={
                    "namespace": namespace,
                    **doc.get("metadata", {})
                }
            )
    
    async def search(
        self,
        query: str,
        namespace: str = "default",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search dalam cache dengan namespace filter."""
        results = self._client.search(
            query=query,
            top_k=top_k * 2,  # Over-fetch untuk filter
            filter={"namespace": namespace}
        )
        
        # Filter dan format
        filtered = []
        for r in results:
            if r.metadata.get("namespace") == namespace:
                filtered.append({
                    "key": r.id.replace(f"{namespace}:", ""),
                    "content": r.text,
                    "metadata": r.metadata,
                    "score": r.score
                })
                if len(filtered) >= top_k:
                    break
        
        return filtered
    
    def _evict_oldest(self, count: int):
        """Remove oldest entries untuk make room."""
        # Zvec-specific eviction logic
        pass
```

---

## 4. Knowledge Versioning

```python
# knowledge/versioning/manager.py
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class KnowledgeVersion:
    version_id: str           # e.g., "hukum-perdata:v2.1.0"
    base_version: Optional[str]
    created_at: str
    created_by: str
    change_summary: str
    document_count: int
    vector_count: int

class VersionedKnowledgeBase:
    """
    Git-like versioning untuk knowledge bases.
    Critical untuk dokumen hukum yang berubah (revisi UU, putusan baru).
    """
    
    def __init__(self, store: PgvectorStore):
        self.store = store
    
    async def create_version(
        self,
        namespace: str,
        summary: str,
        created_by: str = "system"
    ) -> KnowledgeVersion:
        """
        Create immutable snapshot dari current knowledge base.
        """
        version_id = f"{namespace}:{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Get current stats
        stats = await self._get_namespace_stats(namespace)
        
        # Create version metadata table entry
        version = KnowledgeVersion(
            version_id=version_id,
            base_version=await self._get_current_version(namespace),
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            change_summary=summary,
            document_count=stats["documents"],
            vector_count=stats["vectors"]
        )
        
        # Copy current vectors ke versioned table
        await self._snapshot_namespace(namespace, version_id)
        
        return version
    
    async def rollback(
        self,
        namespace: str,
        version_id: str
    ) -> bool:
        """
        Rollback knowledge base ke specific version.
        ⚠️ Destructive operation - backup dulu!
        """
        # 1. Verify version exists
        version = await self._get_version_metadata(version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found")
        
        # 2. Backup current state
        await self.create_version(
            namespace,
            f"Pre-rollback backup before restoring {version_id}"
        )
        
        # 3. Restore dari versioned snapshot
        await self._restore_snapshot(namespace, version_id)
        
        return True
    
    async def diff(
        self,
        namespace: str,
        version_a: str,
        version_b: str
    ) -> Dict[str, Any]:
        """
        Compare dua versi knowledge base.
        Returns: added, removed, modified documents.
        """
        docs_a = await self._get_version_documents(namespace, version_a)
        docs_b = await self._get_version_documents(namespace, version_b)
        
        keys_a = {d["key"] for d in docs_a}
        keys_b = {d["key"] for d in docs_b}
        
        return {
            "added": list(keys_b - keys_a),
            "removed": list(keys_a - keys_b),
            "common": list(keys_a & keys_b)
        }
```

---

## 5. Benchmarks & Capacity Planning

### 5.1 Store Comparison

| Metric | pgvector (PRIMARY) | Zvec (CACHE) |
|--------|-------------------|--------------|
| **Max vectors** | 10M+ | ~100K (comfortable) |
| **Query latency** | 10-50ms (network) | 1-5ms (local) |
| **Durability** | ✅ ACID transactions | ⚠️ Single file |
| **Concurrent access** | ✅ Yes | ❌ No |
| **Offline capability** | ❌ No | ✅ Yes |
| **Backup** | Automated (PostgreSQL) | Manual copy |
| **Use case** | Authoritative source | Hot data cache |

### 5.2 Sizing Guidelines

```python
# Knowledge base sizing estimates

# Small (Startup/Law Firm Small)
- Documents: 1,000 - 10,000
- Vectors: 10K - 100K
- Storage: 100MB - 1GB
- Config: pgvector primary only, no cache needed

# Medium (Enterprise/Agency)
- Documents: 10,000 - 100,000
- Vectors: 100K - 1M
- Storage: 1GB - 10GB
- Config: pgvector primary + Zvec cache (hot 100K)

# Large (Government/Enterprise)
- Documents: 100,000+
- Vectors: 1M - 10M
- Storage: 10GB - 100GB
- Config: pgvector primary (sharded) + Zvec cache per shard
```

---

## 6. Cross-References

- Lihat `03-core-components.md` untuk base classes
- Lihat `05-skills-layer.md` untuk skill yang menggunakan knowledge
- Lihat `07-domain-examples.md` untuk use cases konkret

---

**Prev:** [03-core-components.md](03-core-components.md)  
**Next:** [05-skills-layer.md](05-skills-layer.md)
