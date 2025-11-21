# Fix Neo4j Authentication - Complete Reset

$ErrorActionPreference = "Stop"

Write-Host "Fixing Neo4j Authentication..." -ForegroundColor Cyan

# Step 1: Stop all Java processes
Write-Host "[1/5] Stopping Neo4j..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -eq 'java'} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# Step 2: Delete data directory
Write-Host "[2/5] Deleting Neo4j data directory..." -ForegroundColor Yellow
$dataDir = "$env:USERPROFILE\.neo4j\neo4j-community-5.26.0\data"
if (Test-Path $dataDir) {
    Remove-Item -Path $dataDir -Recurse -Force
    Write-Host "  Deleted: $dataDir" -ForegroundColor Green
}

# Step 3: Set Java environment
Write-Host "[3/5] Setting up Java environment..." -ForegroundColor Yellow
$javaPath = Get-Item "C:\Program Files\Eclipse Adoptium\jdk-21*\bin\java.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($javaPath) {
    $javaDir = Split-Path (Split-Path $javaPath.FullName -Parent) -Parent
    $env:JAVA_HOME = $javaDir
    $env:PATH = "$(Split-Path $javaPath.FullName -Parent);$env:PATH"
    Write-Host "  JAVA_HOME: $javaDir" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Java not found!" -ForegroundColor Red
    exit 1
}

# Step 4: Set initial password
Write-Host "[4/5] Setting initial password..." -ForegroundColor Yellow
$neo4jHome = "$env:USERPROFILE\.neo4j\neo4j-community-5.26.0"
& "$neo4jHome\bin\neo4j-admin.bat" dbms set-initial-password research123
Write-Host "  Password set to: research123" -ForegroundColor Green

# Step 5: Start Neo4j
Write-Host "[5/5] Starting Neo4j..." -ForegroundColor Yellow
Start-Process -FilePath "$neo4jHome\bin\neo4j.bat" -ArgumentList "console" -WindowStyle Hidden
Write-Host "  Waiting for startup (20 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Test connection
Write-Host ""
Write-Host "Testing connection..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:7474" -TimeoutSec 5 -UseBasicParsing
    Write-Host "[SUCCESS] Neo4j is running!" -ForegroundColor Green
    Write-Host "  URL: http://localhost:7474" -ForegroundColor White
    Write-Host "  Bolt: bolt://localhost:7687" -ForegroundColor White
    Write-Host "  Username: neo4j" -ForegroundColor White
    Write-Host "  Password: research123" -ForegroundColor White
} catch {
    Write-Host "[WARNING] Web interface not responding yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done! Now test with Python..." -ForegroundColor Cyan
