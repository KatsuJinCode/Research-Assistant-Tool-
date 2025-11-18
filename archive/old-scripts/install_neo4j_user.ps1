# Automatic Neo4j Installation for Windows (User-space, no admin required)
# Downloads, installs, and configures Neo4j Community Edition in user directory

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "         Neo4j Community Edition - User Installation" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$NEO4J_VERSION = "5.26.0"
$NEO4J_DOWNLOAD_URL = "https://dist.neo4j.org/neo4j-community-$NEO4J_VERSION-windows.zip"
$USER_HOME = $env:USERPROFILE
$INSTALL_DIR = "$USER_HOME\.neo4j\neo4j-community-$NEO4J_VERSION"
$NEO4J_HOME = $INSTALL_DIR
$NEO4J_PASSWORD = "research123"
$TEMP_DIR = "$env:TEMP\neo4j_install"

Write-Host "Installing Neo4j to user directory (no admin required):" -ForegroundColor Green
Write-Host "  $INSTALL_DIR" -ForegroundColor Cyan
Write-Host ""

# Check if Neo4j already installed and running
if (Test-Path $INSTALL_DIR) {
    Write-Host "Neo4j is already installed at: $INSTALL_DIR" -ForegroundColor Yellow

    # Check if running
    $neo4jProcess = Get-Process -Name "java" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*neo4j*" }
    if ($neo4jProcess) {
        Write-Host "Neo4j appears to be running. Stopping..." -ForegroundColor Yellow
        Stop-Process -Id $neo4jProcess.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    Write-Host "Using existing installation." -ForegroundColor Green
    Write-Host ""

    # Start Neo4j
    Write-Host "Starting Neo4j..." -ForegroundColor Cyan
    Start-Process -FilePath "$INSTALL_DIR\bin\neo4j.bat" -ArgumentList "console" -WindowStyle Hidden
    Start-Sleep -Seconds 5

    Write-Host "[SUCCESS] Neo4j is running!" -ForegroundColor Green
    Write-Host "  URL: http://localhost:7474" -ForegroundColor Cyan
    Write-Host "  Bolt: bolt://localhost:7687" -ForegroundColor Cyan
    Write-Host "  Username: neo4j" -ForegroundColor Cyan
    Write-Host "  Password: $NEO4J_PASSWORD" -ForegroundColor Cyan
    exit 0
}

# Create temp directory
New-Item -ItemType Directory -Force -Path $TEMP_DIR | Out-Null

# Check for Java
Write-Host "[1/6] Checking Java installation..." -ForegroundColor Cyan
$javaVersion = $null

# Try standard java command first
try {
    $javaVersion = & java -version 2>&1 | Select-String -Pattern "version" | ForEach-Object { $_.Line }
    Write-Host "  Found: $javaVersion" -ForegroundColor Green
} catch {
    # Try to find Java in common locations
    $javaLocations = @(
        "C:\Program Files\Eclipse Adoptium\jdk-21*\bin\java.exe",
        "C:\Program Files\Java\jdk-21*\bin\java.exe",
        "C:\Program Files\AdoptOpenJDK\jdk-21*\bin\java.exe",
        "$env:ProgramFiles\Eclipse Adoptium\jdk-21*\bin\java.exe"
    )

    $javaPath = $null
    foreach ($location in $javaLocations) {
        $found = Get-Item $location -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $javaPath = $found.FullName
            break
        }
    }

    if ($javaPath) {
        $javaDir = Split-Path (Split-Path $javaPath -Parent) -Parent
        $env:JAVA_HOME = $javaDir
        $env:PATH = "$(Split-Path $javaPath -Parent);$env:PATH"

        try {
            $versionOutput = & $javaPath -version 2>&1
            $javaVersion = ($versionOutput | Select-String -Pattern "version" | Select-Object -First 1).Line
        } catch {
            $javaVersion = "Java 21"
        }
        Write-Host "  Found: $javaVersion" -ForegroundColor Green
        Write-Host "  Location: $javaDir" -ForegroundColor Cyan
    } else {
        Write-Host "  Java not found!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install Java 21 or later:" -ForegroundColor Yellow
        Write-Host "  Download: https://adoptium.net/" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Or install via Chocolatey:" -ForegroundColor Yellow
        Write-Host "  choco install temurin21" -ForegroundColor Cyan
        exit 1
    }
}

# Download Neo4j
Write-Host ""
Write-Host "[2/6] Downloading Neo4j Community $NEO4J_VERSION..." -ForegroundColor Cyan
$zipFile = "$TEMP_DIR\neo4j.zip"

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($NEO4J_DOWNLOAD_URL, $zipFile)
    Write-Host "  Downloaded: $(([System.IO.FileInfo]$zipFile).Length / 1MB) MB" -ForegroundColor Green
} catch {
    Write-Host "  Failed to download Neo4j: $_" -ForegroundColor Red
    exit 1
}

