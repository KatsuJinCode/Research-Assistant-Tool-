#!/usr/bin/env python3
"""
Setup script for CLI Research Assistant
Auto-installs dependencies needed for the CLI tool.
"""

import subprocess
import sys
import os


def install_package(package):
    """Install a Python package using pip."""
    print(f"Installing {package}...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet", package
        ])
        print(f"[OK] {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[X] Failed to install {package}: {e}")
        return False


def main():
    """Install all required dependencies."""
    print("=" * 80)
    print("CLI Research Assistant - Dependency Setup")
    print("=" * 80)
    print()

    # Minimal dependencies for CLI tool
    dependencies = [
        "openai",  # For AI features
    ]

    print(f"Installing {len(dependencies)} package(s)...\n")

    failed = []
    for package in dependencies:
        if not install_package(package):
            failed.append(package)
        print()

    print("=" * 80)
    if failed:
        print(f"[WARNING] Setup completed with {len(failed)} error(s)")
        print("Failed packages:", ", ".join(failed))
        print("\nYou can try installing them manually with:")
        print(f"  pip install {' '.join(failed)}")
    else:
        print("[OK] All dependencies installed successfully!")

    print("\nNext steps:")
    print("1. Set your OpenAI API key:")
    print("   export OPENAI_API_KEY='your-api-key-here'")
    print("\n2. Create a test project:")
    print("   python cli_assistant.py create-project \"My Research\"")
    print("\n3. Add a document:")
    print("   python cli_assistant.py add-document 1 sample_document.txt")
    print("\n4. Try AI features:")
    print("   python cli_assistant.py summarize 1")
    print("=" * 80)


if __name__ == "__main__":
    main()
