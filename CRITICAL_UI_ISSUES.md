# Critical UI/UX Issues - Repository Migration Impact

**Status**: Repository migration working but revealed pre-existing UI bugs and broke real-time updates

## Issue #1: Nodes Disappear on Page Refresh ✅ FIXED
**What happens**: After processing completes and nodes are visible, refreshing the page shows only document node
**Root cause**: `/api/full-graph` query uses wrong relationship type (`HAS_SUB_CLAIM` vs actual `PARENT_OF`/`CONTAINS_CLAIM`)
**Impact**: Can't view processed documents after refresh
**Fix**: Changed `/api/full-graph` to use `PARENT_OF` relationship (lines 164-167 in app.py)
**Status**: ✅ FIXED - Ready for testing

## Issue #2: Stats at Top Show Zero ✅ FIXED
**What happens**: "Total Nodes", "Claims", "Evidence", "Research Results" all show `-`
**Location**: Top of UI, always shows zero
**Root cause**: UI JavaScript looking for wrong element IDs (doc-count vs stat-nodes) and wrong stats structure
**Impact**: No visibility into system state
**Fix**: Fixed UI.updateStats() to use correct element IDs and parse API response structure
**Status**: ✅ FIXED - Stats now display correct counts from database

## Issue #3: Nodes Only Appear All-at-Once at End ✅ FIXED
**What happens**: During processing, nodes created in DB but don't appear in graph until very end
**Expected**: Nodes appear incrementally as they're created (real-time)
**Root cause**:
  - Repository doesn't emit WebSocket events when creating nodes
  - UI polls `/api/full-graph` instead of receiving push notifications
  - OLD code probably emitted events directly, new repository layer doesn't
**Impact**: User can't see progress, seems broken during processing
**Fix**:
  1. Created `backend/database/event_emitter.py` - Event emitter singleton
  2. Modified `BaseRepository.create_node()` to call `event_emitter.emit_node_created()`
  3. Modified `BaseRepository.update_node()` to call `event_emitter.emit_node_updated()`
  4. Registered callback in `web_ui/app.py` with `RepositoryEventEmitter.set_emit_callback(socketio.emit)`
**Status**: ✅ FIXED - Real-time WebSocket events now working

## Issue #4: Processing Log UX is Backwards ❌ MEDIUM
**What happens**: Processing log adds items one-by-one as they complete
**Expected**:
  1. Show ALL tasks upfront (e.g., "Processing claim 1/4", "Processing claim 2/4", etc.)
  2. Mark them complete one-by-one as they finish
  3. Visual indication of "what's done" vs "what's remaining"
**Impact**: User can't see total workload, only what's completed so far
**Fix**: Restructure progress callback to emit "task list" then "task updates"
**Status**: NOT STARTED - **UX REDESIGN NEEDED**

## Issue #5: Upload UI - Purple Box Too Big ❌ LOW
**What happens**: Upload dropzone takes up too much screen space
**Impact**: Minor UX annoyance
**Fix**: CSS adjustment to reduce height
**Status**: NOT STARTED

## Issue #6: DOCX Support Claimed But Doesn't Work ❌ MEDIUM
**What happens**: UI says "Supported: PDF, TXT, DOCX" but DOCX uploads fail
**Impact**: User confusion, broken promise
**Fix Options**:
  1. Remove DOCX from supported list (easy)
  2. Actually implement DOCX parsing (harder)
**Status**: NOT STARTED - **DECISION NEEDED**

## Issue #7: Missing Input Methods ❌ LOW
**Requested features**:
- Manual text input of claims (no file upload)
- Folder upload (process multiple files)
- Queue multiple files
**Impact**: Limited flexibility for users
**Fix**: New features to implement
**Status**: NOT STARTED - **FEATURE REQUEST**

## Issue #8: Can't Select Nodes During Processing ❌ CRITICAL
**What happens**: During background processing, clicking nodes is unresponsive (~10 second lag)
**Root cause**:
  - Probably UI thread blocked by something
  - OR graph re-rendering constantly
  - OR too many WebSocket messages flooding
