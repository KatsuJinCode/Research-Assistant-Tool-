# Agent-Fusion Installation - Quick Start

## Purpose
Install Agent-Fusion to provide semantic search over YOUR CODEBASE ONLY (not research PDFs).

**Two Separate Databases:**
- **Neo4j**: Research papers, claims, evidence (your app)
- **Agent-Fusion**: Your codebase (development tool for finding code)

---

## Step 1: Install Java 21

### Download
1. Go to: https://adoptium.net/temurin/releases/
2. Select:
   - **Version**: 21 (LTS)
   - **Operating System**: Windows
   - **Architecture**: x64
3. Download the `.msi` installer

### Install
1. Run the downloaded `.msi` file
2. Follow the installer (accept defaults)
3. **Important**: Check "Add to PATH" if asked

### Verify
Open a **new** PowerShell/Command Prompt and run:
```bash
java -version
```

Expected output:
```
openjdk version "21.0.x"
OpenJDK Runtime Environment Temurin-21...
```

---

## Step 2: Download Agent-Fusion

1. Go to: https://github.com/krokozyab/Agent-Fusion/releases
2. Download `release.zip` (latest version)
3. Extract to: `C:\Users\jpswi\Agent-Fusion\`

**Extracted files:**
```
C:\Users\jpswi\Agent-Fusion\
├── orchestrator-0.1.0-all.jar
├── fusionagent_win.toml
├── start.bat
└── other files...
```

---

## Step 3: Configure for CODE ONLY (Not PDFs)

Edit `C:\Users\jpswi\Agent-Fusion\fusionagent_win.toml`:

```toml
# Watch ONLY your code directories (NOT uploads folder with PDFs)
watch_paths = [
  "C:\\Users\\jpswi\\Research-Assistant-Tool-\\research_agent",
  "C:\\Users\\jpswi\\Research-Assistant-Tool-\\web_ui",
  "C:\\Users\\jpswi\\Research-Assistant-Tool-\\docs"
]

[context]
deployment = "STANDALONE"

[context.indexing]
# Index ONLY code files (NOT .pdf)
allowed_extensions = [
  ".py",      # Python
  ".js",      # JavaScript
  ".html",    # Templates
  ".md",      # Docs
  ".json",    # Config
  ".toml",    # Config
  ".css"      # Styles
]

# Ignore build artifacts and caches
[ignore]
patterns = [
  "**/__pycache__/**",
  "**/.git/**",
  "**/node_modules/**",
  "**/.pytest_cache/**",
  "**/venv/**",
  "**/*.pyc",
  "**/uploads/**"  # IMPORTANT: Don't index uploaded research PDFs
]
```

---

## Step 4: Start Agent-Fusion

**IMPORTANT**: Agent-Fusion must be started from a **native Windows shell** (Command Prompt or PowerShell), NOT Git Bash or WSL.

### Option 1: Double-Click (Easiest)
1. Open Windows Explorer
2. Navigate to `C:\Users\jpswi\Agent-Fusion`
3. Double-click `start.bat`

### Option 2: Command Prompt
1. Press `Win + R`, type `cmd`, press Enter
2. Run:
```cmd
cd C:\Users\jpswi\Agent-Fusion
start.bat
```

### Option 3: PowerShell
1. Press `Win + X`, select "Windows PowerShell"
2. Run:
```powershell
cd C:\Users\jpswi\Agent-Fusion
.\start.bat
```

**What happens:**
- Service starts on http://127.0.0.1:3000
- Indexes your Python/JS/HTML code
- Opens admin page in browser
- Ready for Claude Code connection

**Verify:**
- Browser opens showing admin panel
- Console shows "Indexing complete"
- Can see indexed files in web UI

---

## Step 5: Connect to Claude Code

In a **new** terminal:

```bash
claude mcp add --transport http orchestrator http://127.0.0.1:3000/mcp
```

Verify:
```bash
claude mcp list
```

Should show:
```
orchestrator - http://127.0.0.1:3000/mcp
```

---

## Step 6: Test It

In your Claude Code session (this one):

```
use query_context to find where we create claim nodes in Neo4j
```

I should now be able to search your codebase semantically!

---

## Usage Examples

**Finding code:**
```
use query_context to find the document upload handler
use query_context to find all Cypher queries
use query_context to find WebSocket event handlers
```

**Understanding architecture:**
```
use query_context to understand how claims are processed
use query_context to find the claim extraction logic
```

**During modularization:**
```
use query_context to find all imports of document_processor
use query_context to find all places we call db.create_node
```

---

## Troubleshooting

**Java not found after install:**
- Close and reopen terminal
- Verify PATH includes Java: `echo %JAVA_HOME%`

**Port 3000 already in use:**
```powershell
netstat -ano | findstr :3000
```
Kill the process or change port in config

**Files not indexed:**
- Check `watch_paths` matches actual directories
- Check file extensions in `allowed_extensions`
- Check logs in Agent-Fusion console

---

## After Installation

Once working, let me know by saying:
"Agent-Fusion is running"

Then I can test it with:
```
use query_context to find claim extraction code
```

And we'll see semantic code search in action!
