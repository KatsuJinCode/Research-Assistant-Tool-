#!/bin/bash
# Quick Setup for Research Assistant CLI
# Run this once after cloning the repository

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      Research Assistant Tool - Quick Setup                 ║"
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
python3 -m pip install --quiet openai

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "⚠ Warning: Some dependencies may not have installed correctly"
fi
echo

# Check for API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠ OpenAI API key not detected"
    echo
    echo "To use AI features, set your API key:"
    echo "  export OPENAI_API_KEY='sk-your-key-here'"
    echo
    echo "Or add to your shell config (~/.bashrc or ~/.zshrc):"
    echo "  echo 'export OPENAI_API_KEY=\"sk-your-key\"' >> ~/.bashrc"
    echo
    echo "You can still use basic features without an API key."
    echo
else
    echo "✓ OpenAI API key detected"
    echo
fi

# Make scripts executable
chmod +x research.sh demo.sh cli_assistant_enhanced.py 2>/dev/null || true

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete! ✓                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo
echo "🚀 Quick Start:"
echo
echo "  1. Try the demo:"
echo "     ./demo.sh"
echo
echo "  2. Or use the assistant directly:"
echo "     ./research.sh create-project \"My Research\""
echo "     ./research.sh add-document 1 sample_documents/ai_research.txt"
echo "     ./research.sh search \"machine learning\""
echo
echo "  3. With OpenAI API key, use AI features:"
echo "     ./research.sh summarize 1"
echo "     ./research.sh ask 1 \"What are the main points?\""
echo
echo "📚 Documentation:"
echo "   CLI_README.md - Quick reference"
echo "   USAGE_EXAMPLES.md - Detailed examples"
echo
echo "Need help? Run: ./research.sh --help"
echo
