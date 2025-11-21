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

REM Install Neo4j (Windows native - no Docker needed!)
echo.
echo Checking for Neo4j...
where neo4j >nul 2>&1
if errorlevel 1 (
    echo   Neo4j not found
    set /p INSTALL_NEO4J="Would you like to install Neo4j Community Edition? (y/n): "
    if /i "%INSTALL_NEO4J%"=="y" (
        echo.
        echo   Installing Neo4j via PowerShell...
        echo   ^(This requires Administrator privileges^)
        echo.
        powershell -ExecutionPolicy Bypass -File "%~dp0install_neo4j_windows.ps1"
        if errorlevel 1 (
            echo   WARNING: Neo4j installation failed or was cancelled
            echo   You can install manually later with:
            echo   powershell -ExecutionPolicy Bypass -File install_neo4j_windows.ps1
        ) else (
            echo.
            echo   Neo4j installed successfully!
        )
    ) else (
        echo   Skipping Neo4j installation
        echo   ^(You can install later with: install_neo4j_windows.ps1^)
    )
) else (
    echo   Neo4j already installed!
    neo4j status
)

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
