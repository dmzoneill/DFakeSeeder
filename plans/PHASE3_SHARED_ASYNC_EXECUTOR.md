# Phase 3: Shared Async Event Loop Architecture

## Problem Statement

**Current Architecture:**
- Each `PeerProtocolManager` instance creates its own thread, event loop, and ThreadPoolExecutor
- With 10 torrents @ 50 max_connections each: **510 threads, 10 event loops**
- High context switching overhead and resource waste

**Example Resource Usage:**
```
10 torrents × (1 manager thread + 50 connection workers) = 510 threads
10 separate asyncio event loops running identical operations
```

## Solution Architecture

### SharedAsyncExecutor Singleton

**Core Design:**
```python
class SharedAsyncExecutor:
    """
    Global singleton managing a shared async event loop and thread pool.

    Benefits:
    - Single event loop for all PeerProtocolManager instances
    - Global thread pool with configurable max_workers
    - Centralized task scheduling and monitoring
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        # Single dedicated thread for event loop
        self.loop_thread = None
        self.event_loop = None
        self.running = False
        self.shutdown_event = threading.Event()

        # Global thread pool with limit
        self.max_workers = 100  # Configurable
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

        # Task tracking
        self.active_tasks = {}  # manager_id -> set of tasks
        self.task_stats = {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
        }
```

**Key Methods:**

1. **`get_instance()`** - Thread-safe singleton access
2. **`start()`** - Start the global event loop in dedicated thread
3. **`stop()`** - Graceful shutdown with task cleanup
4. **`submit_coroutine(coro, manager_id)`** - Submit async task to shared loop
5. **`cancel_manager_tasks(manager_id)`** - Cancel all tasks for a manager
6. **`get_stats()`** - Thread pool and task statistics

### PeerProtocolManager Refactoring

**Changes Required:**

1. **Remove per-instance resources:**
   ```python
   # REMOVE:
   # self.manager_thread = threading.Thread(...)
   # self.connection_pool = ThreadPoolExecutor(...)
   # asyncio.new_event_loop()

   # ADD:
   self.executor = SharedAsyncExecutor.get_instance()
   self.manager_id = f"{info_hash.hex()[:16]}"
   self.manager_task = None
   ```

2. **Refactor start() method:**
   ```python
   def start(self):
       """Start peer protocol manager using shared executor"""
       if self.running:
           return

       self.running = True

       # Submit async loop to shared executor
       self.manager_task = self.executor.submit_coroutine(
           self._async_manager_loop(),
           manager_id=self.manager_id
       )

       logger.info(f"Started PeerProtocolManager via SharedAsyncExecutor")
   ```

3. **Refactor stop() method:**
   ```python
   def stop(self):
       """Stop peer protocol manager"""
       if not self.running:
           return

       self.running = False

       # Cancel all tasks for this manager
       self.executor.cancel_manager_tasks(self.manager_id)

       # Close all active connections
       with self.lock:
           for connection in self.active_connections.values():
               connection.close()
           self.active_connections.clear()
   ```

4. **Keep _async_manager_loop() unchanged** - It already uses async/await properly

### Implementation Plan

**File Structure:**
```
d_fake_seeder/domain/torrent/
├── shared_async_executor.py          # NEW - Singleton executor
├── peer_protocol_manager.py          # MODIFIED - Use shared executor
└── global_peer_manager.py            # MODIFIED - Start/stop executor
```

**Step-by-step Implementation:**

1. **Create `shared_async_executor.py`:**
   - Implement singleton pattern with thread-safe initialization
   - Create dedicated thread for event loop
   - Implement task submission and cancellation
   - Add statistics tracking

2. **Refactor `peer_protocol_manager.py`:**
   - Remove thread creation (lines 64, 135-136)
   - Remove event loop creation (line 196)
   - Replace ThreadPoolExecutor with shared pool (line 55)
   - Update start() and stop() methods
   - Add manager_id for task tracking

3. **Update `global_peer_manager.py`:**
   - Start SharedAsyncExecutor in __init__
   - Stop SharedAsyncExecutor in stop()
   - Optional: Add executor stats to global stats

4. **Update `config/default.json`:**
   ```json
   "shared_async_executor": {
     "max_workers": 100,
     "task_timeout_seconds": 30.0,
     "shutdown_timeout_seconds": 5.0,
     "stats_enabled": true
   }
   ```

### Expected Performance Impact

**Thread Reduction:**
```
BEFORE: 10 torrents × (1 + 50) = 510 threads
AFTER:  1 executor thread + 100 global workers = 101 threads
REDUCTION: 80% fewer threads (409 threads saved)
```

**Event Loop Reduction:**
```
BEFORE: 10 separate event loops
AFTER:  1 shared event loop
REDUCTION: 90% reduction in loop overhead
```

**Estimated CPU Impact:**
- Context switching reduction: 70-80%
- Memory footprint reduction: 60-70%
- **Total CPU reduction: 20-40%** (additional to Phase 2's 31-58%)

### Risks and Mitigation

**Risk 1: Single event loop bottleneck**
- Mitigation: Event loop only schedules I/O, actual work in thread pool
- Async operations are I/O-bound, not CPU-bound

**Risk 2: One manager's heavy load affects others**
- Mitigation: Task timeouts and priority scheduling
- Per-manager task limits

**Risk 3: Shutdown complexity**
- Mitigation: Aggressive timeouts and forced cleanup
- Task cancellation with grace period

**Risk 4: Debugging becomes harder**
- Mitigation: Comprehensive logging with manager_id tagging
- Statistics tracking per manager

### Testing Strategy

1. **Unit Tests:**
   - SharedAsyncExecutor singleton behavior
   - Task submission and cancellation
   - Graceful shutdown

2. **Integration Tests:**
   - Multiple PeerProtocolManagers using shared executor
   - Concurrent start/stop operations
   - Resource cleanup verification

3. **Performance Tests:**
   - Thread count monitoring
   - CPU usage measurement
   - Context switching metrics

4. **Stress Tests:**
   - 100+ active torrents
   - Rapid start/stop cycles
   - Network error scenarios

### Rollback Plan

If Phase 3 causes issues:

1. **Immediate rollback:** Revert to Phase 2 (commit a05c532)
2. **Partial rollback:** Keep SharedAsyncExecutor but make it optional via config
3. **Gradual migration:** Support both modes, migrate torrents one-by-one

**Config flag for rollback:**
```json
"peer_protocol": {
  "use_shared_executor": true  // Set to false to use old per-instance threads
}
```

### Success Metrics

**Primary Metrics:**
- Thread count reduced by 70-85%
- CPU usage reduced by 20-40%
- Memory usage reduced by 50-70%

**Secondary Metrics:**
- No increase in connection latency
- No reduction in successful peer connections
- Shutdown time remains < 2 seconds

**Monitoring:**
- Add executor stats to status bar
- Log thread pool saturation warnings
- Track task submission/completion rates

### Timeline Estimate

- **Week 1:** Implement SharedAsyncExecutor + unit tests
- **Week 2:** Refactor PeerProtocolManager + integration tests
- **Week 3:** Testing, optimization, documentation

**Total: ~2-3 weeks** (as estimated in original audit)
