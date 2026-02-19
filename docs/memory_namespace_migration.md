# Memory Namespace Migration Guide

**Date:** 2026-02-19  
**Status:** Schema Updated - Migration Required  
**Priority:** HIGH

---

## Overview

The memory system now supports **namespace isolation** to prevent cross-project memory contamination. This document explains the schema changes and migration steps.

---

## Schema Changes

### New Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `namespace` | TEXT | 'default' | Project/tenant identifier for isolation |

### New Indexes

```sql
-- Namespace filtering index (critical for isolation)
CREATE INDEX memories_namespace_idx ON memories (namespace);

-- Composite index for namespace + key lookups
CREATE INDEX memories_namespace_key_idx ON memories (namespace, key);
```

---

## Migration Steps

### Option 1: Automatic Migration (Recommended for Development)

The `initialize_db()` function will automatically:
1. Add the `namespace` column if not exists
2. Set default value to `'default'` for existing records
3. Create required indexes

Simply restart the application:
```bash
cd /home/aseps/MCP/mcp-unified
python3 -c "from memory.longterm import initialize_db; import asyncio; asyncio.run(initialize_db())"
```

### Option 2: Manual Migration (Recommended for Production)

Run these SQL commands with appropriate permissions:

```sql
-- Step 1: Add namespace column
ALTER TABLE memories 
ADD COLUMN IF NOT EXISTS namespace TEXT NOT NULL DEFAULT 'default';

-- Step 2: Create indexes for performance
CREATE INDEX IF NOT EXISTS memories_namespace_idx ON memories (namespace);
CREATE INDEX IF NOT EXISTS memories_namespace_key_idx ON memories (namespace, key);

-- Step 3: Verify migration
SELECT namespace, COUNT(*) 
FROM memories 
GROUP BY namespace;
```

---

## API Changes

### Updated Functions

All memory functions now accept an optional `namespace` parameter:

```python
# Save memory with namespace
await memory_save(
    key="config", 
    content="API endpoint: /api/v1",
    namespace="project_alpha"  # Isolated to this project
)

# Search within namespace
await memory_search(
    query="API endpoint",
    namespace="project_alpha",
    limit=5
)

# List memories in namespace
await memory_list(namespace="project_alpha", limit=10)

# Delete from namespace
await memory_delete(key="config", namespace="project_alpha")
```

### Default Behavior

- If `namespace` is not specified, it defaults to `"default"`
- All existing memories will be in the `"default"` namespace
- Search and list operations are **scoped to the namespace**
- Cross-namespace queries require explicit namespace specification

---

## Usage Examples

### Single Project (Default Namespace)

```python
# No changes needed for single project usage
await memory_save(key="notes", content="Meeting at 3pm")
results = await memory_search(query="meeting")
```

### Multi-Project Isolation

```python
# Project A
await memory_save(
    key="api_config", 
    content="Base URL: https://api.project-a.com",
    namespace="project_a"
)

# Project B (same key, different namespace)
await memory_save(
    key="api_config", 
    content="Base URL: https://api.project-b.com",
    namespace="project_b"
)

# Search only returns results from specified namespace
results_a = await memory_search(query="api", namespace="project_a")
# Returns: Project A's API config only

results_b = await memory_search(query="api", namespace="project_b")
# Returns: Project B's API config only
```

---

## Security Considerations

### Isolation Guarantee

- Memories are **never** leaked across namespaces
- Search operations filter by namespace
- Delete operations only affect specified namespace
- No global search across all namespaces (by design)

### Best Practices

1. **Use descriptive namespace names**:
   ```python
   namespace="client_acme_corp"
   namespace="project_ecommerce_2024"
   ```

2. **Validate namespace input**:
   ```python
   import re
   
   def sanitize_namespace(namespace: str) -> str:
       # Only allow alphanumeric, hyphen, underscore
       return re.sub(r'[^a-zA-Z0-9_-]', '', namespace)
   ```

3. **Don't use user input directly as namespace** without validation

---

## Rollback Plan

If migration causes issues:

```sql
-- Remove namespace column (data loss warning!)
ALTER TABLE memories DROP COLUMN IF EXISTS namespace;

-- Remove indexes
DROP INDEX IF EXISTS memories_namespace_idx;
DROP INDEX IF EXISTS memories_namespace_key_idx;
```

---

## Testing

After migration, verify with:

```bash
# Test namespace isolation
python3 -c "
import asyncio
from memory.longterm import memory_save, memory_search, memory_list

async def test():
    # Save to different namespaces
    await memory_save('test', 'Content A', namespace='ns_a')
    await memory_save('test', 'Content B', namespace='ns_b')
    
    # Verify isolation
    results_a = await memory_search('Content', namespace='ns_a')
    results_b = await memory_search('Content', namespace='ns_b')
    
    print(f'Namespace A results: {len(results_a[\"results\"])}')
    print(f'Namespace B results: {len(results_b[\"results\"])}')
    
    # Verify no cross-contamination
    assert len(results_a['results']) == 1
    assert len(results_b['results']) == 1
    assert results_a['results'][0]['content'] == 'Content A'
    assert results_b['results'][0]['content'] == 'Content B'
    print('All tests passed!')

asyncio.run(test())
"
```

---

## Questions?

- Review `mcp-unified/memory/longterm.py` for implementation details
- Check `SECURITY_NOTICE.md` for security context
- See `docs/review_2026-02-19.md` for migration timeline
