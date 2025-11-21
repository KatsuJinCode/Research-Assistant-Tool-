# WebSocket Progress Update Incident Report

**Date:** 2025-11-17
**Issue Duration:** Multiple hours across multiple sessions
**Severity:** Critical - Complete feature failure
**Status:** RESOLVED

---

## Executive Summary

WebSocket progress updates completely failed to work despite the backend processing functioning correctly. The issue consumed hours of development time across multiple attempts, involving approximately 50+ failed fix attempts, extensive unit testing, and multiple complete rollbacks.

**Root Cause:** Missing `socketio.sleep(0)` calls in the progress callback to yield control to the eventlet event loop.

**Why It Was Hard to Find:** The symptom (no progress updates) had multiple plausible causes, and the actual root cause was a subtle async/greenthread scheduling issue that traditional debugging approaches couldn't catch.

---

## Timeline of Events

### Initial Problem
- **Symptom:** Progress bar stuck at 10%, no real-time updates
- **Reality:** Backend processing worked perfectly, data saved to Neo4j correctly
- **User Experience:** Page appeared to hang during upload, only showing results after manual refresh

### Failed Attempts (Chronological)

1. **Attempt 1-5:** Assumed WebSocket connection issue
   - Changed transport modes
   - Modified CORS settings
   - Adjusted polling intervals
   - Result: No improvement

2. **Attempt 6-15:** Assumed emit() not being called
   - Added extensive logging
   - Verified callback was invoked
   - Confirmed emit() was executing
   - Result: Logs showed emit() calls, but no client reception

3. **Attempt 16-25:** Assumed threading incompatibility
   - Changed from `threading.Thread()` to `socketio.start_background_task()`
   - This was NECESSARY but NOT SUFFICIENT
   - Result: Still no progress updates

4. **Attempt 26-35:** Created diagnostic unit tests
   - Built `test_websocket_diagnostics.py` - confirmed 0 events received
   - Built `test_callback_invoked.py` - proved callbacks work (5/5 success)
   - Built `test_eventlet_emit.py` - all patterns failed (0/0/0)
   - Built `test_fresh_minimal.py` - minimal test worked (5/5 success)
   - Built `test_client_minimal.py` - automated client verified pattern
   - Result: Proved the pattern SHOULD work, but didn't explain why production failed

5. **Attempt 36-45:** Searched documentation and web resources
   - Found Flask-SocketIO docs explaining eventlet requirements
   - User criticized adding "2024" to searches (valid point - date filtering harmful)
   - Learned about monkey patching and eventlet compatibility
   - Result: Good theory, wrong application

6. **Attempt 46-50:** Applied various eventlet fixes
   - Tried eventlet.monkey_patch() - caused errors
   - Changed to socketio.start_background_task() - insufficient alone
   - Added logging to trace event flow
   - Result: Still blocking, but didn't understand why

### The Actual Fix (Attempt 51)

**What Actually Worked:**
```python
def progress_callback(message, progress, data):
    logger.info(f"[PROGRESS {progress:.0f}%] {message}")
    socketio.sleep(0)  # Yield to eventlet event loop BEFORE emitting
    socketio.emit('processing_update', {
        'message': message,
        'progress': progress,
        'data': data
    })
    socketio.sleep(0)  # Yield AFTER emitting to allow event delivery
    logger.debug(f"Emitted processing_update: {progress:.0f}%")
```

**Key Insight from Logs:**
```
2025-11-17 12:23:00,683 - __main__ - INFO - [PROGRESS 5%] Creating document node...
2025-11-17 12:23:00,687 - __main__ - INFO - [PROGRESS 10%] Extracting text from PDF...
```
The first log appeared, but the debug log AFTER emit() never appeared. This proved emit() was blocking the greenthread.

---

## Root Cause Analysis

### The Technical Problem

**Eventlet Greenthreads vs Real Threads:**
- Eventlet uses cooperative multitasking (greenthreads)
- Greenthreads only yield control at specific points
- Blocking operations (file I/O, network calls, CPU-intensive work) don't yield automatically
- `socketio.emit()` queues the event but doesn't yield
- Without yielding, the event loop never gets a chance to actually send the event

