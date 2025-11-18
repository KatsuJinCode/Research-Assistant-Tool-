#!/usr/bin/env python3
"""
Interactive Setup for Research Assistant - Cross-Platform
Works on Windows, macOS, and Linux
"""

import os
import sys
import subprocess
import re
from pathlib import Path

CONFIG_FILE = ".research_config"

def print_header(text):
    """Print a formatted header."""
    border = "=" * 60
    print(f"\n{border}")
    print(f"  {text}")
    print(f"{border}\n")

def print_section(text):
    """Print a section divider."""
    print(f"\n{'-' * 60}")
    print(f"{text}")
    print(f"{'-' * 60}\n")

def check_python():
    """Check Python version."""
    version = sys.version_info
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro} found")
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("[FAIL] Error: Python 3.7+ is required")
        sys.exit(1)

def install_dependencies():
    """Install required Python packages."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet",
            "--upgrade", "pip"
        ], stderr=subprocess.DEVNULL)

        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet",
            "openai", "anthropic"
        ])
        print("[OK] Dependencies installed (OpenAI + Anthropic)\n")
        return True
    except subprocess.CalledProcessError:
        print("[WARNING] Warning: Some dependencies may not have installed correctly\n")
        return False

def validate_openai_key(key):
    """Validate OpenAI API key format."""
    return bool(re.match(r'^sk-[a-zA-Z0-9]{32,}$', key) or
                re.match(r'^sk-proj-[a-zA-Z0-9_-]{32,}$', key))

def validate_anthropic_key(key):
    """Validate Anthropic API key format."""
    return bool(re.match(r'^sk-ant-[a-zA-Z0-9_-]{32,}$', key))

def configure_openai():
    """Configure OpenAI provider."""
    print_section("OpenAI Configuration (ChatGPT)")

    response = input("Do you have an OpenAI API key? (y/n): ").strip().lower()
    print()

    if response != 'y':
        print("Skipping OpenAI configuration\n")
        return None, None

    while True:
        key = input("Enter your OpenAI API key (starts with sk-): ").strip()

        if not key:
            print("Skipping OpenAI configuration\n")
            return None, None

        if validate_openai_key(key):
            print("[OK] Valid OpenAI API key format\n")

            print("Available OpenAI models:")
            print("  1. gpt-3.5-turbo (Faster, cheaper)")
            print("  2. gpt-4-turbo (More capable, slower)")
            print("  3. gpt-4o (Latest, balanced)")

            model_choice = input("Choose model (1-3) [default: 1]: ").strip()

            models = {
                "2": "gpt-4-turbo",
                "3": "gpt-4o"
            }
            model = models.get(model_choice, "gpt-3.5-turbo")

            print(f"[OK] OpenAI configured (model: {model})")
            return key, model
        else:
            print("[WARNING] Invalid key format. OpenAI keys start with 'sk-' or 'sk-proj-'")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return None, None

def configure_anthropic():
    """Configure Anthropic provider."""
    print_section("Anthropic Configuration (Claude)")

    response = input("Do you have an Anthropic API key? (y/n): ").strip().lower()
    print()

    if response != 'y':
        print("Skipping Anthropic configuration\n")
        return None, None

    while True:
        key = input("Enter your Anthropic API key (starts with sk-ant-): ").strip()

        if not key:
            print("Skipping Anthropic configuration\n")
            return None, None

        if validate_anthropic_key(key):
            print("[OK] Valid Anthropic API key format\n")

            print("Available Anthropic models:")
            print("  1. claude-3-5-sonnet-20241022 (Latest, most capable)")
            print("  2. claude-3-opus-20240229 (Very capable, slower)")
            print("  3. claude-3-sonnet-20240229 (Balanced)")
            print("  4. claude-3-haiku-20240307 (Fastest, cheapest)")

            model_choice = input("Choose model (1-4) [default: 1]: ").strip()

            models = {
                "2": "claude-3-opus-20240229",
                "3": "claude-3-sonnet-20240229",
                "4": "claude-3-haiku-20240307"
            }
            model = models.get(model_choice, "claude-3-5-sonnet-20241022")

            print(f"[OK] Anthropic configured (model: {model})")
            return key, model
        else:
            print("[WARNING] Invalid key format. Anthropic keys start with 'sk-ant-'")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return None, None

def save_config(openai_key, openai_model, anthropic_key, anthropic_model):
    """Save configuration to file."""
    config_lines = []

    has_openai = openai_key is not None
    has_anthropic = anthropic_key is not None

    if has_openai:
        config_lines.append(f'OPENAI_API_KEY="{openai_key}"')
        config_lines.append(f'OPENAI_MODEL="{openai_model}"')

    if has_anthropic:
        config_lines.append(f'ANTHROPIC_API_KEY="{anthropic_key}"')
        config_lines.append(f'ANTHROPIC_MODEL="{anthropic_model}"')

    if has_openai and has_anthropic:
        print_section("Both providers configured!")
        print("Which provider do you want to use by default?")
        print("  1. OpenAI (ChatGPT)")
        print("  2. Anthropic (Claude)")

        choice = input("Choose default (1-2) [default: 1]: ").strip()

        if choice == "2":
            config_lines.append('DEFAULT_PROVIDER="anthropic"')
            print("[OK] Default provider: Anthropic (Claude)")
        else:
            config_lines.append('DEFAULT_PROVIDER="openai"')
            print("[OK] Default provider: OpenAI (ChatGPT)")
    elif has_openai:
        config_lines.append('DEFAULT_PROVIDER="openai"')
        print("[OK] Using OpenAI (ChatGPT)")
    elif has_anthropic:
        config_lines.append('DEFAULT_PROVIDER="anthropic"')
        print("[OK] Using Anthropic (Claude)")

    if config_lines:
        with open(CONFIG_FILE, 'w') as f:
            f.write('\n'.join(config_lines) + '\n')
        return True
    return False

def make_executable():
    """Make shell scripts executable (Unix only)."""
    if os.name != 'nt':  # Not Windows
        try:
            for script in ['research.sh', 'demo.sh', 'cli_assistant_enhanced.py']:
                if os.path.exists(script):
                    os.chmod(script, 0o755)
        except:
            pass

def main():
    """Main setup function."""
    print_header("Research Assistant Tool - Interactive Setup")

    # Check Python
    check_python()
    print()

    # Install dependencies
    install_dependencies()

    # AI Provider Configuration
    print_header("AI Provider Configuration")
    print("This tool supports two AI providers:")
    print("  1. OpenAI (ChatGPT models: GPT-4, GPT-3.5-turbo)")
    print("  2. Anthropic (Claude models: Claude 3.5 Sonnet, Claude 3 Opus)")
    print("\nYou can configure one or both providers.\n")

    # Configure OpenAI
    openai_key, openai_model = configure_openai()

    # Configure Anthropic
    anthropic_key, anthropic_model = configure_anthropic()

    # Save configuration
    if save_config(openai_key, openai_model, anthropic_key, anthropic_model):
        print()
        make_executable()

        print_header("Setup Complete! [OK]")
        print("[OK] Configuration saved to .research_config\n")
        print("[->] Quick Start:\n")
        print("  1. Try the demo:")

        if os.name == 'nt':  # Windows
            print("     python cli_assistant_enhanced.py create-project \"My Research\"")
        else:
            print("     ./demo.sh\n")
            print("  2. Or use the assistant directly:")
            print("     ./research.sh create-project \"My Research\"")

        print("\n[IDEA] Tip: You can switch providers anytime by editing .research_config")
        print("    or running this setup again")
    else:
        print_header("No API keys configured")
        print("[WARNING] No API keys configured\n")
        print("You can still use basic features without AI:")

        if os.name == 'nt':
            print("  python cli_assistant_enhanced.py create-project \"My Research\"")
            print("  python cli_assistant_enhanced.py search \"keyword\"")
        else:
            print("  ./research.sh create-project \"My Research\"")
            print("  ./research.sh search \"keyword\"")

        print("\nTo add AI features later, run this setup again")

    print("\n[BOOK] Documentation:")
    print("   QUICKSTART.md - 60 second guide")
    print("   CLI_README.md - Complete reference")
    print("   USAGE_EXAMPLES.md - Detailed examples\n")

    if os.name == 'nt':
        print("Need help? Run: python cli_assistant_enhanced.py --help\n")
    else:
        print("Need help? Run: ./research.sh --help\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        sys.exit(1)
