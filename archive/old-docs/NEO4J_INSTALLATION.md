# Neo4j Community Edition 5.26.0 - Windows Installation Guide

## Overview

This guide documents how to install Neo4j Community Edition 5.26.0 on Windows **without administrator privileges** in a way that can be fully automated by an AI agent.

## System Requirements

- **Java 21**: Required for Neo4j 5.26.0
  - Location: `C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot`
  - If not installed, download from: https://adoptium.net/
- **Windows 10/11**: User-space installation
- **Disk Space**: ~200MB for Neo4j installation
- **RAM**: Minimum 512MB, recommended 1GB+ for Neo4j process

## Installation Files

### Main Installer Script
- **File**: `install_neo4j_windows.ps1`
- **Purpose**: Downloads, extracts, configures, and starts Neo4j
- **Requirements**: No admin privileges needed
- **Run Time**: ~2-3 minutes (depends on download speed)

### Helper Scripts
- **start_neo4j.ps1**: Starts Neo4j in console mode
- **set_neo4j_password.ps1**: Sets initial password before first start
- **change_password.py**: Python script to verify/change password

## Installation Steps

### Automated Installation (Recommended)

Run the installer script:

```powershell
powershell -ExecutionPolicy Bypass -File install_neo4j_windows.ps1
```

The installer performs these steps automatically:

1. **Checks Java Installation**
   - Verifies Java 21 is installed at expected location
   - Sets `JAVA_HOME` and `PATH` environment variables

2. **Creates Installation Directory**
   - Default location: `C:\Users\<username>\.neo4j\neo4j-community-5.26.0`
   - Cleans any previous installation

3. **Downloads Neo4j**
   - URL: `https://dist.neo4j.org/neo4j-community-5.26.0-windows.zip`
   - Size: ~151 MB
   - Uses .NET WebClient for reliable download

4. **Extracts Neo4j Archive**
   - Uses .NET ZipFile for complete extraction
   - Verifies all required folders: bin, conf, data, lib, logs, plugins

5. **Configures Neo4j**
   - Updates `neo4j.conf` with user-space settings
   - Sets listen addresses: `127.0.0.1:7687` (Bolt), `127.0.0.1:7474` (HTTP)
   - Configures memory limits: 512MB-1GB heap

6. **Sets Initial Password**
   - Uses `neo4j-admin.bat dbms set-initial-password research123`
   - **CRITICAL**: This creates `data/dbms/auth.ini` with password hash
   - **Note**: Password has "change required" flag (trailing colon in auth.ini)

7. **Starts Neo4j**
   - Launches Neo4j in console mode (minimized PowerShell window)
   - Waits 20 seconds for startup
   - Verifies ports 7687 (Bolt) and 7474 (HTTP) are listening

## Post-Installation

### Verification

Neo4j should be running with these endpoints:

- **Bolt Protocol**: `bolt://localhost:7687`
- **HTTP/Browser**: `http://localhost:7474`
- **Username**: `neo4j`
- **Password**: `research123`

### Testing Connection

#### Using Python (Direct Connection)

```python
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "research123"))
driver.verify_connectivity()
print("Connected successfully!")
driver.close()
```

#### Using Neo4jDatabase Class

The `research_agent.neo4j_database.Neo4jDatabase` class requires explicit credentials:

```python
from research_agent.neo4j_database import Neo4jDatabase

# Option 1: Explicit credentials (RECOMMENDED)
db = Neo4jDatabase(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="research123"
)
print("Connected!")
db.close()

# Option 2: Use environment variables (requires load_dotenv)
from dotenv import load_dotenv
load_dotenv()  # Load .env file

db = Neo4jDatabase()  # Will use NEO4J_* env vars
print("Connected!")
db.close()
```

### Environment Variables (.env file)

The project uses a `.env` file for configuration:

```env
# Neo4j Connection Settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=research123

# Research Agent Settings
RESEARCH_AGENT_ENV=development
```

**Note**: The `Neo4jDatabase` class does NOT automatically load `.env` file. You must either:
1. Call `load_dotenv()` before creating Neo4jDatabase instance, OR
2. Pass credentials explicitly to the constructor

## Manual Operations

### Start Neo4j

```powershell
powershell -ExecutionPolicy Bypass -File start_neo4j.ps1
```

Or manually:

```powershell
cd C:\Users\<username>\.neo4j\neo4j-community-5.26.0
.\bin\neo4j.bat console
```

### Stop Neo4j

Find and kill the Java process:

```powershell
tasklist | findstr "java.exe"
taskkill //F //PID <PID>
```

Or use Ctrl+C in the Neo4j console window.

### Check Status

```powershell
# Check if ports are listening
netstat -an | findstr "7687"
netstat -an | findstr "7474"
```

### View Logs