**The Processing Pipeline:**
```
1. progress_callback() called
2. socketio.emit() queues event
3. IMMEDIATELY returns to heavy processing (AI calls, DB queries)
4. Heavy processing blocks the greenthread for 2-30 seconds
5. Event loop never gets CPU time to send queued events
6. Client never receives updates
7. Eventually processing completes
8. Event loop finally runs, sends ALL queued events at once
9. Client receives burst of updates after processing done
```

**Why `socketio.sleep(0)` Fixes It:**
- `socketio.sleep(0)` explicitly yields to the event loop
- Event loop processes queued WebSocket events
- Then returns control to the greenthread
- Allows events to be delivered DURING processing, not after

### Why Traditional Debugging Failed

1. **Logging Showed Emit Calls:**
   - Logs before emit() appeared
   - This made it seem like emit() was working
   - But logs AFTER emit() never appeared (crucial clue missed initially)

2. **Unit Tests Passed:**
   - Simple tests without blocking I/O worked fine
   - Minimal server test succeeded (5/5 messages)
   - Production had heavy blocking operations that tests didn't replicate

3. **Threading Change Seemed Right:**
   - Documentation said "use socketio.start_background_task()"
   - We did that, so assumed we were done
   - Docs didn't emphasize the need for explicit yielding

4. **Symptom Had Multiple Causes:**
   - Could be: connection issue, emit not called, client not listening, server not sending
   - Each had plausible solutions we tried
   - Real cause (greenthread scheduling) wasn't obvious

---

## What Should Have Been Done Differently

### 1. **Read ALL the Debug Logs Carefully**
**What We Missed:**
```python
logger.info(f"[PROGRESS {progress:.0f}%] {message}")  # This appeared
socketio.emit(...)
logger.debug(f"Emitted processing_update: {progress:.0f}%")  # This NEVER appeared
```

**Lesson:** When debug logging, if the log AFTER a call doesn't appear, the call is blocking or erroring silently.

### 2. **Test Production Conditions, Not Ideal Conditions**

**Bad Unit Test:**
```python
def worker():
    for i in range(5):
        socketio.sleep(1)  # Light, non-blocking delay
        socketio.emit('test_message', {'count': i})
```
This worked because there's no heavy processing blocking the greenthread.

**Good Unit Test (Should Have Built This):**
```python
def worker():
    for i in range(5):
        socketio.emit('test_message', {'count': i})
        # Simulate heavy processing that blocks
        simulate_heavy_work()  # Long AI call, DB query, etc.
```

### 3. **First Principles Debugging Checklist**

When WebSocket events don't reach client:

**Step 1: Can client receive ANY events?**
- Test with manual emit from route handler
- If works: problem is in background task
- If fails: problem is connection/client

**Step 2: Is emit() being called?**
- Add log BEFORE emit()
- Add log AFTER emit()
- If before appears but after doesn't: emit() is blocking/failing

**Step 3: Is background task running in correct context?**
- Must use `socketio.start_background_task()` not `threading.Thread()`
- Verify with test

**Step 4: Is event loop getting CPU time?**
- Add `socketio.sleep(0)` before and after emit()
- This forces cooperative yielding

**Step 5: Are events being queued but not delivered?**
- Check if events arrive in burst at end
- Indicates event loop not running during processing

### 4. **Better Search Strategy**

**What We Did Wrong:**
- Added "2024" to searches (user was right to criticize this)
- Searched for solutions before understanding the problem
- Looked for "how to fix" instead of "how does this work"

**What We Should Have Done:**
- Search: "flask-socketio eventlet cooperative multitasking"
- Search: "eventlet greenthread blocking operations"
- Search: "socketio.emit not delivering events immediately"
- Read the Flask-SocketIO docs section on "Long-Running Tasks"

### 5. **Reproduce in Minimal Environment First**

**We Did Build Minimal Tests, But:**
- They didn't include blocking operations
- They worked, so we assumed production should work
- Should have added CPU-intensive work to minimal test

**Better Approach:**
```python
# test_minimal_with_blocking.py
def worker():
    for i in range(5):
        # Emit event
        socketio.emit('update', {'progress': i})

        # Simulate blocking work (this is the key!)
        import time
        time.sleep(2)  # Blocks greenthread

        # Will this emit reach the client?
```

This would have immediately shown the problem.

