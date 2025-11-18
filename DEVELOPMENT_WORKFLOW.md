# Development Workflow - MANDATORY PROCESS

## 🚨 CRITICAL RULE: Always Restart Services After Changes

**PROBLEM**: Multiple Flask/Python processes can run simultaneously on different git commits, causing:
- Testing the wrong code version
- Debugging non-existent bugs
- Wasting hours investigating issues that don't exist in current code

**SOLUTION**: Follow this workflow **EVERY TIME** you make changes.

---

## Standard Development Cycle

### 1. Before Making ANY Changes

```bash
# Kill all Python processes
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force"

# Verify current commit
git log --oneline HEAD -1

# Verify clean working tree
git status
```

### 2. Make Your Changes

- Edit code
- Test locally if needed
- Commit changes with descriptive message

### 3. ALWAYS Restart Services After Commit

```bash
# Kill ALL Python processes (critical!)
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force"

# Start Neo4j (if needed)
powershell -ExecutionPolicy Bypass -File start_neo4j.ps1

# Start Flask on CURRENT code
cd web_ui
python app.py
```

**Wait for Flask to show**: `* Running on http://127.0.0.1:5000`

### 4. Verify You're Running Current Code

```bash
# In Flask terminal, you should see recent log lines matching your changes
# Check git commit in terminal:
git log --oneline HEAD -1
```

### 5. Test Your Changes

- Open browser to localhost:5000
- Clear browser cache (Ctrl+Shift+R)
- Test the feature
- Check browser console (F12)

---

## Common Mistakes to Avoid

### ❌ Running Multiple Flask Instances
**Symptom**: Old behavior persists after code changes
**Fix**: Always kill ALL Python processes before starting Flask

### ❌ Testing on Wrong Commit
**Symptom**: Changes don't appear, bugs that shouldn't exist
**Fix**: Check `git log HEAD -1` before testing

### ❌ Cached Frontend Code
**Symptom**: JavaScript changes don't work
**Fix**: Hard refresh browser (Ctrl+Shift+R)

### ❌ Reusing Old Neo4j Data
**Symptom**: Schema changes don't apply, old data structure
**Fix**: Clear Neo4j database if schema changed:
```cypher
MATCH (n) DETACH DELETE n
```

---

## Quick Checklist Before Testing

- [ ] All Python processes killed
- [ ] Git status shows correct commit
- [ ] Neo4j running (if needed)
- [ ] Flask started on current code
- [ ] Browser hard-refreshed
- [ ] Browser console open for debugging

---

## Multi-Process Architecture

This project has:
1. **Neo4j Database** (Java process) - runs on port 7687/7474
2. **Flask Web Server** (Python) - runs on port 5000
3. **Background Workers** (Python) - document processing
4. **Claude Code CLI** (spawned by Flask) - AI processing

**All must be restarted** when relevant code changes:
- Neo4j: Only when database schema changes
- Flask: **ALWAYS** after backend changes
- Browser: **ALWAYS** after frontend changes (hard refresh)

---

## Emergency: "Nothing Works After Changes"

```bash
# Nuclear option - restart everything
powershell -Command "Get-Process python,java -ErrorAction SilentlyContinue | Stop-Process -Force"

# Verify clean slate
powershell -Command "Get-Process python,java -ErrorAction SilentlyContinue"
# Should return nothing

# Start Neo4j
powershell -ExecutionPolicy Bypass -File start_neo4j.ps1

# Wait 20 seconds for Neo4j to initialize
Start-Sleep -Seconds 20

# Start Flask
cd web_ui
python app.py

# Hard refresh browser
# Press Ctrl+Shift+R in browser
```

---

## Best Practices

1. **One Feature = One Commit** → Test → Restart Services
2. **Never assume** services auto-reload correctly
3. **Always verify** current commit before testing
4. **Document unexpected behavior** before restarting (helps debugging)
5. **Use background tasks** (`run_in_background=true`) to keep services running during investigation

---

## Quick Reference Commands

### Kill Everything
```bash
powershell -Command "Get-Process python,java -ErrorAction SilentlyContinue | Stop-Process -Force"
```

### Start Clean Stack
```bash
# Neo4j
powershell -ExecutionPolicy Bypass -File start_neo4j.ps1

# Flask (in new terminal)
cd web_ui && python app.py
```

### Verify Current State
```bash
git log --oneline HEAD -1
git status
powershell -Command "Get-Process python | Select-Object Id,StartTime,CommandLine"
```

---

## Remember

**RESTART EVERYTHING AFTER EVERY COMMIT**

This 30-second process saves hours of debugging phantom issues.
