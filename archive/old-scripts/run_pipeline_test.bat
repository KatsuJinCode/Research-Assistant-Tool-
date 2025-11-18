@echo off
REM Windows wrapper for pipeline test with UTF-8 encoding
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
python test_full_pipeline.py
pause
