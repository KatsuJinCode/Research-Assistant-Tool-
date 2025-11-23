# Tutorial System Testing Guide

## Quick Start Testing

### 1. First-Time User Experience

**Steps:**
1. Open browser in incognito/private mode
2. Navigate to the web UI
3. Wait 1.5 seconds after page loads

**Expected:**
- Tutorial automatically starts
- Welcome screen appears centered on page
- Backdrop dims the rest of the UI
- "Start Tour" and "Skip" buttons are visible

### 2. Tutorial Navigation

**Steps:**
1. Click "Start Tour"
2. Use "Next" button to advance through steps
3. Try "Previous" button to go back
4. Try keyboard arrows to navigate

**Expected:**
- Each step highlights the correct UI element with spotlight
- Tutorial panel positions near highlighted element
- Previous button hidden on first step
- Next button changes to "Finish" on last step
- Arrow keys work for navigation

### 3. Step Validation

**Test Step 2 (Upload Document):**
1. Navigate to Step 2
2. Try clicking "Next" without uploading

**Expected:**
- Orange warning message appears
- Cannot advance until document uploaded
- After upload, automatically advances to Step 3

**Test Step 4 (Click Node):**
1. Navigate to Step 4
2. Try clicking "Next" without clicking node

**Expected:**
- Warning message appears
- Cannot advance until node clicked
- After clicking node, automatically advances to Step 5

### 4. Skip Tutorial

**Steps:**
1. Start tutorial
2. Click "Skip Tour" button
3. Confirm in dialog

**Expected:**
- Tutorial closes immediately
- `tutorial_skipped` saved in localStorage
- Tutorial doesn't auto-start on next visit

### 5. Help Button

**Steps:**
1. Click "? Help" button in header
2. Click each help option

**Expected:**
- Help menu modal appears
- 6 help topics displayed in grid
- Each topic opens correct help content
- "Start Tutorial" option restarts tutorial

### 6. Context Help Icons

**Steps:**
1. Find "?" icon next to upload button
2. Click it

**Expected:**
- Help modal appears
- Shows upload-specific help content
- "Got it!" button closes modal

### 7. Resume Tutorial

**Steps:**
1. Start tutorial and go to Step 3
2. Refresh the page
3. Wait for notification

**Expected:**
- "Continue Tutorial?" notification appears top-right
- Shows current step number
- "Continue" button resumes from Step 3
- "Not Now" dismisses notification

### 8. Complete Tutorial

**Steps:**
1. Complete all 8 steps
2. Click "Finish" on last step
3. Refresh page

**Expected:**
- Success notification appears
- Tutorial closes
- `tutorial_completed` saved in localStorage
- Tutorial doesn't auto-start on refresh
- Can still manually start via Help button

## Browser DevTools Testing

### Check LocalStorage

**Open DevTools → Application → Local Storage**

Should see:
```
first_visit: "true"
tutorial_completed: "true" (after completion)
tutorial_skipped: "true" (if skipped)
tutorial_current_step: "3" (if in progress)
```

### Check Console

**Open DevTools → Console**

Should see:
```
[Tutorial] Initializing tutorial system
[Tutorial] Tutorial system ready
[Tutorial] Starting tutorial (when started)
[Tutorial] Document uploaded - advancing (on upload)
[Tutorial] Node selected - advancing (on node click)
```

### Check Events

**Open DevTools → Console → Type:**
```javascript
document.addEventListener('documentUploaded', (e) => {
    console.log('Document uploaded event:', e.detail);
});

document.addEventListener('nodeSelected', (e) => {
    console.log('Node selected event:', e.detail);
});
```

Then upload document or click node - should see events logged.

## Visual Inspection Checklist

### Tutorial Panel
- [ ] Panel has blue gradient header
- [ ] Close button (×) appears in header
- [ ] Content area is readable with white text on dark background
- [ ] Footer has progress indicator (e.g., "Step 2 of 8")
- [ ] Buttons are styled correctly (blue primary, gray secondary)
- [ ] Panel has rounded corners
- [ ] Panel has blue border glow

### Spotlight
- [ ] Spotlight appears around target element
- [ ] Spotlight has blue border
- [ ] Spotlight has pulsing glow effect
- [ ] Spotlight follows element if page resizes
- [ ] Backdrop dims everything except spotlight

### Help Button
- [ ] Help button appears in header
- [ ] Help button has "?" icon
- [ ] Help button glows on hover
- [ ] Help button is easy to find

### Context Help Icons
- [ ] Small blue circles with "?" inside
- [ ] Icons scale up on hover
- [ ] Icons are positioned correctly near UI elements

## Keyboard Navigation Testing

### Keys to Test
- **Esc**: Should skip tutorial (with confirmation)
- **Enter**: Should advance to next step
- **Right Arrow**: Should advance to next step
- **Left Arrow**: Should go to previous step

**Note:** Arrow keys shouldn't work when typing in input fields.

## Mobile/Responsive Testing

### Small Screens
1. Resize browser to 768px width
2. Start tutorial

