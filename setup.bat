@echo off
REM Windows setup script for Research Assistant
REM This runs the Python setup which works on all platforms

echo Running Research Assistant Setup...
echo.

python setup_interactive.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Python is required but not found.
    echo Please install Python 3.7+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

pause
