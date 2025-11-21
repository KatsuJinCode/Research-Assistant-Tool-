# Research Verification Agent System - Auto-Install Script for Windows
# PowerShell version - Run with: powershell -ExecutionPolicy Bypass -File auto_install.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "       RESEARCH VERIFICATION AGENT - AUTO-INSTALLER (Windows)" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green

    # Extract version number
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Host "  ERROR: Python 3.11+ required. Found: $pythonVersion" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "  ERROR: Python not found. Please install Python 3.11+" -ForegroundColor Red
    Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check pip
Write-Host ""
Write-Host "Checking pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "  Found: pip" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: pip not found" -ForegroundColor Red
    exit 1
}

# Install core dependencies
Write-Host ""
Write-Host "Installing core Python dependencies..." -ForegroundColor Yellow
Write-Host "  (This may take a few minutes)" -ForegroundColor Gray
try {
    pip install -r requirements.txt 2>&1 | Out-Null
    Write-Host "  Core dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Failed to install core dependencies" -ForegroundColor Red
    Write-Host "  Run manually: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Install test dependencies
Write-Host ""
Write-Host "Installing test dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements-test.txt 2>&1 | Out-Null
    Write-Host "  Test dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "  WARNING: Failed to install test dependencies" -ForegroundColor Yellow
}

# Install Neo4j Python driver
Write-Host ""
Write-Host "Installing Neo4j Python driver..." -ForegroundColor Yellow
try {
    pip install -r requirements-neo4j.txt 2>&1 | Out-Null
    Write-Host "  Neo4j Python driver installed successfully" -ForegroundColor Green
} catch {
    Write-Host "  WARNING: Failed to install Neo4j driver" -ForegroundColor Yellow
}

# Run critical tests
Write-Host ""
Write-Host "Running critical tests..." -ForegroundColor Yellow
try {
    $env:PYTHONIOENCODING = "utf-8"
    python run_tests.py critical 2>&1 | Out-String | Write-Host
    Write-Host "  Tests completed" -ForegroundColor Green
} catch {
    Write-Host "  WARNING: Some tests may have failed" -ForegroundColor Yellow
}

# Check for Docker
Write-Host ""
Write-Host "Checking for Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "  Found: $dockerVersion" -ForegroundColor Green

    # Check if Docker is running
    try {
        docker ps 2>&1 | Out-Null
        Write-Host "  Docker is running" -ForegroundColor Green

        # Offer to install Neo4j via Docker
        Write-Host ""
        $installNeo4j = Read-Host "Would you like to install Neo4j via Docker? (y/n)"
        if ($installNeo4j -eq "y" -or $installNeo4j -eq "Y") {
            Write-Host ""
            Write-Host "Installing Neo4j via Docker..." -ForegroundColor Yellow

            # Create directories
            New-Item -ItemType Directory -Force -Path "neo4j\data" | Out-Null
            New-Item -ItemType Directory -Force -Path "neo4j\logs" | Out-Null
            New-Item -ItemType Directory -Force -Path "neo4j\import" | Out-Null
            New-Item -ItemType Directory -Force -Path "neo4j\plugins" | Out-Null

            # Check if container exists
            $existing = docker ps -a --filter "name=research-neo4j" --format "{{.Names}}" 2>&1
            if ($existing -eq "research-neo4j") {
                Write-Host "  Container 'research-neo4j' already exists" -ForegroundColor Yellow
                $recreate = Read-Host "  Remove and recreate? (y/n)"
                if ($recreate -eq "y" -or $recreate -eq "Y") {
                    docker rm -f research-neo4j 2>&1 | Out-Null
                }
            }

            # Run Neo4j container
            docker run `
                --name research-neo4j `
                -p7474:7474 -p7687:7687 `
                -d `
                -v "${PWD}\neo4j\data:/data" `
                -v "${PWD}\neo4j\logs:/logs" `
                -v "${PWD}\neo4j\import:/var/lib/neo4j/import" `
                -v "${PWD}\neo4j\plugins:/plugins" `
                --env NEO4J_AUTH=neo4j/research123 `
                neo4j:latest 2>&1 | Out-Null

            Write-Host "  Neo4j container started" -ForegroundColor Green
            Write-Host "  Waiting for Neo4j to start (30 seconds)..." -ForegroundColor Gray
            Start-Sleep -Seconds 30

            # Create .env file
            @"
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=research123
NEO4J_DATABASE=neo4j
"@ | Out-File -FilePath ".env" -Encoding UTF8

            Write-Host "  Created .env file" -ForegroundColor Green
            Write-Host ""
            Write-Host "  Neo4j is ready!" -ForegroundColor Green
            Write-Host "  Browser: http://localhost:7474" -ForegroundColor Cyan
            Write-Host "  Username: neo4j" -ForegroundColor Cyan
            Write-Host "  Password: research123" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "  Docker Desktop is not running" -ForegroundColor Yellow
        Write-Host "  Please start Docker Desktop to use Neo4j" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Docker not found" -ForegroundColor Yellow
    Write-Host "  Neo4j installation skipped" -ForegroundColor Yellow
    Write-Host "  Install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
}

# Summary
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "                    INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run tests: python run_tests.py critical" -ForegroundColor White
Write-Host "  2. Test research APIs: python -c \"import arxiv; print('OK')\"" -ForegroundColor White
Write-Host "  3. Extract claims: python extract_and_cluster_claims.py" -ForegroundColor White
if (Test-Path ".env") {
    Write-Host "  4. Migrate to Neo4j: python migrate_to_neo4j.py" -ForegroundColor White
}
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  - STATUS.md: Complete system status" -ForegroundColor White
Write-Host "  - HANDOFF_TO_CLI.md: This handoff document" -ForegroundColor White
Write-Host "  - tests/README.md: Testing guide" -ForegroundColor White
Write-Host ""
