"""
Agent Auto-Detection and Setup Script

Automatically detects which AI CLI tools are available and configures the system.
"""

import subprocess
import sys
import json
from pathlib import Path

# Fix Windows unicode issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def check_cli_available(executable: str) -> bool:
    """Check if a CLI tool is available"""
    try:
        result = subprocess.run(
            [executable, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def detect_available_agents():
    """Detect which AI agent CLIs are installed"""
    agents = {
        'claude': ['claude', 'Claude Code'],
        'openai': ['openai', 'OpenAI Codex'],
        'gemini': ['gemini', 'Google Gemini'],
    }

    available = []
    for key, (exe, name) in agents.items():
        if check_cli_available(exe):
            available.append((key, exe, name))
            print(f"✓ Found {name} ({exe})")
        else:
            print(f"✗ {name} ({exe}) not found")

    return available


def save_agent_config(agent_type: str):
    """Save agent configuration to file"""
    config_file = Path(__file__).parent / 'web_ui' / 'agent_config.json'

    config_data = {'agent': agent_type}

    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)

    print(f"\n✓ Configuration saved to {config_file}")


def main():
    """Main setup routine"""
    print("=" * 60)
    print("AI Agent CLI Auto-Detection".center(60))
    print("=" * 60)
    print()

    # Detect available agents
    print("Scanning for installed AI CLI tools...\n")
    available = detect_available_agents()

    if not available:
        print("\n❌ No AI agent CLIs found!")
        print("\nPlease install one of the following:")
        print("  - Claude Code: https://code.claude.com/")
        print("  - OpenAI CLI: pip install openai")
        print("  - Google Gemini CLI: gcloud components install")
        print("\nOr configure a custom CLI in web_ui/agent_config.json")
        sys.exit(1)

    print(f"\n✓ Found {len(available)} agent(s)")

    # If multiple agents available, let user choose
    if len(available) > 1:
        print("\nMultiple AI agents detected. Please choose:")
        for i, (key, exe, name) in enumerate(available, 1):
            print(f"  {i}. {name} ({exe})")

        while True:
            try:
                choice = input("\nEnter number (1-{}): ".format(len(available)))
                idx = int(choice) - 1
                if 0 <= idx < len(available):
                    selected = available[idx]
                    break
                else:
                    print("Invalid choice, please try again.")
            except (ValueError, KeyboardInterrupt):
                print("\nSetup cancelled.")
                sys.exit(1)
    else:
        selected = available[0]

    agent_type, exe, name = selected
    print(f"\n✓ Selected: {name}")

    # Save configuration
    save_agent_config(agent_type)

    print("\n" + "=" * 60)
    print("Setup Complete!".center(60))
    print("=" * 60)
    print(f"\nConfigured to use: {name}")
    print("\nYou can now run:")
    print("  python web_ui/app.py")
    print("\nTo change agents later:")
    print("  - Set environment variable: AI_AGENT_CLI=<agent>")
    print("  - Edit: web_ui/agent_config.json")
    print("  - Run this script again: python setup_agent.py")
    print("\nSee AGENT_CONFIGURATION.md for details.")


if __name__ == '__main__':
    main()
