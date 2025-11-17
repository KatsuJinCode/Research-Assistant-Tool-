# Automatic Neo4j Installation for Windows
# Downloads, installs, and configures Neo4j Community Edition as a Windows Service
# No Docker required!

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "              Neo4j Community Edition - Auto Installer" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$NEO4J_VERSION = "5.26.0"  # Latest stable as of 2025
$NEO4J_DOWNLOAD_URL = "https://dist.neo4j.org/neo4j-community-$NEO4J_VERSION-windows.zip"
$INSTALL_DIR = "$env:ProgramFiles\Neo4j\neo4j-community-$NEO4J_VERSION"
$NEO4J_HOME = $INSTALL_DIR
$NEO4J_PASSWORD = "research123"

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges to install as a Windows service." -ForegroundColor Yellow
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Right-click PowerShell -> 'Run as Administrator'" -ForegroundColor Cyan
    exit 1
}

# Check if Neo4j already installed
if (Test-Path $INSTALL_DIR) {
    Write-Host "Neo4j is already installed at: $INSTALL_DIR" -ForegroundColor Yellow
    $reinstall = Read-Host "Reinstall? (y/n)"
    if ($reinstall -ne "y") {
        Write-Host "Using existing installation." -ForegroundColor Green
        exit 0
    }

    Write-Host "Stopping and removing existing service..." -ForegroundColor Yellow
    try {
        & "$INSTALL_DIR\bin\neo4j.bat" stop 2>$null
        & "$INSTALL_DIR\bin\neo4j.bat" uninstall-service 2>$null
    } catch {
        # Ignore errors if service doesn't exist
    }

    Write-Host "Removing existing installation..." -ForegroundColor Yellow
    Remove-Item -Path $INSTALL_DIR -Recurse -Force
}

# Check Java (required for Neo4j)
Write-Host "Checking for Java..." -ForegroundColor Yellow
try {
    $javaVersion = java -version 2>&1 | Select-String "version" | Select-Object -First 1
    Write-Host "  Found: $javaVersion" -ForegroundColor Green
} catch {
    Write-Host "  Java not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Neo4j requires Java 21+. Installing via Chocolatey..." -ForegroundColor Yellow

    # Check for Chocolatey
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host "  Installing Chocolatey first..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    }

    Write-Host "  Installing OpenJDK 21..." -ForegroundColor Yellow
    choco install openjdk21 -y

    # Refresh environment
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    Write-Host "  Java installed!" -ForegroundColor Green
}

# Create installation directory
Write-Host ""
Write-Host "Creating installation directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null

# Download Neo4j
Write-Host "Downloading Neo4j Community $NEO4J_VERSION..." -ForegroundColor Yellow
Write-Host "  URL: $NEO4J_DOWNLOAD_URL" -ForegroundColor Gray

$zipFile = "$env:TEMP\neo4j-community-$NEO4J_VERSION-windows.zip"

try {
    Invoke-WebRequest -Uri $NEO4J_DOWNLOAD_URL -OutFile $zipFile -UseBasicParsing
    Write-Host "  Download complete!" -ForegroundColor Green
} catch {
    Write-Host "  Download failed: $_" -ForegroundColor Red
    exit 1
}

# Extract Neo4j
Write-Host "Extracting Neo4j..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $zipFile -DestinationPath "$env:ProgramFiles\Neo4j" -Force
    Write-Host "  Extraction complete!" -ForegroundColor Green
} catch {
    Write-Host "  Extraction failed: $_" -ForegroundColor Red
    exit 1
}

# Clean up zip file
Remove-Item $zipFile -Force

# Set NEO4J_HOME environment variable
Write-Host "Setting NEO4J_HOME environment variable..." -ForegroundColor Yellow
[System.Environment]::SetEnvironmentVariable("NEO4J_HOME", $NEO4J_HOME, [System.EnvironmentVariableTarget]::Machine)
$env:NEO4J_HOME = $NEO4J_HOME
Write-Host "  NEO4J_HOME = $NEO4J_HOME" -ForegroundColor Green

# Configure Neo4j
Write-Host "Configuring Neo4j..." -ForegroundColor Yellow

$configFile = "$NEO4J_HOME\conf\neo4j.conf"

# Update config for research project
$config = Get-Content $configFile
$config = $config -replace "#server.default_listen_address=0.0.0.0", "server.default_listen_address=0.0.0.0"
$config = $config -replace "#server.bolt.enabled=true", "server.bolt.enabled=true"
$config = $config -replace "#server.http.enabled=true", "server.http.enabled=true"
$config | Set-Content $configFile

Write-Host "  Configuration updated!" -ForegroundColor Green

# Set initial password
Write-Host "Setting initial password..." -ForegroundColor Yellow
& "$NEO4J_HOME\bin\neo4j-admin.bat" dbms set-initial-password $NEO4J_PASSWORD 2>&1 | Out-Null
Write-Host "  Password set to: $NEO4J_PASSWORD" -ForegroundColor Green

# Install as Windows Service
Write-Host "Installing Neo4j as Windows Service..." -ForegroundColor Yellow
try {
    & "$NEO4J_HOME\bin\neo4j.bat" install-service
    Write-Host "  Service installed!" -ForegroundColor Green
} catch {
    Write-Host "  Service installation failed: $_" -ForegroundColor Yellow
    Write-Host "  You can still run Neo4j manually with: neo4j.bat console" -ForegroundColor Yellow
}

# Start Neo4j service
Write-Host "Starting Neo4j service..." -ForegroundColor Yellow
try {
    & "$NEO4J_HOME\bin\neo4j.bat" start
    Write-Host "  Neo4j service started!" -ForegroundColor Green
} catch {
    Write-Host "  Service start failed: $_" -ForegroundColor Yellow
    Write-Host "  Trying console mode..." -ForegroundColor Yellow
    Start-Process -FilePath "$NEO4J_HOME\bin\neo4j.bat" -ArgumentList "console" -NoNewWindow -PassThru
}

# Wait for Neo4j to start
Write-Host ""
Write-Host "Waiting for Neo4j to start (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Create .env file in project directory
Write-Host "Creating .env configuration file..." -ForegroundColor Yellow
$projectDir = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrEmpty($projectDir)) {
    $projectDir = (Get-Location).Path
}

$envContent = @"
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=$NEO4J_PASSWORD
NEO4J_DATABASE=neo4j
"@

$envFile = Join-Path $projectDir ".env"
$envContent | Out-File -FilePath $envFile -Encoding UTF8 -Force
Write-Host "  Created: $envFile" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "                   Neo4j Installation Complete!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Neo4j Browser: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:7474" -ForegroundColor Cyan
Write-Host "Username:      " -NoNewline -ForegroundColor White
Write-Host "neo4j" -ForegroundColor Cyan
Write-Host "Password:      " -NoNewline -ForegroundColor White
Write-Host "$NEO4J_PASSWORD" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installation:  " -NoNewline -ForegroundColor White
Write-Host "$NEO4J_HOME" -ForegroundColor Gray
Write-Host ""
Write-Host "Service Status:" -ForegroundColor White
& "$NEO4J_HOME\bin\neo4j.bat" status 2>&1
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Open Neo4j Browser: http://localhost:7474" -ForegroundColor White
Write-Host "  2. Test connection: python -c ""from research_agent.neo4j_database import Neo4jDatabase; db = Neo4jDatabase(); print('Connected!'); db.close()""" -ForegroundColor White
Write-Host "  3. Migrate data: python migrate_to_neo4j.py" -ForegroundColor White
Write-Host ""