---

## Prevention Strategy for Future

### For AI Assistant (Claude)

**Before Implementing Solutions:**
1. Read ALL debug output carefully - if logs after a call are missing, investigate blocking
2. Build unit tests that replicate production conditions (blocking I/O, CPU work)
3. Use first-principles debugging checklist
4. Search for "how it works" before "how to fix"
5. Don't add date filters to searches unless specifically needed

**When Stuck:**
1. Ask: "What is different between my working test and failing production?"
2. Ask: "What logs am I NOT seeing that I expect?"
3. Ask: "Am I testing the actual failure conditions or idealized conditions?"

**Red Flags to Watch For:**
- Unit tests pass but production fails → tests don't replicate production conditions
- Logs before operation appear, logs after don't → operation is blocking/failing
- Events arrive in burst at end → event loop not getting CPU during processing
- Simple examples work, complex ones don't → complexity introduces blocking

### For Development Process

**Mandatory Steps for Async/WebSocket Issues:**

1. **Log Sandwich Pattern:**
```python
logger.info("BEFORE operation")
operation()
logger.info("AFTER operation")  # If this doesn't appear, operation blocks/fails
```

2. **Production Condition Testing:**
- If production has AI calls, tests must simulate CPU-intensive work
- If production has DB queries, tests must simulate I/O blocking
- If production has file operations, tests must include them

3. **Explicit Yielding in Event Loops:**
- For eventlet: Always add `socketio.sleep(0)` around emit() calls
- For asyncio: Always `await asyncio.sleep(0)`
- For trio: Always `await trio.sleep(0)`
- Document why it's needed in comments

4. **Incremental Verification:**
```python
# Step 1: Verify emit works at all (simple route handler)
@app.route('/test-emit')
def test_emit():
    socketio.emit('test', {'data': 'hello'})
    return 'ok'

# Step 2: Verify emit works from background task (no blocking)
def simple_worker():
    socketio.emit('test', {'data': 'from worker'})

# Step 3: Add light blocking
def worker_with_sleep():
    socketio.sleep(1)
    socketio.emit('test', {'data': 'after sleep'})

# Step 4: Add heavy blocking
def worker_with_cpu():
    heavy_computation()
    socketio.emit('test', {'data': 'after CPU'})  # Will this work?
```

---

## Code Pattern: The Correct Way

### For Flask-SocketIO with Eventlet

**Starting Background Tasks:**
```python
# WRONG - Don't use threading.Thread()
thread = threading.Thread(target=worker, args=(arg1,))
thread.start()

# RIGHT - Use socketio.start_background_task()
socketio.start_background_task(worker, arg1)
```

**Emitting from Background Tasks:**
```python
# WRONG - Emit without yielding
def worker():
    socketio.emit('update', {'progress': 50})
    heavy_processing()  # Blocks greenthread, prevents event delivery

# RIGHT - Yield before and after emit
def worker():
    socketio.sleep(0)  # Yield to event loop
    socketio.emit('update', {'progress': 50})
    socketio.sleep(0)  # Yield to allow event delivery
    heavy_processing()  # Can now block safely
```

**Progress Callback Pattern:**
```python
def progress_callback(message, progress, data):
    # Log BEFORE
    logger.info(f"[PROGRESS {progress:.0f}%] {message}")

    # Yield BEFORE emit
    socketio.sleep(0)

    # Emit the event
    socketio.emit('processing_update', {
        'message': message,
        'progress': progress,
        'data': data
    })

    # Yield AFTER emit (allows delivery)
    socketio.sleep(0)

    # Log AFTER (if this doesn't appear, something is wrong!)
    logger.debug(f"Emitted processing_update: {progress:.0f}%")
```

---

## Testing Strategy

### Minimal Working Test
```python
# test_basic_emit.py
def test_basic_emit():
    """Verify emit works in simplest case"""
    def worker():
        socketio.emit('test', {'data': 'hello'})

    socketio.start_background_task(worker)
    # Verify client receives event
```

### Test With Blocking Operations
```python
# test_emit_with_blocking.py
def test_emit_during_blocking_work():
    """Verify emit works when greenthread is blocked"""
    def worker():
        for i in range(5):
            # This is the crucial test!
            socketio.sleep(0)  # Without this, test fails
            socketio.emit('test', {'count': i})
            socketio.sleep(0)

            # Simulate blocking work
            time.sleep(1)  # or: heavy_computation()

    socketio.start_background_task(worker)
    # Verify client receives events DURING processing, not after
```

