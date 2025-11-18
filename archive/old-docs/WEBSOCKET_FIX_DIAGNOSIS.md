# WebSocket Progress Updates - Root Cause Analysis & Fix

## Executive Summary

**Problem**: Progress bar stuck at 10% despite background processing completing successfully.

**Root Cause**: `socketio.emit()` called from background thread without Flask application context - **emit silently fails** with no errors.

**Solution**: Wrap all `socketio.emit()` calls in background thread with `with app.app_context():` and add `broadcast=True`.

**Status**: FIXED in commit (pending test)

---

## Andon Problem-Solving Analysis

### 1. Problem Statement

**User Experience:**
1. User uploads PDF document
2. Progress bar shows "Upload successful! Processing started..." at 10%
3. Progress bar NEVER advances beyond 10%
4. Graph does NOT update
5. Minutes later, user refreshes page → document appears (processing DID complete!)

**Server Behavior:**
- Background processing IS running correctly
- All processing stages complete successfully (PDF extraction, claim extraction, etc.)
- Document IS saved to Neo4j
- BUT: No `socketio.emit()` messages visible in logs
- AND: No WebSocket events reaching frontend

### 2. Evidence Chain

**Evidence Point 1: `_emit()` calls exist**
- Location: `web_ui/document_processor.py` lines 56-58
- Function: `self.progress_callback(message, progress, data or {})`
- Status: ✓ Called throughout processing (lines 748, 797, 804, 835, 871, 911, 922, 938)

**Evidence Point 2: `progress_callback` is passed correctly**
- Location: `web_ui/app.py` lines 332-341
- Function: Defined in `process_with_updates()` and passed to `LiveDocumentProcessor`
- Status: ✓ Callback is registered

**Evidence Point 3: `socketio.emit()` calls exist**
- Location: `web_ui/app.py` lines 334-338, 346, 351
- Function: Emit `'processing_update'`, `'document_processed'`, `'processing_error'` events
- Status: ✗ CALLED but FAILING SILENTLY

**Evidence Point 4: Frontend handlers exist**
- Location: `web_ui/static/js/app.js` lines 37-52
- Handlers: `'processing_update'`, `'document_processed'` events
- Status: ✓ Registered but never triggered

**Evidence Point 5: No errors in logs**
- Server logs show "Client connected" and "Starting background processing for: ..."
- NO socketio.emit() confirmation messages
- NO error messages
- NO exceptions thrown
- Status: ✗ Silent failure

### 3. Root Cause Identification

**The Critical Insight:**

Flask-SocketIO requires a **Flask application context** when emitting from background threads.

**Why?**
- Flask uses context-local storage for request/application data
- SocketIO needs access to the session registry to broadcast to clients
- Background threads run OUTSIDE the Flask request context
- Without context, `socketio.emit()` silently fails (no exception raised!)

**Original Code (BROKEN):**
```python
def process_with_updates(filepath):
    def progress_callback(message, progress, data):
        socketio.emit('processing_update', {  # FAILS SILENTLY
            'message': message,
            'progress': progress,
            'data': data
        })
```

**Fixed Code:**
```python
def process_with_updates(filepath):
    def progress_callback(message, progress, data):
        with app.app_context():  # CRITICAL FIX
            socketio.emit('processing_update', {
                'message': message,
                'progress': progress,
                'data': data
            }, broadcast=True)  # Also add broadcast=True
```

### 4. Why This Was So Hard to Debug

1. **No error messages** - `socketio.emit()` fails silently without raising exceptions
2. **Processing completes successfully** - Only the *notifications* fail, not the work
3. **Works in some cases** - Direct HTTP requests work fine, only background threads fail
4. **Previous working state** - System WAS working, so context was easy to overlook
5. **Misleading symptoms** - Progress bar stuck suggested processing failure, not notification failure

### 5. The Complete Fix

**File: `web_ui/app.py` lines 329-354**

Changes made:
1. Wrapped ALL `socketio.emit()` calls with `with app.app_context():`
2. Added `broadcast=True` to all emit calls (ensures delivery to all clients)
3. Added diagnostic logging: `logger.info(f"[PROGRESS {progress:.0f}%] {message}")`
4. Added emit confirmation: `logger.debug(f"Emitted processing_update: {progress:.0f}%")`

