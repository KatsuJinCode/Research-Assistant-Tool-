#!/usr/bin/env python3
"""
CLEAN RESTART SCRIPT - Ensures NO stale code is running

This script:
1. Kills ALL Python processes (no survivors!)
2. Generates a new build hash for cache busting
3. Starts fresh server with version tracking
4. Opens browser with cache-busting timestamp

Usage:
    python restart_clean.py
"""

import subprocess
import sys
import time
import hashlib
import os
from datetime import datetime
from pathlib import Path

def get_build_hash():
    """Generate hash of critical files to detect changes."""
    files_to_hash = [
        'web_ui/document_processor.py',
        'web_ui/app.py',
        'backend/database/repositories/claim_repository.py',
        'backend/database/event_emitter.py'
    ]

    hasher = hashlib.md5()
    for filepath in files_to_hash:
        if Path(filepath).exists():
            with open(filepath, 'rb') as f:
                hasher.update(f.read())

    return hasher.hexdigest()[:8]

def kill_all_python():
    """Kill ALL Python processes - nuclear option."""
    print("[*] KILLING ALL PYTHON PROCESSES...")
    try:
        subprocess.run(
            ['powershell', '-Command', 'Stop-Process -Name python -Force'],
            capture_output=True
        )
        print("   [+] Killed all python.exe processes")
    except Exception as e:
        print(f"   [!] Failed to kill processes: {e}")

    # Wait for cleanup
    time.sleep(2)

def write_version_file(build_hash):
    """Write version file for UI to display."""
    version_data = {
        'build_hash': build_hash,
        'timestamp': datetime.now().isoformat(),
        'restart_count': get_restart_count() + 1
    }

    version_file = Path('web_ui/static/VERSION.json')
    import json
    with open(version_file, 'w') as f:
        json.dump(version_data, f, indent=2)

    print(f"[+] Version file written: {build_hash}")
    return version_data

def get_restart_count():
    """Get number of restarts today."""
    version_file = Path('web_ui/static/VERSION.json')
    if not version_file.exists():
        return 0

    import json
    with open(version_file) as f:
        data = json.load(f)
        return data.get('restart_count', 0)

def main():
    print("=" * 80)
    print("CLEAN RESTART - Ensuring fresh code with NO cache".center(80))
    print("=" * 80)
    print()

    # Step 1: Kill everything
    kill_all_python()

    # Step 2: Generate version info
    build_hash = get_build_hash()
    version_data = write_version_file(build_hash)

    print()
    print("[*] STARTING FRESH SERVER")
    print(f"   Build Hash: {build_hash}")
    print(f"   Restart #: {version_data['restart_count']}")
    print(f"   Time: {version_data['timestamp']}")
    print()
    print("=" * 80)
    print()

    # Step 3: Start server
    os.chdir('web_ui')

    # Start server with explicit environment to prevent auto-reload issues
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output

    # Use subprocess instead of os.system for better control
    try:
        subprocess.run([sys.executable, 'app.py'], env=env)
    except KeyboardInterrupt:
        print("\n\n[!] Server stopped by user")
        print("=" * 80)

if __name__ == '__main__':
    main()
