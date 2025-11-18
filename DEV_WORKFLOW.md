# Development Workflow - FOOLPROOF GUIDE

## 🔴 THE PROBLEM: Stale Code Cache

Flask's auto-reload **DOES NOT RESTART BACKGROUND TASKS**.

When you change code:
- ✅ Main Flask app restarts with new code
- ❌ Background tasks (`socketio.start_background_task`) keep running OLD code
- ❌ Result: You test against STALE code and waste hours!

## ✅ THE SOLUTION: Clean Restart Every Time

### Method 1: Use the Clean Restart Script (RECOMMENDED)

```bash
python restart_clean.py
```

This script:
1. 🔥 Kills ALL Python processes (nuclear option)
2. 📝 Generates new build hash for cache detection
3. 🚀 Starts fresh server with version tracking
4. ✨ Updates UI with version indicator

**When to use**: Every time you make ANY code change during development

### Method 2: Manual Clean Restart (Backup)

If the script fails, do this manually:

```bash
# 1. Kill ALL Python processes
powershell -Command "Stop-Process -Name python -Force"

# 2. Wait 2 seconds
timeout /t 2

# 3. Start fresh server
cd web_ui
python app.py
```

### Method 3: Check for Stale Code (Visual Indicator)

Look at the **bottom-right corner of the UI** - it shows:
```
Build: a1b2c3d4 | Restart #5
```

If this doesn't change after restart → YOU'RE RUNNING STALE CODE!

## 🎯 Development Workflow Checklist

### Before Each Test Session:
- [ ] Run `python restart_clean.py`
- [ ] Check browser console for build hash
- [ ] Verify build hash changes when you edit code
- [ ] Clear browser cache if UI looks wrong (Ctrl+Shift+R)

### After Making Code Changes:
- [ ] **NEVER** rely on Flask auto-reload for background task changes
- [ ] **ALWAYS** run clean restart script
- [ ] **VERIFY** build hash changed in UI
- [ ] **CONFIRM** logs show your new code (check for your debug prints)

### Red Flags (You're Testing Stale Code):
- ⚠️ Build hash didn't change after restart
- ⚠️ Your debug logs don't appear
- ⚠️ Bug you "fixed" still happens
- ⚠️ Feature you added doesn't work
- ⚠️ Database IDs don't match logs (phantom nodes)

## 🔧 Technical Details

### Why Flask Auto-Reload Fails

Flask's watchdog auto-reloader:
1. Detects file change
2. Restarts **main process** with new code ✅
3. **Background greenthreads continue with OLD code** ❌

The background task created by `socketio.start_background_task()` is running in eventlet/gevent and is **NOT restarted** when Flask reloads.

### Why Clean Restart Works

1. Kills ALL Python processes → No orphaned background tasks
2. Starts fresh process → All code loaded from disk
3. Background tasks inherit fresh code → No cache

### Build Hash System

The restart script generates an MD5 hash of critical files:
- `web_ui/document_processor.py` (main pipeline)
- `web_ui/app.py` (Flask routes)
- `backend/database/repositories/claim_repository.py` (data access)
- `backend/database/event_emitter.py` (WebSocket events)

If ANY of these change → hash changes → you can visually confirm fresh code.

## 🚀 Quick Reference

| Scenario | Action |
|----------|--------|
| Starting dev session | `python restart_clean.py` |
| Made code changes | `python restart_clean.py` |
| Testing not working | `python restart_clean.py` |
| Bug you fixed reappears | `python restart_clean.py` |
| Confused why feature doesn't work | `python restart_clean.py` |
| In doubt | `python restart_clean.py` |

**Golden Rule**: When in doubt, clean restart. It's faster than debugging stale code!

## 📊 Version Tracking

The UI now shows version info in the bottom-right:

```
Build: a1b2c3d4 | Restart #5 | 2025-11-18 01:30:15
```

- **Build**: Hash of critical files (changes when you edit code)
- **Restart #**: How many times restarted today (resets at midnight)
- **Timestamp**: When this build was created

If you edit code and restart, the build hash **MUST** change. If it doesn't → something is wrong!

## 🐛 Troubleshooting

### Build hash not changing?
1. Make sure you're editing the right file
2. Check file is actually saved (Ctrl+S)
3. Verify file is in the hash list (see Technical Details)
4. Try killing Python processes manually

### Server won't start?
1. Check if port 5000 is already in use: `netstat -ano | findstr :5000`
2. Kill process using port: `taskkill /F /PID <pid>`
3. Try starting manually: `cd web_ui && python app.py`

### UI showing old version?
1. Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Open in incognito/private window
4. Check if VERSION.json was updated

---

**Last Updated**: 2025-11-18
**Owner**: Development Team
**Status**: Active - Use this workflow for ALL development!