# Extract Neo4j
Write-Host ""
Write-Host "[3/6] Extracting Neo4j..." -ForegroundColor Cyan
try {
    # Create parent directory
    $parentDir = Split-Path $INSTALL_DIR -Parent
    New-Item -ItemType Directory -Force -Path $parentDir | Out-Null

    # Extract
    Expand-Archive -Path $zipFile -DestinationPath $parentDir -Force
    Write-Host "  Extracted to: $INSTALL_DIR" -ForegroundColor Green
} catch {
    Write-Host "  Failed to extract: $_" -ForegroundColor Red
    exit 1
}

# Configure Neo4j
Write-Host ""
Write-Host "[4/6] Configuring Neo4j..." -ForegroundColor Cyan

$configFile = "$INSTALL_DIR\conf\neo4j.conf"

# Uncomment and set key configurations
$config = Get-Content $configFile

# Set data directory to user space
$config = $config -replace '#dbms.directories.data=.*', "dbms.directories.data=$INSTALL_DIR/data"

# Enable remote connections
$config = $config -replace '#server.default_listen_address=.*', 'server.default_listen_address=0.0.0.0'

# Set memory limits appropriate for development
$config = $config -replace '#server.memory.heap.initial_size=.*', 'server.memory.heap.initial_size=512m'
$config = $config -replace '#server.memory.heap.max_size=.*', 'server.memory.heap.max_size=1g'

Set-Content -Path $configFile -Value $config
Write-Host "  Configuration updated" -ForegroundColor Green

# Set initial password
Write-Host ""
Write-Host "[5/6] Setting initial password..." -ForegroundColor Cyan
try {
    & "$INSTALL_DIR\bin\neo4j-admin.bat" dbms set-initial-password $NEO4J_PASSWORD
    Write-Host "  Password set to: $NEO4J_PASSWORD" -ForegroundColor Green
} catch {
    Write-Host "  Warning: Could not set password automatically" -ForegroundColor Yellow
    Write-Host "  You may need to set it on first login" -ForegroundColor Yellow
}

# Create .env file
Write-Host ""
Write-Host "[6/6] Creating .env file..." -ForegroundColor Cyan
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = "$projectRoot\.env"

$envContent = @"
# Neo4j Connection Settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=$NEO4J_PASSWORD

# Research Agent Settings
RESEARCH_AGENT_ENV=development
"@

Set-Content -Path $envFile -Value $envContent
Write-Host "  Created .env file: $envFile" -ForegroundColor Green

# Add to PATH for current session
$env:PATH = "$INSTALL_DIR\bin;$env:PATH"

# Start Neo4j
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Starting Neo4j..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

try {
    # Start in console mode in background
    Start-Process -FilePath "$INSTALL_DIR\bin\neo4j.bat" -ArgumentList "console" -WindowStyle Hidden

    Write-Host "Waiting for Neo4j to start (may take 10-20 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15

    # Test connection
    $testUrl = "http://localhost:7474"
    try {
        $response = Invoke-WebRequest -Uri $testUrl -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host ""
            Write-Host "============================================================================" -ForegroundColor Green
            Write-Host "                   Neo4j SUCCESSFULLY INSTALLED!" -ForegroundColor Green
            Write-Host "============================================================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "Connection Details:" -ForegroundColor Cyan
            Write-Host "  Browser:  http://localhost:7474" -ForegroundColor White
            Write-Host "  Bolt:     bolt://localhost:7687" -ForegroundColor White
            Write-Host "  Username: neo4j" -ForegroundColor White
            Write-Host "  Password: $NEO4J_PASSWORD" -ForegroundColor White
            Write-Host ""
            Write-Host "Installation Directory:" -ForegroundColor Cyan
            Write-Host "  $INSTALL_DIR" -ForegroundColor White
            Write-Host ""
            Write-Host "To stop Neo4j:" -ForegroundColor Cyan
            Write-Host "  Stop the Java process running Neo4j" -ForegroundColor White
            Write-Host ""
        }
    } catch {
        Write-Host "Neo4j started but web interface not responding yet." -ForegroundColor Yellow
        Write-Host "Give it a few more seconds and check: http://localhost:7474" -ForegroundColor Yellow
    }

} catch {
    Write-Host "Failed to start Neo4j: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "To start manually:" -ForegroundColor Yellow
    Write-Host "  cd $INSTALL_DIR" -ForegroundColor Cyan
    Write-Host "  .\bin\neo4j.bat console" -ForegroundColor Cyan
    exit 1
}

# Cleanup
Write-Host "Cleaning up temporary files..." -ForegroundColor Cyan
Remove-Item -Path $TEMP_DIR -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[SUCCESS] Installation complete!" -ForegroundColor Green
Write-Host ""
