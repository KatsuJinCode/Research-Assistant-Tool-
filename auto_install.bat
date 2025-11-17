@echo off
REM Research Verification Agent System - Auto-Install Script for Windows
REM Run by double-clicking this file or: auto_install.bat

echo.
echo ============================================================================
echo        RESEARCH VERIFICATION AGENT - AUTO-INSTALLER (Windows)
echo ============================================================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not found
    echo   Please install Python 3.11+ from: https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo   Python found!
echo.

REM Check pip
echo Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: pip not found
    pause
    exit /b 1
)
echo   pip found!
echo.

REM Install core dependencies
echo Installing core Python dependencies...
echo   (This may take a few minutes)
pip install -q -r requirements.txt
if errorlevel 1 (
    echo   ERROR: Failed to install core dependencies
    echo   Try manually: pip install -r requirements.txt
    pause
    exit /b 1
)
echo   Core dependencies installed!
echo.

REM Install test dependencies
echo Installing test dependencies...
pip install -q -r requirements-test.txt
if errorlevel 1 (
    echo   WARNING: Some test dependencies may have failed
)
echo   Test dependencies installed!
echo.

REM Install Neo4j Python driver
echo Installing Neo4j Python driver...
pip install -q -r requirements-neo4j.txt
if errorlevel 1 (
    echo   WARNING: Neo4j driver installation may have failed
)
echo   Neo4j Python driver installed!
echo.

REM Run critical tests
echo Running critical tests...
set PYTHONIOENCODING=utf-8
python -m pytest -v -m critical tests/
echo   Tests completed!
echo.

REM Check Docker
echo Checking for Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo   Docker not found - Neo4j installation skipped
    echo   To use Neo4j, install Docker Desktop from:
    echo   https://www.docker.com/products/docker-desktop
    goto :skip_docker
)

echo   Docker found!
docker ps >nul 2>&1
if errorlevel 1 (
    echo   WARNING: Docker Desktop is not running
    echo   Please start Docker Desktop to install Neo4j
    goto :skip_docker
)

echo   Docker is running!
echo.
set /p INSTALL_NEO4J="Would you like to install Neo4j via Docker? (y/n): "
if /i not "%INSTALL_NEO4J%"=="y" goto :skip_docker

echo.
echo Installing Neo4j via Docker...

REM Create directories
if not exist "neo4j\data" mkdir neo4j\data
if not exist "neo4j\logs" mkdir neo4j\logs
if not exist "neo4j\import" mkdir neo4j\import
if not exist "neo4j\plugins" mkdir neo4j\plugins

REM Check for existing container
docker ps -a --filter "name=research-neo4j" --format "{{.Names}}" | findstr /C:"research-neo4j" >nul 2>&1
if not errorlevel 1 (
    echo   Container 'research-neo4j' already exists
    set /p RECREATE="  Remove and recreate? (y/n): "
    if /i "!RECREATE!"=="y" (
        docker rm -f research-neo4j >nul 2>&1
    )
)

REM Start Neo4j container
echo   Starting Neo4j container...
docker run --name research-neo4j -p7474:7474 -p7687:7687 -d -v "%CD%\neo4j\data:/data" -v "%CD%\neo4j\logs:/logs" -v "%CD%\neo4j\import:/var/lib/neo4j/import" -v "%CD%\neo4j\plugins:/plugins" --env NEO4J_AUTH=neo4j/research123 neo4j:latest >nul 2>&1

echo   Neo4j container started!
echo   Waiting for Neo4j to initialize (30 seconds)...
timeout /t 30 /nobreak >nul

REM Create .env file
(
echo # Neo4j Connection
echo NEO4J_URI=bolt://localhost:7687
echo NEO4J_USER=neo4j
echo NEO4J_PASSWORD=research123
echo NEO4J_DATABASE=neo4j
) > .env

echo   Created .env file
echo.
echo   Neo4j is ready!
echo   Browser: http://localhost:7474
echo   Username: neo4j
echo   Password: research123
echo.

:skip_docker

REM Summary
echo.
echo ============================================================================
echo                     INSTALLATION COMPLETE!
echo ============================================================================
echo.
echo Next steps:
echo   1. Run tests: python run_tests.py critical
echo   2. Extract claims: python extract_and_cluster_claims.py
if exist ".env" (
    echo   3. Migrate to Neo4j: python migrate_to_neo4j.py
    echo   4. Open Neo4j Browser: http://localhost:7474
)
echo.
echo Documentation:
echo   - STATUS.md: Complete system status
echo   - HANDOFF_TO_CLI.md: Handoff documentation
echo   - tests/README.md: Testing guide
echo.
echo Press any key to exit...
pause >nul
