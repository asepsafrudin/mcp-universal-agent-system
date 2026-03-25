# Load Testing Plan - Phase C

**Date:** 2026-02-25  
**Phase:** C - Load Testing  
**Status:** 🟡 READY FOR EXECUTION

---

## Overview

Based on Phase B findings (single worker bottleneck at ~58 req/s), Phase C will:
1. **Stress Test** - Find system breaking point with multiple workers
2. **Scaling Test** - Determine optimal worker count (diminishing returns)
3. **Soak Test** - Memory leak detection over extended period

---

## Pre-Requisites

### 1. Worker Configuration Setup

Create test configurations for different worker counts:

```bash
# run_workers_test.sh
#!/bin/bash
# Test with different worker configurations

WORKER_COUNTS=(1 2 4 8 16)
RESULTS_FILE="docs/04-operations/scaling-test-results.json"

echo "[]" > $RESULTS_FILE

for workers in "${WORKER_COUNTS[@]}"; do
    echo "Testing with $workers workers..."
    
    # Start server with specific worker count
    MCP_ENV=development JWT_SECRET=dev-secret \
        gunicorn core.server:app -w $workers \
        -k uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 --daemon
    
    sleep 5  # Wait for server to start
    
    # Run benchmark
    python tests/benchmark_baseline.py --workers $workers --output $RESULTS_FILE
    
    # Stop server
    pkill -f gunicorn
    sleep 2
done
```

### 2. Memory Monitoring Setup

```python
# tests/soak_test.py
import psutil
import time
import asyncio
from datetime import datetime

async def monitor_memory(duration_minutes=60, interval_seconds=10):
    """Monitor memory usage during soak test."""
    process = psutil.Process()
    readings = []
    
    start_time = time.time()
    while time.time() - start_time < duration_minutes * 60:
        mem_info = process.memory_info()
        reading = {
            "timestamp": datetime.now().isoformat(),
            "rss_mb": mem_info.rss / 1024 / 1024,
            "vms_mb": mem_info.vms / 1024 / 1024,
            "percent": process.memory_percent()
        }
        readings.append(reading)
        print(f"Memory: {reading['rss_mb']:.1f} MB ({reading['percent']:.1f}%)")
        await asyncio.sleep(interval_seconds)
    
    return readings
```

---

## Test Scenarios

### 1. Scaling Test: Finding the Sweet Spot

**Objective:** Determine optimal worker count before diminishing returns

**Test Matrix:**

| Workers | Concurrent Users | Duration | Metrics |
|---------|-----------------|----------|---------|
| 1 | 10, 20, 50 | 60s | Throughput, Latency, CPU |
| 2 | 10, 20, 50 | 60s | Throughput, Latency, CPU |
| 4 | 10, 20, 50, 100 | 60s | Throughput, Latency, CPU |
| 8 | 10, 20, 50, 100 | 60s | Throughput, Latency, CPU |
| 16 | 10, 20, 50, 100 | 60s | Throughput, Latency, CPU |

**Expected Results:**
- 1 worker: ~58 req/s (baseline)
- 2 workers: ~100-116 req/s (linear scaling)
- 4 workers: ~180-232 req/s (sub-linear)
- 8 workers: ~280-350 req/s (diminishing returns start)
- 16 workers: Diminishing returns or degradation

**Success Criteria:**
- Find worker count where throughput increase < 10% per doubling
- CPU usage should be < 80% at optimal point
- Latency p95 should remain < 200ms

---

### 2. Stress Test: Breaking Point

**Objective:** Find maximum load before system failure

**Progressive Load Pattern:**
```
Ramp-up: 0 → 500 concurrent users over 5 minutes
Sustain: 500 concurrent for 5 minutes
Ramp-down: 500 → 0 over 2 minutes
```

**Monitoring Points:**
- Error rate > 1% (failure threshold)
- Latency p95 > 500ms (degradation)
- Throughput plateau or drop
- Memory usage spike

**Expected Breaking Points:**
- Auth middleware bcrypt verification (CPU intensive)
- Audit logging queue overflow
- Connection pool exhaustion

---

### 3. Soak Test: Memory Leak Detection

**Objective:** Detect memory leaks in Auth/Logging over extended period

**Test Configuration:**
- Duration: 60 minutes
- Load: Moderate (20 concurrent users, ~100 req/s)
- Endpoints: Mix of public and protected
- Monitoring: Memory every 10 seconds

**Memory Leak Indicators:**
- RSS memory growing > 10% over test period
- No memory release after GC
- Linear growth pattern

**Components to Monitor:**
1. **Auth Manager** - Session storage, key storage
2. **Audit Logger** - Event buffering, file handles
3. **JWT Verification** - Token cache (if any)
4. **Database Connections** - Connection pool

**Leak Detection Query:**
```python
def detect_memory_leak(readings):
    """Analyze memory readings for leak pattern."""
    if len(readings) < 6:  # Need at least 1 minute of data
        return False, "Insufficient data"
    
    # Calculate trend
    first_half = readings[:len(readings)//2]
    second_half = readings[len(readings)//2:]
    
    first_avg = sum(r['rss_mb'] for r in first_half) / len(first_half)
    second_avg = sum(r['rss_mb'] for r in second_half) / len(second_half)
    
    growth_percent = ((second_avg - first_avg) / first_avg) * 100
    
    if growth_percent > 10:
        return True, f"Potential leak: {growth_percent:.1f}% growth"
    elif growth_percent > 5:
        return False, f"Moderate growth: {growth_percent:.1f}% (monitor)"
    else:
        return False, f"Stable: {growth_percent:.1f}% growth"
```