**Expected:**
- Panel resizes to fit screen
- Panel never goes off-screen
- Buttons remain accessible
- Content is readable

### Touch Testing
- Tap spotlight to ensure it doesn't interfere with clicks
- Tap buttons to ensure they respond
- Swipe gestures shouldn't interfere

## Error Handling Testing

### Missing Elements

**Test if tutorial handles missing target elements:**

1. Open DevTools Console
2. Type:
```javascript
TutorialManager.steps[2].target = '#nonexistent-element';
TutorialManager.goToStep(2);
```

**Expected:**
- Tutorial doesn't crash
- Warning logged to console
- Panel centers instead of positioning near element

### Invalid Step

**Test invalid step navigation:**
```javascript
TutorialManager.goToStep(99);
```

**Expected:**
- Nothing happens (silently fails)
- No errors thrown

### Multiple Tutorial Instances

**Test singleton behavior:**
```javascript
TutorialManager.init();
TutorialManager.init(); // Call twice
```

**Expected:**
- Only one overlay exists
- No duplicate elements created

## Performance Testing

### Load Time
- Measure page load time with tutorial system
- Should add minimal overhead (<100ms)

### Animation Performance
- Open DevTools → Performance tab
- Record during tutorial navigation
- Check frame rate stays above 30fps

### Memory Leaks
- Complete tutorial multiple times
- Check memory usage doesn't grow
- Close and restart tutorial several times

## Cross-Browser Testing

### Chrome
- [ ] Tutorial works correctly
- [ ] All animations smooth
- [ ] LocalStorage persists

### Firefox
- [ ] Tutorial works correctly
- [ ] All animations smooth
- [ ] LocalStorage persists

### Safari
- [ ] Tutorial works correctly
- [ ] All animations smooth
- [ ] LocalStorage persists

### Edge
- [ ] Tutorial works correctly
- [ ] All animations smooth
- [ ] LocalStorage persists

## Integration Testing

### With Existing Features

**Upload Flow:**
1. Start tutorial
2. Upload document during Step 2
3. Verify tutorial advances
4. Verify document appears in graph

**Node Selection:**
1. Start tutorial
2. Click node during Step 4
3. Verify tutorial advances
4. Verify property viewer opens

**AI Assistant:**
1. Complete tutorial
2. Use AI Assistant
3. Verify no tutorial interference

**Search:**
1. Complete tutorial
2. Use search feature
3. Verify no tutorial interference

## Regression Testing

After any code changes, verify:
- [ ] Tutorial still auto-starts for first-time users
- [ ] Help button still works
- [ ] Context help icons still work
- [ ] Events still fire correctly
- [ ] State still persists
- [ ] No JavaScript errors in console
- [ ] No CSS conflicts with existing styles

## Bug Reporting Template

If you find a bug, report it with this format:

```
**Bug Title**: [Short description]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Browser**: [Chrome/Firefox/Safari/Edge + version]
**OS**: [Windows/Mac/Linux]
**Screenshot**: [If applicable]
**Console Errors**: [If any]
```

## Success Criteria

Tutorial system is working correctly if:
- ✅ All 8 steps display correctly
- ✅ Spotlight highlights correct elements
- ✅ Auto-advancement works for Steps 2 and 4
- ✅ Help button and context help work
- ✅ State persists across page reloads
- ✅ Tutorial can be skipped and resumed
- ✅ No JavaScript errors in console
- ✅ Works in all major browsers
- ✅ Responsive on different screen sizes
- ✅ Keyboard navigation works

## Manual Test Scenarios

### Scenario 1: Complete First-Time User Flow
1. Clear localStorage
2. Load page in incognito mode
3. Complete entire tutorial (all 8 steps)
4. Verify each step works correctly
5. Verify tutorial marks as completed

**Time**: ~3 minutes

### Scenario 2: Skip and Restart
1. Start tutorial
2. Skip at Step 3
3. Confirm skip
4. Click Help button
5. Restart tutorial
6. Verify starts from Step 1

**Time**: ~1 minute

### Scenario 3: Resume Interrupted Tutorial
1. Start tutorial
2. Navigate to Step 4
3. Refresh page
4. Click "Continue" on notification
5. Verify resumes at Step 4

**Time**: ~1 minute

### Scenario 4: Context Help Tour
1. Click Help button
2. Click each of 6 help topics
3. Read content
4. Verify all display correctly

**Time**: ~2 minutes

### Scenario 5: Validation Testing
1. Start tutorial
2. Navigate to Step 2
3. Try to advance without uploading
4. Verify warning appears
5. Upload document
6. Verify auto-advances
7. Navigate to Step 4
8. Try to advance without clicking node
9. Verify warning appears
10. Click node
11. Verify auto-advances

**Time**: ~2 minutes

## Total Testing Time

**Quick Test**: ~5 minutes (basic functionality)
**Comprehensive Test**: ~20 minutes (all scenarios)
**Full Regression**: ~45 minutes (all browsers, all scenarios)
