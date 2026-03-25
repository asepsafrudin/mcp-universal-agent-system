# Optimization Plan - MCP Unified System

**Date:** 2026-02-25  
**Phase:** Post-Profiling Optimization  
**Status:** 🟡 READY FOR IMPLEMENTATION

---

## Executive Summary

Based on profiling results, the main bottleneck is **NOT** in the application code but in:
1. **Worker configuration** - Single worker limits throughput
2. **HTTP client overhead** - SSL context initialization in benchmark tool
3. **Concurrent load handling** - Server performs well sequentially (~19ms) but struggles under concurrent load (162ms p95)

---

## Profiling Results Summary

### Sequential vs Concurrent Performance

| Test Type | /health | /tools/list | Conclusion |
|-----------|---------|-------------|------------|
| **Sequential** | 19.08 ms | 18.82 ms | Fast, similar performance |
| **Concurrent (10 conn)** | 162.70 ms | 75.40 ms | 8x slower under load |

**Key Insight:** Server code is efficient; bottleneck is in concurrent request handling infrastructure.

---

## Optimization Priorities

### 🔴 CRITICAL - Worker Configuration

**Problem:** Throughput capped at ~58 req/s

**Root Cause:** Default Uvicorn configuration uses single worker

**Solution:**
```python
# Current (single worker)
uvicorn core.server:app --host 0.0.0.0 --port 8000

# Optimized (multiple workers)
uvicorn core.server:app --host 0.0.0.0 --port 8000 --workers 9

# Or use Gunicorn with Uvicorn workers
gunicorn core.server:app -w 9 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Expected Impact:** 
- Throughput: 58 req/s → 200+ req/s (3x improvement)
- Latency under load: Significant reduction

**Implementation:**
1. Update `run.sh` to use multiple workers
2. Make workers configurable via environment variable
3. Test with different worker counts

---

### 🟡 HIGH - Connection Keep-Alive

**Problem:** HTTP client creating new connections per request

**Root Cause:** Benchmark tool using httpx without connection pooling

**Note:** This is benchmark tool issue, not server issue. But server should support keep-alive.

**Verification:**
```bash
# Check if server supports keep-alive
curl -v http://localhost:8000/health 2>&1 | grep -i keep-alive
```

**Expected Impact:** 
- Reduced connection overhead
- Better concurrent performance

---

### 🟡 HIGH - Async Logging

**Problem:** Logging might be blocking under high load

**Current Implementation:**
```python
# In add_correlation_id_middleware
logger.info("http_request", ...)  # Potentially blocking
```

**Solution Options:**
1. **Queue-based logging** (Recommended)
```python
import asyncio
from queue import Queue

class AsyncLogger:
    def __init__(self):
        self.queue = Queue()
        self.worker = asyncio.create_task(self._process_queue())
    
    def info(self, **kwargs):
        self.queue.put(kwargs)  # Non-blocking
    
    async def _process_queue(self):
        while True:
            if not self.queue.empty():
                msg = self.queue.get()
                # Actually write to log
            await asyncio.sleep(0.01)  # Yield control
```

2. **Structlog with async processors**
```python
import structlog
structlog.configure(
    processors=[...],
    wrapper_class=structlog.asyncio.AsyncBoundLogger,
)
```

**Expected Impact:**
- Reduced latency variance
- Better throughput under load

---

### 🟢 MEDIUM - Response Caching

**Problem:** `/tools/list` returns same data repeatedly

**Solution:**
```python
from functools import lru_cache
import time

# Cache tools list for 60 seconds
@lru_cache(maxsize=1)
def get_cached_tools():
    return registry.list_tools(), time.time()

def list_tools():
    tools, cached_at = get_cached_tools()
    if time.time() - cached_at > 60:  # 60 second TTL
        get_cached_tools.cache_clear()
        tools, _ = get_cached_tools()
    return tools
```

**Expected Impact:**
- /tools/list latency: 75ms → <10ms (cached)
- Reduced registry computation

---

### 🟢 MEDIUM - JSON Serialization

**Problem:** Standard json library slower than alternatives

**Solution:**
```python
# Replace standard json with orjson
try:
    import orjson as json
except ImportError:
    import json

# In FastAPI
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)
```

**Expected Impact:**
- 2-10x faster JSON serialization
- Reduced CPU usage

---

### 🟢 LOW - UUID Generation Optimization

**Problem:** UUID generation in middleware might be slow

**Current:**
```python
cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
```

**Alternative:** Use faster UUID generation
```python
import uuid

# uuid4 is already fast, but we can use uuid1 if we don't need randomness
# Or use a simple counter + timestamp for debugging
import time
import random

def fast_id():
    return f"{int(time.time()*1000)}-{random.randint(1000,9999)}"
```

**Expected Impact:** Minimal (UUID generation is already fast)

---

## Implementation Roadmap

### Phase 1: Worker Configuration (Immediate)
- [ ] Update run.sh with multiple workers
- [ ] Add WORKERS environment variable
- [ ] Re-run benchmark to verify improvement

### Phase 2: Async Logging (Week 1)
- [ ] Implement queue-based logging
- [ ] Add async log processor
- [ ] Benchmark under high load

### Phase 3: Caching (Week 1)
- [ ] Add response caching for /tools/list
- [ ] Implement cache invalidation
- [ ] Test cache hit rates

### Phase 4: JSON Optimization (Week 2)
- [ ] Replace json with orjson
- [ ] Update FastAPI response class
- [ ] Verify no breaking changes

---

## Benchmark Targets

After optimization:

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| Throughput | 58 req/s | 200+ req/s | 🔴 Critical |
| /health p95 | 162.70 ms | < 50 ms | 🔴 Critical |
| /tools/list p95 | 75.40 ms | < 30 ms | 🟡 High |
| Concurrent Users | 10 | 100+ | 🔴 Critical |

---

## Testing Plan

1. **Single Worker Baseline**
   ```bash
   ./run_benchmark.sh
   ```

2. **Multi-Worker Test**
   ```bash
   WORKERS=9 ./run_benchmark.sh
   ```

3. **Load Test**
   ```bash
   # Gradual ramp-up
   python tests/benchmark_baseline.py --requests 5000 --concurrent 50
   ```

4. **Regression Test**
   - All existing tests must pass
   - Auth functionality verified
   - Security audit re-run

---

## Notes

- Sequential performance is already good (~19ms)
- Main issue is concurrent handling capacity
- Worker configuration will give biggest immediate improvement
- Async logging will help with latency consistency

---

**Next Action:** Implement worker configuration optimization
