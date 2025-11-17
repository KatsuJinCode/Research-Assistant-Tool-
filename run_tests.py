#!/usr/bin/env python3
"""
Test runner script for Research Verification Agent System.

Provides convenient commands for running different test suites.
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print status."""
    print("=" * 80)
    print(f"  {description}")
    print("=" * 80)
    print(f"Running: {cmd}")
    print()

    result = subprocess.run(cmd, shell=True)

    print()
    if result.returncode == 0:
        print(f"[PASS] {description}")
    else:
        print(f"[FAIL] {description}")
        return False

    print()
    return True


def main():
    """Main test runner."""

    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <command>")
        print()
        print("Commands:")
        print("  all          - Run all tests")
        print("  unit         - Run only unit tests")
        print("  integration  - Run only integration tests")
        print("  critical     - Run only critical tests")
        print("  fast         - Run fast tests (exclude slow)")
        print("  coverage     - Run tests with coverage report")
        print("  qualifier    - Run only qualifier extractor tests (CRITICAL)")
        print("  pdf          - Run only PDF extractor tests")
        print("  watch        - Run tests in watch mode (requires pytest-watch)")
        print()
        return 1

    command = sys.argv[1]

    # Ensure we're in the project root
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Test commands
    commands = {
        "all": (
            "pytest -v",
            "All Tests"
        ),
        "unit": (
            "pytest -v -m unit",
            "Unit Tests Only"
        ),
        "integration": (
            "pytest -v -m integration",
            "Integration Tests Only"
        ),
        "critical": (
            "pytest -v -m critical",
            "Critical Tests Only (Must Always Pass)"
        ),
        "fast": (
            "pytest -v -m 'not slow'",
            "Fast Tests (Exclude Slow)"
        ),
        "coverage": (
            "pytest -v --cov=research_agent --cov-report=term-missing --cov-report=html",
            "Tests with Coverage Report"
        ),
        "qualifier": (
            "pytest -v tests/unit/test_qualifier_extractor.py",
            "Qualifier Extractor Tests (CRITICAL)"
        ),
        "pdf": (
            "pytest -v tests/unit/test_pdf_extractor.py",
            "PDF Extractor Tests"
        ),
        "watch": (
            "pytest-watch -- -v",
            "Watch Mode (Auto-rerun on changes)"
        )
    }

    if command not in commands:
        print(f"[ERROR] Unknown command: {command}")
        print()
        print("Run without arguments to see available commands.")
        return 1

    cmd, description = commands[command]
    success = run_command(cmd, description)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