---

## Load Testing Execution

### Step 1: Scaling Test

```bash
#!/bin/bash
# scaling_test.sh

echo "Starting Scaling Test..."
echo "This will test with 1, 2, 4, 8, 16 workers"
echo ""

for workers in 1 2 4 8 16; do
    echo "=== Testing with $workers workers ==="
    
    # Start server
    gunicorn core.server:app \
        -w $workers \
        -k uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --daemon \
        --pid /tmp/gunicorn.pid
    
    sleep 5
    
    # Test with increasing concurrency
    for concurrency in 10 20 50 100; do
        echo "  Testing $concurrency concurrent users..."
        python tests/benchmark_baseline.py \
            --concurrent $concurrency \
            --requests 1000 \
            --output docs/04-operations/scaling_${workers}w_${concurrency}c.json
    done
    
    # Stop server
    kill $(cat /tmp/gunicorn.pid)
    sleep 3
done

echo "Scaling test complete!"
```

### Step 2: Soak Test

```bash
#!/bin/bash
# soak_test.sh

echo "Starting 60-minute Soak Test..."
echo "Monitoring memory for leak detection"
echo ""

# Start server with 4 workers (expected optimal)
gunicorn core.server:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --daemon

# Start memory monitoring in background
python tests/soak_test.py --duration 60 &
MEMORY_PID=$!

# Run continuous load
cd /home/aseps/MCP/mcp-unified
python tests/benchmark_baseline.py \
    --mode continuous \
    --concurrent 20 \
    --duration 3600 &
LOAD_PID=$!

# Wait for completion
wait $MEMORY_PID
kill $LOAD_PID
pkill -f gunicorn

echo "Soak test complete!"
echo "Check docs/04-operations/soak-test-results.json"
```

---

## Analysis & Reporting

### Scaling Analysis

Generate report showing:
```python
import json
import matplotlib.pyplot as plt

def analyze_scaling_results():
    """Analyze scaling test results."""
    workers = [1, 2, 4, 8, 16]
    throughputs = []
    
    for w in workers:
        with open(f'docs/04-operations/scaling_{w}w_50c.json') as f:
            data = json.load(f)
            throughputs.append(data['metrics'][0]['requests_per_sec'])
    
    # Find diminishing returns point
    for i in range(1, len(throughputs)):
        improvement = (throughputs[i] - throughputs[i-1]) / throughputs[i-1] * 100
        if improvement < 50:  # Less than 50% improvement
            optimal_workers = workers[i-1]
            print(f"Optimal workers: {optimal_workers}")
            print(f"Throughput: {throughputs[i-1]:.1f} req/s")
            break
    
    return workers, throughputs
```

### Soak Test Analysis

```python
def analyze_soak_results(readings):
    """Analyze soak test for memory leaks."""
    timestamps = [r['timestamp'] for r in readings]
    memory = [r['rss_mb'] for r in readings]
    
    # Linear regression for trend
    x = range(len(memory))
    slope = np.polyfit(x, memory, 1)[0]
    
    # Convert to MB per hour
    readings_per_hour = 360  # 10-second intervals
    growth_per_hour = slope * readings_per_hour
    
    print(f"Memory growth: {growth_per_hour:.1f} MB/hour")
    
    if growth_per_hour > 50:
        return "CRITICAL: Significant memory leak detected"
    elif growth_per_hour > 20:
        return "WARNING: Moderate memory growth"
    else:
        return "OK: Stable memory usage"
```

---

## Expected Outcomes

### Phase C Success Criteria

1. **Scaling Test:**
   - ✅ Identify optimal worker count (likely 4-8 for 4-core machine)
   - ✅ Document throughput vs workers curve
   - ✅ Determine CPU saturation point

2. **Stress Test:**
   - ✅ Find breaking point (likely 200+ concurrent users)
   - ✅ Identify failure mode (CPU/IO/Memory)
   - ✅ Document recovery behavior

3. **Soak Test:**
   - ✅ No memory leaks in Auth/Logging systems
   - ✅ Stable memory usage over 60 minutes
   - ✅ No degradation in response times

### Capacity Planning Data

After Phase C, we should know:
- **Max Throughput:** XXX req/s (with optimal worker config)
- **Max Concurrent Users:** XXX before degradation
- **Optimal Workers:** X for this hardware
- **Memory Footprint:** XXX MB per worker
- **Scaling Strategy:** Horizontal vs Vertical

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Scaling Test | 2 hours | Worker optimization report |
| Stress Test | 1 hour | Breaking point analysis |
| Soak Test | 1.5 hours | Memory stability report |
| Analysis | 2 hours | Capacity planning doc |
| **Total** | **6.5 hours** | Complete load testing report |

---

## Next Actions

1. ✅ Create load testing scripts (scaling_test.sh, soak_test.sh)
2. ⏳ Run scaling test (1, 2, 4, 8, 16 workers)
3. ⏳ Run stress test to breaking point
4. ⏳ Run 60-minute soak test
5. ⏳ Analyze results and generate capacity planning report

---

**Phase C Ready for Execution**