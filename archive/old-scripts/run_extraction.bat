@echo off
REM Simple wrapper to run extraction pipeline with proper encoding on Windows
set PYTHONIOENCODING=utf-8
python extract_and_cluster_claims.py
pause