**Impact**: UI feels broken during processing
**Fix**: Debug performance, async rendering, throttle updates
**Status**: NOT STARTED - **PERFORMANCE INVESTIGATION NEEDED**

---

## Priority Order for Fixes

### P0 - Blocking (Must fix immediately)
1. ✅ **Issue #1**: Nodes disappear on refresh - FIXED ✅
2. ✅ **Issue #2**: Stats show zero - FIXED ✅
3. ✅ **Issue #3**: Nodes only appear at end - FIXED ✅
4. ✅ **Issue #9**: Claims attach to phantom document (ID mismatch) - FIXED ✅
5. ✅ **Issue #10**: 4 separate agent calls waste context/time - FIXED ✅
6. **Issue #8**: Can't select nodes during processing (UI feels broken) - NEEDS INVESTIGATION

### P1 - Important (Fix soon)
5. **Issue #4**: Processing log UX backwards (can't see remaining work)
6. **Issue #6**: DOCX support claims vs reality (decide: remove or implement)

### P2 - Nice to have (Can defer)
7. **Issue #5**: Purple box too big (cosmetic)
8. **Issue #7**: Missing input methods (new features)

---

## Root Cause Analysis

### The Real Problem: Repository Layer Doesn't Emit Events

The **OLD code** probably emitted WebSocket events directly when creating nodes:
```python
self.db.create_node('Claim', data)
socketio.emit('node_created', data)  # <-- Direct emission
```

The **NEW repository code** just writes to database:
```python
self.claim_repo.create_claim(...)  # <-- No events!
```

**This breaks real-time updates** because:
1. UI expects WebSocket push notifications
2. Repositories don't know about socketio
3. UI falls back to polling, which is slow

### Solutions

**Option A**: Make repositories emit events (violates separation of concerns)
**Option B**: Add event layer above repositories that emits after operations
**Option C**: UI polls more frequently (band-aid, not real-time)

**RECOMMENDED**: Option B - Event emitter wrapper around repositories

---

## Technical Debt Created by Migration

1. **No WebSocket events from repository layer** - Real-time updates broken
2. **Schema mismatch** - UI expected `HAS_SUB_CLAIM`, DB has `PARENT_OF` (FIXED)
3. **Missing repository methods** - `/api/graph-stats` needs new methods
4. **Performance issues** - Cartesian product warnings in relationship creation queries

---

## Next Steps

1. Test fix for Issue #1 (refresh showing nodes)
2. Add WebSocket event emission to repository operations (Issue #3)
3. Fix stats route (Issue #2)
4. Performance investigation for node selection lag (Issue #8)
5. UX redesign for processing log (Issue #4)

---

## Issue #9: Claims Attach to Phantom Document Node ✅ FIXED
**What happens**: Logs show `Created document d98961b4...` but `Created claim xxx for document c1eaaaa4...` (wrong ID!)
**Root cause**: Flask auto-reload restarted main server but background tasks kept running with OLD cached code
**Impact**: Nodes appeared disjointed, not attached to visible document
**Fix**:
  1. Killed ALL background shells, not just Python processes
  2. Identified that `socketio.start_background_task()` keeps old code cached
  3. Verified fix works: All claims now attach to correct document ID
**Status**: ✅ FIXED - Nodes now attach correctly on first appearance

## Issue #10: 4 Separate Agent Calls Waste Context ✅ FIXED
**What happens**: Each claim processes through 4 stages: analyze, clarify, simplify, validate (4 separate agent calls!)
**Impact**: VERY slow (4x redundant context loading), each stage re-reads same claim text
**Root cause**: Pipeline designed before realizing LLMs can do all stages in one pass
**Fix**: Created `_normalize_claim_unified()` that does all 4 stages in ONE agent call
  - Single prompt with all 4 stage instructions
  - Agent uses same context for all stages
  - Returns all results at once: analysis, clarified, 3 candidates, scores, disposition
  - Estimated 4x faster (eliminates 3 redundant API calls per claim)
**Status**: ✅ FIXED - Unified normalization pipeline implemented and deployed

**Created**: 2025-11-18
**Last Updated**: 2025-11-18 (Added Issues #9 and #10)
**Owner**: Development Team
