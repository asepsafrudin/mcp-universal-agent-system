# Profiling Notes - MCP Unified System

**Date:** 2026-02-25  
**Phase:** Pre-Profiling Analysis  
**Status:** 🟡 READY FOR PROFILING

---

## Baseline Results Summary

### Original Benchmark (Concurrent Load)
| Endpoint | Throughput | p95 Latency | Observations |
|----------|------------|-------------|--------------|
| `/health` | 57.96 req/s | 162.70 ms | **Slower than tools list** - investigate |
| `/tools/list` | 57.83 req/s | 75.40 ms | Baseline performance |

### Profiling Results (Sequential Requests)
| Endpoint | Avg Latency | Notes |
|----------|-------------|-------|
| `/health` | 19.08 ms | Much faster under sequential load |
| `/tools/list` | 18.82 ms | Similar to health check |

**Key Finding:** Sequential vs Concurrent performance differs significantly!
- Sequential: ~19ms (both endpoints)
- Concurrent (10 connections): 162ms vs 75ms
- **Conclusion:** Bottleneck is in concurrent handling, not endpoint logic

## Profiling Analysis Results

### Major Bottleneck Identified: SSL Context Initialization
```
100 x 1.531s = load_verify_locations (SSL context)
```
**Impact:** Each httpx client creation initializes SSL context (15ms overhead)
**Solution:** Use connection pooling / reuse HTTP clients

### Server-Side Findings
- Both endpoints perform similarly under sequential load
- No significant middleware overhead detected in profiler
- Throughput ceiling (~58 req/s) likely due to:
  1. Single worker configuration
  2. GIL contention under concurrent load
  3. HTTP client overhead in benchmark tool

---

## Critical Profiling Checkpoints

### 1. Middleware Overhead Analysis ⚠️ HIGH PRIORITY

**Hypothesis:** Auth middleware (bcrypt/JWT) running on public endpoints

**Check:**
```python
# In core/server.py - verify these endpoints are PUBLIC:
- GET /health          # Should NOT require auth
- GET /docs (dev)      # Should NOT require auth  
- GET /redoc (dev)     # Should NOT require auth
- GET /openapi.json    # Should NOT require auth (or disabled in prod)
```

**Current Status:**
- `/health` - Currently PUBLIC (no auth dependency) ✅
- `/docs`, `/redoc` - Conditional on environment ✅

**Action:** Profile middleware execution time on `/health`

### 2. Worker Strategy Analysis ⚠️ HIGH PRIORITY

**Hypothesis:** Limited workers causing throughput bottleneck at ~58 req/s

**Check Uvicorn/Gunicorn Configuration:**
```bash
# Current server startup
cat mcp-unified/run.sh
# Check for: workers, worker-class, threads
```

**Recommended Configuration:**
```python
# For CPU-bound (bcrypt/auth): workers = (2 x $num_cores) + 1
# For IO-bound (DB/network): threads = high number

# Example for 4-core machine:
workers = 9  # (2 x 4) + 1
worker_class = "uvicorn.workers.UvicornWorker"
threads = 4
```

**Action:** 
- Check current worker count
- Benchmark dengan workers = 2x cores + 1

### 3. IO-Bound vs CPU-Bound Identification ⚠️ CRITICAL

**Profiling Strategy:**

```python
# Use cProfile to identify bottlenecks
python -m cProfile -o profile.stats -m core.server

# Then analyze:
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
```

**Expected Patterns:**

| Bottleneck Type | Indicators | Solutions |
|-----------------|------------|-----------|
| **IO-Bound** | High time in `asyncio.sleep`, `socket.recv`, `file.read` | Increase concurrency, async optimization |
| **CPU-Bound** | High time in `bcrypt.checkpw`, `jwt.encode`, regex | More workers, caching, algorithm optimization |
| **Lock Contention** | High time in threading locks | Reduce shared state, connection pooling |

**Specific Functions to Profile:**
1. `get_current_user()` - JWT decode time
2. `auth_manager.authenticate_api_key()` - bcrypt verify
3. `add_correlation_id_middleware()` - logging overhead
4. `registry.list_tools()` - DB/registry queries

---

## Profiling Execution Plan

### Step 1: CPU Profiling
```bash
cd /home/aseps/MCP/mcp-unified
python -m cProfile -o health_profile.prof -c "
import asyncio
from tests.benchmark_baseline import BenchmarkRunner
runner = BenchmarkRunner()
asyncio.run(runner.benchmark_endpoint('Health Check', '/health', 100, 5))
"
```

### Step 2: Memory Profiling
```bash
pip install memory_profiler
python -m memory_profiler core/server.py
```

### Step 3: Middleware Timing
Add timing decorator to middleware:
```python
@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    start = time.time()
    # ... existing code ...
    process_time = time.time() - start
    logger.info("middleware_timing", duration=process_time, path=request.url.path)
    return response
```

---

## Target Bottlenecks

Based on baseline results, focus on:

### 🔴 High Priority
1. **Why /health is slower than /tools/list**
   - Middleware overhead investigation
   - Correlation ID generation
   - Logger overhead

2. **Throughput stuck at ~58 req/s**
   - Worker configuration
   - GIL contention (if any)
   - Event loop blocking

### 🟡 Medium Priority
3. **Auth overhead on protected endpoints**
   - bcrypt verify time
   - JWT decode time
   - Session lookup

4. **Database/registry queries**
   - Connection pooling
   - Query optimization
   - Caching opportunities

---

## Profiling Tools Setup

```bash
# Install profiling tools
cd /home/aseps/MCP/mcp-unified
pip install --user py-spy snakeviz line_profiler memory_profiler

# py-spy for live profiling
py-spy top -- python -m core.server

# snakeviz for visualizing cProfile
snakeviz profile.prof

# line_profiler for specific functions
kernprof -l -v server.py
```

---

## Success Criteria

After profiling and optimization:

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| /health p95 | 162.70 ms | < 100 ms | > 38% |
| /tools/list p95 | 75.40 ms | < 50 ms | > 34% |
| Throughput | ~58 req/s | > 200 req/s | > 245% |
| Worker Efficiency | TBD | 80%+ | - |

---

## Notes

- Baseline shows unexpected behavior: health > tools latency
- Throughput ceiling at ~58 req/s suggests worker/config issue
- Auth not applied to /health (verified in code), so bottleneck elsewhere

---

**Next Step:** Execute profiling dengan cProfile + py-spy
