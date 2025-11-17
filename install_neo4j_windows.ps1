# Neo4j Community Edition 5.26.0 - Windows User-Space Installer
# No administrator privileges required
# Can be run automatically by AI agents

param(
    [string]$InstallDir = "$env:USERPROFILE\.neo4j",
    [string]$Neo4jVersion = "5.26.0",
    [string]$InitialPassword = "research123"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Neo4j Community Edition $Neo4jVersion Installer" -ForegroundColor Cyan
Write-Host "User-Space Installation (No Admin Required)" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Java Installation
Write-Host "[1/7] Checking Java installation..." -ForegroundColor Yellow
$javaPath = "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot\bin\java.exe"
if (-not (Test-Path $javaPath)) {
    Write-Host "ERROR: Java not found at $javaPath" -ForegroundColor Red
    Write-Host "Please install Java 21 from https://adoptium.net/" -ForegroundColor Red
    exit 1
}

# Check Java version (java outputs to stderr, so we suppress errors)
$ErrorActionPreference = "SilentlyContinue"
$javaVersionOutput = & $javaPath -version 2>&1
$ErrorActionPreference = "Stop"
if ($javaVersionOutput) {
    $javaVersionMatch = $javaVersionOutput | Select-String "version" | Select-Object -First 1
    if ($javaVersionMatch) {
        Write-Host "  Java found: $($javaVersionMatch.ToString().Trim())" -ForegroundColor Green
    } else {
        Write-Host "  Java found (version check succeeded)" -ForegroundColor Green
    }
} else {
    Write-Host "  Java found" -ForegroundColor Green
}

# Set JAVA_HOME environment variable for this session
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
Write-Host "  JAVA_HOME set to: $env:JAVA_HOME" -ForegroundColor Green

# 2. Create installation directory
Write-Host "[2/7] Creating installation directory..." -ForegroundColor Yellow
$neo4jDir = Join-Path $InstallDir "neo4j-community-$Neo4jVersion"
if (Test-Path $InstallDir) {
    Write-Host "  Cleaning existing installation..." -ForegroundColor Yellow
    Remove-Item -Path $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Write-Host "  Installation directory: $neo4jDir" -ForegroundColor Green

# 3. Download Neo4j
Write-Host "[3/7] Downloading Neo4j Community Edition $Neo4jVersion..." -ForegroundColor Yellow
$downloadUrl = "https://dist.neo4j.org/neo4j-community-$Neo4jVersion-windows.zip"
$zipFile = Join-Path $InstallDir "neo4j-community-$Neo4jVersion-windows.zip"

try {
    # Use .NET WebClient for better progress and reliability
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $zipFile)
    Write-Host "  Downloaded: $zipFile" -ForegroundColor Green
    $fileSize = (Get-Item $zipFile).Length / 1MB
    Write-Host "  Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to download Neo4j" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# 4. Extract Neo4j
Write-Host "[4/7] Extracting Neo4j archive..." -ForegroundColor Yellow
try {
    # Use .NET ZipFile for reliable extraction
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipFile, $InstallDir)
    Write-Host "  Extracted to: $InstallDir" -ForegroundColor Green

    # Verify extraction
    $expectedFolders = @("bin", "conf", "data", "lib", "logs", "plugins")
    $missingFolders = @()
    foreach ($folder in $expectedFolders) {
        $folderPath = Join-Path $neo4jDir $folder
        if (-not (Test-Path $folderPath)) {
            $missingFolders += $folder
        }
    }

    if ($missingFolders.Count -gt 0) {
        Write-Host "ERROR: Extraction incomplete. Missing folders: $($missingFolders -join ', ')" -ForegroundColor Red
        exit 1
    }

    Write-Host "  All required folders extracted successfully" -ForegroundColor Green

    # Clean up zip file
    Remove-Item $zipFile -Force
    Write-Host "  Cleaned up archive file" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to extract Neo4j" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# 5. Configure Neo4j
Write-Host "[5/7] Configuring Neo4j..." -ForegroundColor Yellow
$confFile = Join-Path $neo4jDir "conf\neo4j.conf"

# Backup original config
Copy-Item $confFile "$confFile.original" -Force

# Add/modify configuration - read existing config first
$existingConfig = Get-Content $confFile -Raw

# Add configuration only if not already present
$config = @"

# User-space configuration (added by installer)
server.default_listen_address=127.0.0.1
server.bolt.listen_address=:7687
server.http.listen_address=:7474

# Initial password will be set via neo4j-admin
dbms.security.auth_enabled=true

# Memory settings for user-space (adjust based on available RAM)
server.memory.heap.initial_size=512m
server.memory.heap.max_size=1g
server.memory.pagecache.size=512m
"@

# Only add if not already added
if ($existingConfig -notmatch "User-space configuration") {
    Add-Content -Path $confFile -Value $config
}
Write-Host "  Configuration file updated: $confFile" -ForegroundColor Green

# 6. Set initial password
Write-Host "[6/7] Setting initial password..." -ForegroundColor Yellow
try {
    # Use neo4j-admin set-initial-password
    $neo4jAdminPath = Join-Path $neo4jDir "bin\neo4j-admin.bat"

    # Run neo4j-admin with proper environment
    $env:NEO4J_HOME = $neo4jDir
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = "cmd.exe"
    $processInfo.Arguments = "/c `"$neo4jAdminPath`" dbms set-initial-password $InitialPassword"
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $processInfo.UseShellExecute = $false
    $processInfo.WorkingDirectory = $neo4jDir

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo
    $process.Start() | Out-Null
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    if ($process.ExitCode -eq 0) {
        Write-Host "  Initial password set successfully" -ForegroundColor Green
    } else {
        Write-Host "  Output: $stdout" -ForegroundColor Yellow
        Write-Host "  Error: $stderr" -ForegroundColor Yellow
        Write-Host "  Password configuration may require manual setup" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING: Could not set initial password automatically" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host "  You may need to set it on first connection" -ForegroundColor Yellow
}

# 7. Start Neo4j (using console mode in background)
Write-Host "[7/7] Starting Neo4j in console mode..." -ForegroundColor Yellow
try {
    $neo4jPath = Join-Path $neo4jDir "bin\neo4j.bat"
    $env:NEO4J_HOME = $neo4jDir

    # Start Neo4j console in a new PowerShell window (background process)
    Write-Host "  Starting Neo4j console in background..." -ForegroundColor Yellow
    $neo4jProcess = Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-NoExit", "-Command", "& '$neo4jPath' console" `
        -WorkingDirectory $neo4jDir `
        -WindowStyle Minimized `
        -PassThru

    Write-Host "  Neo4j process started (PID: $($neo4jProcess.Id))" -ForegroundColor Green
    Write-Host "  Waiting for Neo4j to initialize (20 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20

    # Verify Neo4j is running
    $portTest = Test-NetConnection -ComputerName localhost -Port 7687 -WarningAction SilentlyContinue
    if ($portTest.TcpTestSucceeded) {
        Write-Host "  Neo4j is running on bolt://localhost:7687" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Neo4j may not be fully started on port 7687" -ForegroundColor Yellow
        Write-Host "  Give it a few more seconds and check logs at: $neo4jDir\logs\" -ForegroundColor Yellow
    }

    # Also check HTTP port
    $httpPortTest = Test-NetConnection -ComputerName localhost -Port 7474 -WarningAction SilentlyContinue
    if ($httpPortTest.TcpTestSucceeded) {
        Write-Host "  Neo4j Browser is available at http://localhost:7474" -ForegroundColor Green
    }

} catch {
    Write-Host "WARNING: Could not start Neo4j automatically" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To start manually, run:" -ForegroundColor Yellow
    Write-Host "  $neo4jDir\bin\neo4j.bat console" -ForegroundColor White
}

# Summary
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Installation Summary" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Installation Directory: $neo4jDir" -ForegroundColor White
Write-Host "Bolt URL: bolt://localhost:7687" -ForegroundColor White
Write-Host "HTTP URL: http://localhost:7474" -ForegroundColor White
Write-Host "Username: neo4j" -ForegroundColor White
Write-Host "Password: $InitialPassword" -ForegroundColor White
Write-Host ""
Write-Host "Manual Commands:" -ForegroundColor Yellow
Write-Host "  Start:   $neo4jDir\bin\neo4j.bat start" -ForegroundColor White
Write-Host "  Stop:    $neo4jDir\bin\neo4j.bat stop" -ForegroundColor White
Write-Host "  Status:  $neo4jDir\bin\neo4j.bat status" -ForegroundColor White
Write-Host "  Console: $neo4jDir\bin\neo4j.bat console" -ForegroundColor White
Write-Host ""
Write-Host "Logs Directory: $neo4jDir\logs\" -ForegroundColor White
Write-Host "===============================================" -ForegroundColor Cyan