Logs are located at: `C:\Users\<username>\.neo4j\neo4j-community-5.26.0\logs\`

- **neo4j.log**: Main server log
- **debug.log**: Detailed debugging information
- **security.log**: Authentication events
- **http.log**: HTTP server log
- **query.log**: Cypher query log

## Troubleshooting

### Issue: Authentication Failure

**Symptom**: `AuthError: The client is unauthorized due to authentication failure`

**Cause**: Password change required flag (trailing colon in `auth.ini`)

**Solution**: The password "research123" is set correctly. If authentication fails, verify:

1. Neo4j is running: `netstat -an | findstr "7687"`
2. Check auth.ini format: `C:\Users\<username>\.neo4j\neo4j-community-5.26.0\data\dbms\auth.ini`
3. Ensure format is: `neo4j:SHA-256,<hash>,<salt>,1024:`
   - The trailing colon (`:`) indicates password change required
   - This is expected for initial setup

### Issue: Port Already in Use

**Symptom**: `Address already in use: bind`

**Solution**:
1. Find process using port: `netstat -ano | findstr "7687"`
2. Kill process: `taskkill //F //PID <PID>`
3. Restart Neo4j

### Issue: Java Not Found

**Symptom**: `Unable to determine the path to java.exe`

**Solution**:
1. Verify Java installation: `"C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot\bin\java.exe" -version`
2. Set JAVA_HOME manually:
   ```powershell
   $env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot"
   $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
   ```

### Issue: Extraction Failed

**Symptom**: Missing folders (bin, conf, etc.) after extraction

**Solution**:
1. Delete incomplete installation: `Remove-Item -Path "$env:USERPROFILE\.neo4j" -Recurse -Force`
2. Run installer again
3. Check available disk space

## Installation Directory Structure

```
C:\Users\<username>\.neo4j\neo4j-community-5.26.0\
├── bin\                    # Executables (neo4j.bat, neo4j-admin.bat, cypher-shell.bat)
├── conf\                   # Configuration files
│   ├── neo4j.conf          # Main configuration
│   ├── neo4j.conf.original # Backup of original config
│   └── user-logs.xml       # Logging configuration
├── data\                   # Database data
│   └── dbms\
│       └── auth.ini        # User authentication file
├── lib\                    # JAR libraries
├── logs\                   # Log files
│   ├── neo4j.log
│   ├── debug.log
│   ├── security.log
│   ├── http.log
│   └── query.log
├── plugins\                # Neo4j plugins
├── import\                 # CSV import directory
├── certificates\           # SSL certificates
├── licenses\               # License files
└── run\                    # Runtime files (PIDs)
```

## Security Considerations

### Default Password

The default password `research123` should be changed for production use:

1. Connect to Neo4j Browser: `http://localhost:7474`
2. Login with `neo4j` / `research123`
3. Change password when prompted

Or use Cypher:

```cypher
ALTER CURRENT USER SET PASSWORD FROM 'research123' TO 'new_secure_password';
```

### Network Access

The installation binds to `127.0.0.1` (localhost only) for security:

- **Bolt**: `127.0.0.1:7687`
- **HTTP**: `127.0.0.1:7474`

To allow remote access, modify `conf/neo4j.conf`:

```
server.default_listen_address=0.0.0.0
```

**WARNING**: Only do this if you understand the security implications!

## AI Agent Integration

This installation is designed to be fully automated by AI agents:

### Key Features for Automation

1. **No User Input**: Script runs completely unattended
2. **No Admin Rights**: Installs in user-space
3. **Deterministic**: Same result every time
4. **Self-Contained**: All dependencies documented
5. **Verification**: Built-in connectivity tests

### Agent Workflow

```powershell
# 1. Run installer
powershell -ExecutionPolicy Bypass -File install_neo4j_windows.ps1

# 2. Wait for completion (script includes 20s startup wait)

# 3. Test connection
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'research123')); driver.verify_connectivity(); print('SUCCESS'); driver.close()"

# 4. Use in application
python your_app.py
```

## Advanced Configuration

### Memory Settings

Edit `conf/neo4j.conf` to adjust memory allocation:

```
# Initial heap size
server.memory.heap.initial_size=512m

# Maximum heap size
server.memory.heap.max_size=1g

# Page cache size
server.memory.pagecache.size=512m
```

### Performance Tuning

For better performance:

```
# More memory (if available)
server.memory.heap.max_size=2g
server.memory.pagecache.size=1g

# More concurrent transactions
server.db.transaction.concurrent.maximum=1000

# Faster queries
dbms.cypher.planner=COST
```

## Uninstallation

To completely remove Neo4j:

```powershell
# 1. Stop Neo4j
taskkill //F //IM java.exe

# 2. Remove installation directory
Remove-Item -Path "$env:USERPROFILE\.neo4j" -Recurse -Force

# 3. (Optional) Remove environment variables
# Manual step: Check user/system environment variables for NEO4J_HOME
```

## References

- Neo4j Official Documentation: https://neo4j.com/docs/
- Neo4j Community Edition: https://neo4j.com/download-center/
- Neo4j Python Driver: https://neo4j.com/docs/python-manual/current/
- Java Adoptium: https://adoptium.net/

## Version Information

- **Neo4j Version**: 5.26.0 Community Edition
- **Java Version**: 21.0.9 LTS (Eclipse Temurin)
- **Python Driver**: neo4j >= 5.0.0
- **Tested On**: Windows 10/11

## License

Neo4j Community Edition is licensed under GPL v3.
See: https://neo4j.com/licensing/

---

**Created**: 2025-11-16
**Last Updated**: 2025-11-16
**Status**: Production Ready
**AI Agent Compatible**: Yes
