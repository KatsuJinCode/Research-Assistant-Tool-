# Master Testing Checklist - Research Assistant Tool

**Last Updated**: 2025-11-18

## Current Testing Session

### What We're Testing RIGHT NOW:
1. **Unified Normalization Pipeline** (Issue #10) - 4x speed improvement
2. **Visual Version Indicator** - Build hash display in UI
3. **Clean Restart Workflow** - Verifying no stale code issues

---

## ✅ COMPLETED & VERIFIED

### Issue #1: Nodes Disappear on Page Refresh
- [x] Fixed `/api/full-graph` to use `PARENT_OF` relationship
- [x] Verified nodes persist after refresh

### Issue #2: Stats Show Zero
- [x] Fixed `UI.updateStats()` to use correct element IDs
- [x] Verified stats display correct counts

### Issue #3: Nodes Only Appear at End
- [x] Created `event_emitter.py` singleton
- [x] Modified `BaseRepository` to emit events
- [x] Registered callback in `app.py`
- [x] Verified real-time node appearance

### Issue #9: Claims Attach to Phantom Document
- [x] Identified Flask auto-reload doesn't restart background tasks
- [x] Implemented clean restart script
- [x] Verified claims attach to correct document ID

### Issue #10: 4 Separate Agent Calls Waste Context
- [x] Created `_normalize_claim_unified()` method
- [x] Modified pipeline to use unified call
- [ ] **NEEDS TESTING**: Verify 4x speed improvement in practice

---

## 🔄 READY TO TEST (P0 - Critical)

### Issue #8: Can't Select Nodes During Processing
**Status**: NOT STARTED - NEEDS INVESTIGATION
**Test Steps**:
1. Upload document and start processing
2. Try clicking nodes during processing
3. Measure response time (should be < 1 second)
4. Check if UI thread is blocked

**Root Cause Hypotheses**:
- UI thread blocked by something
- Graph re-rendering constantly
- Too many WebSocket messages flooding
- D3.js force simulation running too hot

**Investigation Tools**:
- Browser DevTools Performance tab
- Console log timing
- WebSocket message rate monitoring
- D3.js force simulation diagnostics

---

## 📋 PENDING TESTS (P1 - Important)

### Issue #4: Processing Log UX is Backwards
**Status**: NOT STARTED - UX REDESIGN NEEDED
**Test Steps**:
1. Upload document
2. Check if ALL tasks appear upfront
3. Verify tasks are crossed out as they complete
4. Confirm running head shows current item
5. Check user can see how many tasks ahead

**Implementation TODO**:
- [ ] Emit full task list at start of processing
- [ ] Add strikethrough CSS for completed tasks
- [ ] Add "current task" indicator
- [ ] Show progress bar with N/M tasks format

### Issue #6: DOCX Support Claims vs Reality
**Status**: NOT STARTED - DECISION NEEDED
**Options**:
1. **Quick Fix**: Remove DOCX from supported list in UI
2. **Full Fix**: Implement DOCX parsing with python-docx

**Test Steps** (if implementing DOCX):
- [ ] Install python-docx
- [ ] Add DOCX parser to `document_processor.py`
- [ ] Test with sample DOCX file
- [ ] Verify claim extraction works

---

## 🎨 COSMETIC FIXES (P2 - Low Priority)

### Issue #5: Upload UI - Purple Box Too Big
**Status**: NOT STARTED
**Fix**: CSS adjustment in `index.html`
- [ ] Reduce `#upload-zone` height from 30px padding to ~20px
- [ ] Test on different screen sizes
- [ ] Verify doesn't break drag-and-drop

### Issue #7: Missing Input Methods
**Status**: NOT STARTED - FEATURE REQUEST
**Features Requested**:
- [ ] Manual text input of claims (no file upload)
- [ ] Folder upload (process multiple files)
- [ ] Queue multiple files

---

## 🧪 TEST PROTOCOL

### Before Each Test:
1. **ALWAYS** run `python restart_clean.py` (kills all Python, starts fresh)
2. Check browser console for build hash
3. Verify build hash in UI bottom-right corner
4. Clear browser cache if needed (Ctrl+Shift+R)

### During Test:
1. Watch server logs for correct IDs
2. Check browser console for errors
3. Monitor WebSocket events
4. Note any performance issues

### After Test:
1. Document results in this checklist
2. Update CRITICAL_UI_ISSUES.md with status
3. If bug found: Add to issues list with details

---

## 🚨 RED FLAGS (You're Testing Stale Code!)

- ⚠️ Build hash didn't change after restart
- ⚠️ Your debug logs don't appear
- ⚠️ Bug you "fixed" still happens
- ⚠️ Feature you added doesn't work
- ⚠️ Database IDs don't match logs (phantom nodes)
- ⚠️ Version indicator shows same hash after code change

**If you see ANY of these → STOP and run `python restart_clean.py`**

---

## 📊 Next Priority Test Queue

1. **IMMEDIATE**: Test unified normalization speedup (Issue #10)
   - Upload sample document
   - Measure processing time
   - Compare to expected 4x improvement
   - Verify all 4 stages work correctly

2. **NEXT**: Investigate node selection lag (Issue #8)
   - Profile UI performance during processing
   - Identify bottleneck
   - Implement throttling/debouncing if needed

3. **THEN**: Implement task list UX (Issue #4)
   - Design upfront task list UI
   - Add strikethrough for completed tasks
   - Test user experience

---

## 🔧 Automated Testing Commands

### Run Full Test Suite:
```bash
python run_tests.py critical
```

### Run Specific Test:
```bash
pytest tests/test_claim_repository.py -v
```

### Check Database State:
```bash
# TODO: Add database inspection script
```

---

## 📝 Test Results Log

### 2025-11-18 - Session 1
- ✅ Fixed phantom document node issue (Issue #9)
- ✅ Implemented unified normalization pipeline (Issue #10)
- ✅ Added version indicator to UI
- ✅ Created clean restart script
- ⏳ **PENDING**: Test unified normalization speedup

### Next Test Session:
- Test unified normalization with real document
- Measure actual speedup
- Verify all 4 stages work correctly
- Document performance metrics

---

**Last Updated**: 2025-11-18
**Owner**: Development Team
**Current Focus**: Testing unified normalization pipeline performance