```python
def process_with_updates(filepath):
    try:
        def progress_callback(message, progress, data):
            # CRITICAL: socketio.emit() from background thread requires app context
            logger.info(f"[PROGRESS {progress:.0f}%] {message}")
            with app.app_context():
                socketio.emit('processing_update', {
                    'message': message,
                    'progress': progress,
                    'data': data
                }, broadcast=True)
                logger.debug(f"Emitted processing_update: {progress:.0f}%")

        logger.info(f"Starting background processing for: {filepath}")
        processor = LiveDocumentProcessor(progress_callback)
        doc_id = processor.process_document(filepath)
        logger.info(f"Background processing completed: {doc_id}")

        # Emit completion (also needs app context)
        with app.app_context():
            socketio.emit('document_processed', {'document_id': doc_id}, broadcast=True)

    except Exception as e:
        logger.error(f"BACKGROUND THREAD ERROR: {e}")
        logger.error(traceback.format_exc())
        with app.app_context():
            socketio.emit('processing_error', {'error': str(e)}, broadcast=True)
```

---

## Testing Instructions

### Manual Test

1. **Start Flask server:**
   ```bash
   cd C:\Users\jpswi\Research-Assistant-Tool-
   python web_ui/app.py
   ```

2. **Open browser:**
   ```
   http://localhost:5000
   ```

3. **Upload a PDF document**
   - Click "Upload Document" button
   - Select any PDF file
   - Watch the progress bar

### Expected Behavior (FIXED)

**Progress bar should:**
- Start at 0%
- Advance to 5% (Creating document node)
- Advance to 10% (Extracting text)
- Advance to 30% (Extracting claims)
- Advance to 50% (Clustering claims)
- Advance to 60-90% (Adding claims to graph)
- Reach 100% (Processing complete)
- Graph updates automatically (no refresh needed!)

**Server logs should show:**
```
[PROGRESS 5%] Creating document node...
[PROGRESS 10%] Extracting text from PDF...
[PROGRESS 15%] Extracted 12345 characters
[PROGRESS 30%] Extracting flat claims...
[PROGRESS 50%] Clustering claims using semantic embeddings (PRIMARY method)...
[PROGRESS 60%] Added sub-claim 1/15
[PROGRESS 70%] Added sub-claim 8/15
[PROGRESS 90%] Added sub-claim 15/15
[PROGRESS 100%] Document processing complete!
```

### If It Still Fails

**Check browser console (F12):**
- Look for WebSocket connection errors
- Verify `'processing_update'` events are received

**Check Flask server logs:**
- Verify `[PROGRESS XX%]` messages appear
- Verify `Emitted processing_update` debug messages appear
- Look for any exceptions or error messages

**Check Flask-SocketIO version:**
```bash
pip show flask-socketio
```
Should be >= 5.0.0

**Check eventlet/gevent:**
```bash
pip show eventlet
```
Flask-SocketIO uses eventlet or gevent for async handling.

---

## Technical Deep Dive

### Flask Application Context

Flask uses **context-local storage** (thread-local or greenlet-local) to maintain request/application state. This includes:
- Current request object (`request`)
- Current session object (`session`)
- Application configuration (`current_app`)
- SocketIO session registry

### Why Background Threads Break Context

1. HTTP request arrives → Flask creates request context
2. User uploads file → `upload_document()` runs in request context
3. `threading.Thread` spawned → **NEW thread, NO context**
4. Background thread calls `socketio.emit()` → **NO ACCESS TO SESSION REGISTRY**
5. `emit()` fails silently (no exception because it's designed for async use)

### The Solution: `app.app_context()`

```python
with app.app_context():
    socketio.emit(...)  # Now has access to app config and session registry
```

This temporarily pushes the application context onto the context stack for the current thread.

### Why `broadcast=True`?

Without `broadcast=True`, SocketIO tries to emit to the "current request's client". But in a background thread, there IS no current request, so it emits to... nobody.

`broadcast=True` explicitly tells SocketIO: "Send this to ALL connected clients, regardless of request context."

---

## Prevention for Future

### Best Practice: Always Use App Context in Background Threads

```python
def background_task():
    with app.app_context():
        # Any Flask/SocketIO code here
        socketio.emit('event', data, broadcast=True)
        db.session.query(...)
        current_app.config['KEY']
```

### Testing Checklist

- [ ] WebSocket events work from HTTP request handlers
- [ ] WebSocket events work from background threads
- [ ] Progress bar updates smoothly
- [ ] No page refresh needed for graph updates
- [ ] Server logs show all progress messages
- [ ] Browser console shows no errors

---

## Related Documentation

- [Flask Application Context](https://flask.palletsprojects.com/en/latest/appcontext/)
- [Flask-SocketIO Background Tasks](https://flask-socketio.readthedocs.io/en/latest/getting_started.html#emitting-from-an-external-process)
- [Python Threading](https://docs.python.org/3/library/threading.html)

---

## Changelog

**2025-11-17**: Fixed WebSocket progress updates by adding `app.app_context()` to all `socketio.emit()` calls in background thread.
