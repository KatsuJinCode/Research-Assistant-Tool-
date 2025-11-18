# Testing Instructions - Live Updates Implementation

## ✅ What's Been Implemented

### Backend (Completed & Committed)
- **4-Stage Pipeline** in `web_ui/document_processor.py:573-777`
  - Stage 1: Analysis (deep understanding)
  - Stage 2: Clarification (explicit meaning)
  - Stage 3: Simplification (3 candidates)
  - Stage 4: Validation (fidelity + quality scoring)

- **Real-Time Events** emitted via SocketIO:
  - `claim_stage_update` with `status='in_progress'` and `status='complete'`
  - `claim_complete` with final results

- **Complete Data Storage** in Neo4j (lines 1274-1322):
  - All processing stages (original, analysis, clarified, candidates)
  - Fidelity scores for all 3 candidates
  - Quality score (0.0-1.0) and disposition (central/child/review/discard)
  - Timing data for each stage
  - Word counts

### Frontend (Completed & Committed)
- **SocketIO Handlers** in `web_ui/static/js/app.js:130-178`
  - `claim_stage_update` - tracks each stage
  - `claim_complete` - final results
  - `claimStates` object stores complete processing history

- **Console Logging** for real-time visibility:
  - Shows stage progress with durations
  - Displays final quality scores and dispositions

## 🧪 How to Test

### Step 1: Start Neo4j
```powershell
powershell -ExecutionPolicy Bypass -File start_neo4j.ps1
```

Wait for "Started." message.

### Step 2: Start Flask Backend
```bash
cd web_ui
python app.py
```

Should see:
```
* Running on http://127.0.0.1:5000
```

### Step 3: Open Browser
1. Navigate to `http://localhost:5000`
2. Open Developer Console (F12)
3. Go to Console tab

### Step 4: Upload a Test Document
1. Click "Upload PDF" button
2. Select a PDF with claims (or use test_samples/ directory)
3. Watch the console output!

### Expected Console Output

You should see real-time logs like:

```javascript
Claim <claim_id> - analysis: in_progress { ... }
✓ analysis complete (15.2s)

Claim <claim_id> - clarification: in_progress { ... }
✓ clarification complete (13.4s)

Claim <claim_id> - simplification: in_progress { ... }
✓ simplification complete (14.9s)

Claim <claim_id> - validation: in_progress { ... }
✓ validation complete (11.2s)

✓ Claim <claim_id> complete: {
  text: "Neurological defects cannot explain belief",
  quality: 0.85,
  disposition: "central",
  duration: "54.8s"
}
```

### Step 5: Verify Data Storage

After processing completes:

1. **Check Neo4j Browser** (http://localhost:7474)
   ```cypher
   MATCH (c:Claim) RETURN c LIMIT 1
   ```

2. **Verify claim node contains**:
   - `original_text`
   - `analysis`
   - `clarified`
   - `candidate_1`, `candidate_2`, `candidate_3`
   - `score_1`, `score_2`, `score_3`
   - `quality_score`, `disposition`, `recommendation`
   - `duration_*_ms` fields

## 🎯 What to Look For

### ✅ Success Indicators
- [x] Console shows 4 stages progressing in order
- [x] Each stage shows duration
- [x] Final event shows quality score (0.0-1.0)
- [x] Disposition is one of: central/child/review/discard
- [x] Graph updates with claims
- [x] No errors in console
- [x] Neo4j contains all processing data

### ⚠️ Potential Issues

**Issue**: No `claim_stage_update` events in console
- **Fix**: Check Flask terminal for event emission logs
- **Fix**: Verify SocketIO connected ("✓ WebSocket connected")

**Issue**: Events firing but no graph updates
- **Fix**: This is expected - visual UI components not yet implemented
- **Fix**: Nodes will still appear after processing completes

**Issue**: Quality scores all 0 or missing
- **Fix**: Check if `_validate_final()` is being called
- **Fix**: Verify `_analyze_claim()` is returning data

## 📊 Quality Score Examples

Based on test results (ENHANCED_4STAGE_WITH_QUALITY.txt):

- **0.85 (HIGH)**: "Neurological defects cannot explain belief" → CENTRAL
- **0.35 (LOW)**: "Regular use by some may correlate..." → REVIEW
- **0.80 (HIGH)**: "Brain disease theory gains evidential support..." → CENTRAL

## 🔄 What's Still Pending

Visual UI components (will be added after testing confirms events work):
- Stage indicators (progress dots)
- Quality badges (color-coded)
- Expandable details panel
- Stage animations

**Current state**: Events are firing and data is being stored, but not visually displayed yet. You can verify everything works via browser console logs.

## 🐛 Debugging

### Enable verbose logging:
Browser console:
```javascript
App.socket.on('claim_stage_update', (data) => {
    console.log('FULL EVENT:', JSON.stringify(data, null, 2));
});
```

### Check claim states:
```javascript
console.log('All claim states:', App.claimStates);
```

### View specific claim:
```javascript
console.log('Claim data:', App.claimStates['<claim_id>']);
```

## 📝 Test Checklist

- [ ] Neo4j started successfully
- [ ] Flask app running on port 5000
- [ ] Browser console open
- [ ] File uploaded
- [ ] Saw "analysis: in_progress" message
- [ ] Saw "analysis: complete" with duration
- [ ] Saw all 4 stages complete
- [ ] Saw final "Claim complete" message with quality score
- [ ] Graph shows processed claims
- [ ] Neo4j contains full processing data

## Next Steps After Testing

Once you confirm events are firing correctly:
1. Add visual stage indicators to graph nodes
2. Add quality score badges
3. Add expandable details panel
4. Add CSS animations for stage transitions

All the backend infrastructure is in place - the frontend just needs visual components!
