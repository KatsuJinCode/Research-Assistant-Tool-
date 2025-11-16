#!/bin/bash
# Interactive Setup for Research Assistant CLI
# Supports both OpenAI (ChatGPT) and Anthropic (Claude) models

set -e

CONFIG_FILE=".research_config"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      Research Assistant Tool - Interactive Setup           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not installed"
    echo "Please install Python 3.7+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION found"
echo

# Install dependencies
echo "📦 Installing dependencies..."
python3 -m pip install --quiet --upgrade pip 2>/dev/null || true
python3 -m pip install --quiet openai anthropic

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed (OpenAI + Anthropic)"
else
    echo "⚠ Warning: Some dependencies may not have installed correctly"
fi
echo

# Interactive API key setup
echo "════════════════════════════════════════════════════════════"
echo "  AI Provider Configuration"
echo "════════════════════════════════════════════════════════════"
echo
echo "This tool supports two AI providers:"
echo "  1. OpenAI (ChatGPT models: GPT-4, GPT-3.5-turbo)"
echo "  2. Anthropic (Claude models: Claude 3.5 Sonnet, Claude 3 Opus)"
echo
echo "You can configure one or both providers."
echo

# Function to validate API key format
validate_openai_key() {
    if [[ $1 =~ ^sk-[a-zA-Z0-9]{32,}$ ]] || [[ $1 =~ ^sk-proj-[a-zA-Z0-9_-]{32,}$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_anthropic_key() {
    if [[ $1 =~ ^sk-ant-[a-zA-Z0-9_-]{32,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Configure OpenAI
echo "─────────────────────────────────────────────────────────────"
echo "OpenAI Configuration (ChatGPT)"
echo "─────────────────────────────────────────────────────────────"
echo
read -p "Do you have an OpenAI API key? (y/n): " has_openai
echo

if [[ $has_openai =~ ^[Yy]$ ]]; then
    while true; do
        read -p "Enter your OpenAI API key (starts with sk-): " openai_key
        if [ -n "$openai_key" ]; then
            if validate_openai_key "$openai_key"; then
                echo "✓ Valid OpenAI API key format"

                # Ask for model preference
                echo
                echo "Available OpenAI models:"
                echo "  1. gpt-3.5-turbo (Faster, cheaper)"
                echo "  2. gpt-4-turbo (More capable, slower)"
                echo "  3. gpt-4o (Latest, balanced)"
                read -p "Choose model (1-3) [default: 1]: " openai_model_choice

                case $openai_model_choice in
                    2) openai_model="gpt-4-turbo" ;;
                    3) openai_model="gpt-4o" ;;
                    *) openai_model="gpt-3.5-turbo" ;;
                esac

                echo "OPENAI_API_KEY=\"$openai_key\"" > $CONFIG_FILE
                echo "OPENAI_MODEL=\"$openai_model\"" >> $CONFIG_FILE
                echo "✓ OpenAI configured (model: $openai_model)"
                break
            else
                echo "⚠ Invalid key format. OpenAI keys start with 'sk-' or 'sk-proj-'"
                read -p "Try again? (y/n): " retry
                if [[ ! $retry =~ ^[Yy]$ ]]; then
                    break
                fi
            fi
        else
            echo "Skipping OpenAI configuration"
            break
        fi
    done
else
    echo "Skipping OpenAI configuration"
fi

echo

# Configure Anthropic
echo "─────────────────────────────────────────────────────────────"
echo "Anthropic Configuration (Claude)"
echo "─────────────────────────────────────────────────────────────"
echo
read -p "Do you have an Anthropic API key? (y/n): " has_anthropic
echo

if [[ $has_anthropic =~ ^[Yy]$ ]]; then
    while true; do
        read -p "Enter your Anthropic API key (starts with sk-ant-): " anthropic_key
        if [ -n "$anthropic_key" ]; then
            if validate_anthropic_key "$anthropic_key"; then
                echo "✓ Valid Anthropic API key format"

                # Ask for model preference
                echo
                echo "Available Anthropic models:"
                echo "  1. claude-3-5-sonnet-20241022 (Latest, most capable)"
                echo "  2. claude-3-opus-20240229 (Very capable, slower)"
                echo "  3. claude-3-sonnet-20240229 (Balanced)"
                echo "  4. claude-3-haiku-20240307 (Fastest, cheapest)"
                read -p "Choose model (1-4) [default: 1]: " anthropic_model_choice

                case $anthropic_model_choice in
                    2) anthropic_model="claude-3-opus-20240229" ;;
                    3) anthropic_model="claude-3-sonnet-20240229" ;;
                    4) anthropic_model="claude-3-haiku-20240307" ;;
                    *) anthropic_model="claude-3-5-sonnet-20241022" ;;
                esac

                echo "ANTHROPIC_API_KEY=\"$anthropic_key\"" >> $CONFIG_FILE
                echo "ANTHROPIC_MODEL=\"$anthropic_model\"" >> $CONFIG_FILE
                echo "✓ Anthropic configured (model: $anthropic_model)"
                break
            else
                echo "⚠ Invalid key format. Anthropic keys start with 'sk-ant-'"
                read -p "Try again? (y/n): " retry
                if [[ ! $retry =~ ^[Yy]$ ]]; then
                    break
                fi
            fi
        else
            echo "Skipping Anthropic configuration"
            break
        fi
    done
