#!/bin/bash
# Research Assistant CLI Wrapper
# Makes it easier to run the research assistant

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not found"
    echo "Please install Python 3.7+ and run ./setup.sh"
    exit 1
fi

# Check if dependencies are installed (only if using AI features)
if ! python3 -c "import openai" 2>/dev/null; then
    echo "⚠ Dependencies not installed. Running setup..."
    echo
    ./setup.sh
    echo
fi

# Run the CLI assistant
python3 cli_assistant_enhanced.py "$@"
