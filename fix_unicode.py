"""
Fix Unicode Issues - Replace all problematic Unicode characters with ASCII equivalents

This script finds and replaces Unicode emoji and special characters across all Python files
to prevent encoding issues on Windows (cp1252 codec).
"""

import os
import re
from pathlib import Path

# Mapping of Unicode characters to ASCII equivalents
UNICODE_REPLACEMENTS = {
    # Checkmarks and crosses
    '[OK]': '[OK]',
    '[X]': '[X]',
    '[SUCCESS]': '[SUCCESS]',
    '[FAIL]': '[FAIL]',

    # Warning and info
    '[WARNING]': '[WARNING]',
    '[WARNING]': '[WARNING]',
    '[INFO]': '[INFO]',
    '[INFO]': '[INFO]',

    # Emoji
    '[*]': '[*]',
    '[->]': '[->]',
    '[>>]': '[>>]',
    '[>>]': '[>>]',
    '[TREE]': '[TREE]',
    '[BOT]': '[BOT]',
    '[DOC]': '[DOC]',
    '[TOOL]': '[TOOL]',
    '[TARGET]': '[TARGET]',
    '[IDEA]': '[IDEA]',
    '[BOOK]': '[BOOK]',
    '[BUILD]': '[BUILD]',
    '[BUILD]': '[BUILD]',

    # Arrows
    '->': '->',
    '<-': '<-',
    '<->': '<->',

    # Box drawing (from tree structures)
    '+': '+',
    '-': '-',
    '+': '+',
    '|': '|',
}

def fix_unicode_in_file(file_path: Path) -> bool:
    """
    Fix Unicode characters in a single file.

    Returns:
        True if changes were made, False otherwise
    """
    try:
        # Read file
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # Replace all Unicode characters
        for unicode_char, ascii_equiv in UNICODE_REPLACEMENTS.items():
            content = content.replace(unicode_char, ascii_equiv)

        # Check if any changes were made
        if content != original_content:
            # Write back
            file_path.write_text(content, encoding='utf-8')
            return True

        return False

    except Exception as e:
        print(f"  [ERROR] Could not process {file_path}: {e}")
        return False


def fix_all_python_files(root_dir: Path):
    """Fix Unicode in all Python files."""
    print("=" * 80)
    print("FIXING UNICODE ISSUES IN PYTHON FILES".center(80))
    print("=" * 80 + "\n")

    python_files = list(root_dir.rglob("*.py"))

    print(f"Found {len(python_files)} Python files\n")

    fixed_count = 0

    for py_file in python_files:
        # Skip __pycache__ and .git directories
        if '__pycache__' in str(py_file) or '.git' in str(py_file):
            continue

        if fix_unicode_in_file(py_file):
            print(f"  [FIXED] {py_file.relative_to(root_dir)}")
            fixed_count += 1

    print(f"\n{fixed_count} files modified")

    if fixed_count == 0:
        print("\n[SUCCESS] No Unicode issues found in Python files!")
    else:
        print(f"\n[SUCCESS] Fixed Unicode issues in {fixed_count} files")


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent

    print(f"\nScanning directory: {root_dir}\n")

    # Fix Python files
    fix_all_python_files(root_dir)

    print("\n" + "=" * 80)
    print("COMPLETE".center(80))
    print("=" * 80)


if __name__ == "__main__":
    main()