else
    echo "Skipping Anthropic configuration"
fi

echo

# Set default provider
if [ -f $CONFIG_FILE ]; then
    if grep -q "OPENAI_API_KEY" $CONFIG_FILE && grep -q "ANTHROPIC_API_KEY" $CONFIG_FILE; then
        echo "─────────────────────────────────────────────────────────────"
        echo "Both providers configured!"
        echo
        echo "Which provider do you want to use by default?"
        echo "  1. OpenAI (ChatGPT)"
        echo "  2. Anthropic (Claude)"
        read -p "Choose default (1-2) [default: 1]: " default_choice

        if [[ $default_choice == "2" ]]; then
            echo "DEFAULT_PROVIDER=\"anthropic\"" >> $CONFIG_FILE
            echo "✓ Default provider: Anthropic (Claude)"
        else
            echo "DEFAULT_PROVIDER=\"openai\"" >> $CONFIG_FILE
            echo "✓ Default provider: OpenAI (ChatGPT)"
        fi
    elif grep -q "OPENAI_API_KEY" $CONFIG_FILE; then
        echo "DEFAULT_PROVIDER=\"openai\"" >> $CONFIG_FILE
        echo "✓ Using OpenAI (ChatGPT)"
    elif grep -q "ANTHROPIC_API_KEY" $CONFIG_FILE; then
        echo "DEFAULT_PROVIDER=\"anthropic\"" >> $CONFIG_FILE
        echo "✓ Using Anthropic (Claude)"
    fi
fi

echo

# Make scripts executable
chmod +x research.sh demo.sh cli_assistant_enhanced.py 2>/dev/null || true

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete! ✓                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

if [ -f $CONFIG_FILE ]; then
    echo "✓ Configuration saved to .research_config"
    echo
    echo "🚀 Quick Start:"
    echo
    echo "  1. Try the demo:"
    echo "     ./demo.sh"
    echo
    echo "  2. Or use the assistant directly:"
    echo "     ./research.sh create-project \"My Research\""
    echo "     ./research.sh add-document 1 sample_documents/ai_research.txt"
    echo "     ./research.sh summarize 1"
    echo "     ./research.sh ask 1 \"What are the main points?\""
    echo
    echo "💡 Tip: You can switch providers anytime by editing .research_config"
    echo "    or running ./setup.sh again"
else
    echo "⚠ No API keys configured"
    echo
    echo "You can still use basic features without AI:"
    echo "  ./research.sh create-project \"My Research\""
    echo "  ./research.sh add-document 1 sample_documents/ai_research.txt"
    echo "  ./research.sh search \"keyword\""
    echo "  ./research.sh view 1"
    echo
    echo "To add AI features later, run: ./setup.sh"
fi
echo
echo "📚 Documentation:"
echo "   QUICKSTART.md - 60 second guide"
echo "   CLI_README.md - Complete reference"
echo "   USAGE_EXAMPLES.md - Detailed examples"
echo
echo "Need help? Run: ./research.sh --help"
echo
