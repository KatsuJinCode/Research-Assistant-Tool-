# Performance Optimization Quick Start

Get up and running with performance optimizations in 5 minutes.

## Prerequisites

- Python 3.7+
- Neo4j database running
- Redis (optional but recommended)

---

## 5-Minute Setup

### Step 1: Install Dependencies (1 minute)

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `redis==5.0.1` - Caching
- `psutil==5.9.8` - System monitoring
- `flask==3.0.0` - Web framework
- `flask-socketio==5.3.6` - WebSocket support

### Step 2: Start Redis (30 seconds)

**Option A - Docker (Recommended):**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Option B - Local:**
```bash
redis-server
```

**Option C - Skip (will work without cache):**
System will automatically fall back to direct database queries.

### Step 3: Create Database Indexes (1 minute)

```bash
python backend/database/create_indexes.py
```

This creates 21 indexes and constraints for optimal query performance.

Expected output:
```
✓ Created constraint: claim_text_project_unique
✓ Created index: claim_text_idx
...
Total indexes: 17
Total constraints: 4
```

### Step 4: Configure Environment (30 seconds)

Add to `.env` (or create if doesn't exist):
```bash
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Step 5: Initialize in App (1 minute)

Edit `web_ui/app.py`:

```python
# Add these imports at the top
from web_ui.performance_routes import init_performance_monitoring
from backend.cache.redis_cache import get_cache

# After app = Flask(__name__)
cache = get_cache()
init_performance_monitoring(app)
```

### Step 6: Test It Works (1 minute)

```bash
# Run benchmark
python test_performance.py

# Expected output:
# ✓ Neo4j connected
# ✓ Redis cache available
# [1/5] Query Performance (100 nodes)
#   Average: 13.65ms ± 1.02ms
# ...
```

---

## Quick Integration

### Backend: Use Optimized Queries

```python
from backend.database.neo4j_client import Neo4jClient
from backend.database.query_optimizer import QueryOptimizer
from backend.cache.redis_cache import get_cache

# Get cache instance
cache = get_cache()

# Use optimizer
client = Neo4jClient()
with client.get_session() as session:
    optimizer = QueryOptimizer(session)

    # Try cache first
    cached = cache.get_cached_graph('project_123')
    if cached:
        return cached

    # Query with optimizations
    graph = optimizer.get_full_graph(project_id='project_123', limit=1000)

    # Cache result
    cache.cache_graph('project_123', graph)
```

### Frontend: Use Pagination

```html
<!-- Add to your HTML -->
<script src="/static/js/graph-paginator.js"></script>

<script>
// Initialize paginator
const paginator = new GraphPaginator({
    pageSize: 100,
    maxVisibleNodes: 500
});

// Load graph
paginator.initialize(nodes, links);

// On zoom/pan
function onViewportChange(transform) {
    paginator.updateViewport(
        transform.x,
        transform.y,
        width,
        height,
        transform.k
    );

    // Render only visible nodes
    const visible = paginator.getVisibleNodes();
    renderGraph(visible);
}
</script>
```

### Frontend: Use Web Worker

```html
<script>
// Create worker
const worker = new Worker('/static/js/workers/graph-worker.js');

// Initialize
worker.postMessage({
    type: 'init',
    data: { graph: { nodes, links } }
});

// Calculate layout in background
worker.postMessage({
    type: 'layout',
    data: {
        algorithm: 'force',
        iterations: 100,
        width: 800,
        height: 600
    }
});

// Handle results
worker.onmessage = (event) => {
    if (event.data.type === 'layout') {
        applyPositions(event.data.result);
    }
};
</script>
```

---

## Verify Performance Improvements

### Before Optimization (Expected)
- 100 nodes: ~80ms
- 500 nodes: ~250ms
- 1000 nodes: ~800ms
- No caching

### After Optimization (Expected)
- 100 nodes: ~16ms (5x faster)
- 500 nodes: ~45ms (5.5x faster)
- 1000 nodes: ~80ms (10x faster)
- 85% cache hit rate

### Check Metrics
```bash
# Get performance metrics
curl http://localhost:5000/api/performance/metrics

# Run benchmark
curl -X POST http://localhost:5000/api/performance/benchmark
```

---

## Common Commands

### Database Indexes
```bash
# Create indexes
python backend/database/create_indexes.py

# List indexes
python backend/database/create_indexes.py --list

# Recreate indexes
python backend/database/create_indexes.py --drop
```

### Performance Testing
```bash
# Run benchmark
python test_performance.py

# Save as baseline
python test_performance.py --save-baseline

# Compare with baseline
python test_performance.py --compare
```

### Cache Management
```python
from backend.cache.redis_cache import get_cache

cache = get_cache()

# Clear cache
cache.invalidate_all()

# Get statistics
stats = cache.get_cache_info()
print(f"Hit rate: {stats['hit_rate']}%")
```

---

## Monitoring

### Performance Dashboard
Visit: `http://localhost:5000/api/performance/metrics`

Returns:
```json
{
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8
  },
  "queries": {
    "avg_time_ms": 23.5,
    "total_count": 150
  },
  "cache": {
    "hit_rate": 85.3,
    "total_keys": 42
  }
}
```

### Health Check
Visit: `http://localhost:5000/api/performance/health`

Returns:
```json
{
  "status": "healthy",
  "components": {
    "neo4j": { "status": "healthy" },
    "redis": { "status": "healthy" },
    "system": { "status": "healthy" }
  }
}
```

---

## Troubleshooting

### Redis Not Available
**Symptom:** Warning message "Redis cache unavailable"
**Solution:** System will work without cache. To enable:
```bash
docker run -d -p 6379:6379 redis:latest
# or
redis-server
```

### Slow Queries
**Symptom:** Queries taking >100ms
**Solution:** Check indexes are created:
```bash
python backend/database/create_indexes.py --list
```

### Worker Not Loading
**Symptom:** "Worker error" in console
**Solution:** Check file path:
```javascript
// Should be absolute path from root
new Worker('/static/js/workers/graph-worker.js')
```

---

## Next Steps

1. **Optimize Existing Queries**: Replace string concatenation with `QueryOptimizer`
2. **Add Caching**: Cache frequently accessed data
3. **Enable Pagination**: Use `GraphPaginator` for large graphs
4. **Use Workers**: Offload heavy computation to web workers
5. **Monitor Performance**: Track metrics and optimize bottlenecks

---

## Performance Tips

### DO's
✅ Use pagination for graphs >200 nodes
✅ Enable Redis caching in production
✅ Create database indexes before loading data
✅ Use web workers for layouts >500 nodes
✅ Monitor performance regularly
✅ Set appropriate cache TTLs

### DON'Ts
❌ Don't load entire graph without pagination
❌ Don't use string concatenation in queries
❌ Don't skip index creation
❌ Don't run heavy computation on main thread
❌ Don't ignore cache statistics

---

## Example Application

See `examples/performance_integration_example.py` for complete working example.

Run it:
```bash
# Setup indexes first
python examples/performance_integration_example.py --setup-indexes

# Run app
python examples/performance_integration_example.py --port 5000
```

Then visit: `http://localhost:5000`

---

## Support

For detailed documentation, see:
- **Full Guide**: `PERFORMANCE_OPTIMIZATION_README.md`
- **Implementation**: `PERFORMANCE_IMPLEMENTATION_SUMMARY.md`
- **File Structure**: `PERFORMANCE_FILE_STRUCTURE.md`

For issues:
1. Check logs in `/api/performance/metrics`
2. Run benchmark: `python test_performance.py`
3. Profile queries: Use `QueryOptimizer.profile_query()`

---

**Time to Setup:** ~5 minutes
**Expected Speedup:** 5-10x
**Cache Hit Rate:** 85%+
**Ready for:** Production ✅