### Test Production Pattern
```python
# test_production_pattern.py
def test_production_document_processing():
    """Test actual production scenario"""
    def worker():
        # Simulate real production callback
        def progress_callback(msg, pct, data):
            socketio.sleep(0)
            socketio.emit('processing_update', {
                'message': msg,
                'progress': pct,
                'data': data
            })
            socketio.sleep(0)

        # Call progress callback multiple times during heavy work
        progress_callback("Starting", 10, {})
        simulate_ai_call()  # Blocking

        progress_callback("Extracting", 50, {})
        simulate_db_queries()  # Blocking

        progress_callback("Complete", 100, {})

    socketio.start_background_task(worker)
    # Verify all progress updates received in real-time
```

---

## Key Learnings

### For WebSocket + Background Processing

1. **Eventlet is cooperative, not preemptive**
   - Greenthreads don't automatically yield
   - Must explicitly yield with `socketio.sleep(0)`

2. **Emit queues, doesn't send immediately**
   - `socketio.emit()` queues the event
   - Event loop must run to actually send
   - If greenthread never yields, events never send

3. **Blocking operations prevent event delivery**
   - AI calls, DB queries, file I/O all block
   - While blocked, event loop can't run
   - Events pile up, delivered in burst when unblocked

4. **Test with realistic blocking**
   - Simple tests without blocking will always pass
   - Must include production-like blocking operations
   - Only then can you catch scheduling issues

### For Debugging Process

1. **Log sandwich pattern catches blocking**
   - Log before and after every operation
   - Missing "after" log = blocking/error

2. **Reproduce in minimal environment**
   - But include the complexity that matters
   - For async: include blocking operations
   - For concurrency: include race conditions

3. **First principles > trial and error**
   - Understand how eventlet/greenthreads work
   - Understand cooperative vs preemptive scheduling
   - Then the fix is obvious

4. **Unit tests must match production**
   - Test success conditions AND failure conditions
   - Test ideal cases AND realistic cases
   - Test simple scenarios AND complex scenarios

---

## Cost of This Issue

**Time Wasted:** ~4-6 hours across multiple sessions
**Attempts Made:** ~51 attempts
**Tests Written:** 6 diagnostic test files
**Code Rollbacks:** 3 full rollbacks with git reset
**User Frustration:** Extreme

**Final Fix:** 2 lines of code (`socketio.sleep(0)`)

**Why So Costly:**
- Symptom was confusing (progress worked in old commits)
- Unit tests passed (but didn't test realistic conditions)
- Documentation mentioned the requirement but not prominently
- Debugging focused on wrong level (WebSocket connection, not greenthread scheduling)
- No systematic first-principles checklist

---

## Recommendations

### Immediate Actions
- ✅ Add `socketio.sleep(0)` before and after all `socketio.emit()` calls in background tasks
- ✅ Document this pattern in code comments
- ✅ Create comprehensive test with blocking operations
- ✅ Update development guidelines

### Long-term Actions
- Create debugging checklist for async/WebSocket issues
- Build template tests for common patterns (WebSocket + blocking I/O)
- Document eventlet greenthread behavior in project docs
- Add "first-principles debugging" to AI assistant guidelines

### For Future Similar Issues
1. Read ALL logs carefully (before AND after each operation)
2. Test with production-realistic conditions (blocking I/O, CPU work)
3. Use first-principles debugging checklist
4. Don't add unnecessary search filters (like year)
5. Understand the underlying async mechanism before trying fixes

---

## Conclusion

The issue was simple: missing `socketio.sleep(0)` to yield to the event loop.

The solution was 2 lines of code.

But finding it took hours because:
- We didn't carefully read debug logs (missing "after emit" log)
- We built unit tests without realistic blocking operations
- We tried solutions before understanding the async execution model
- We didn't have a systematic debugging checklist

**The lesson:** For async/event-driven code, you must understand the underlying execution model (cooperative vs preemptive scheduling, when yields happen, how event loops work). Without this foundation, you're just guessing.
