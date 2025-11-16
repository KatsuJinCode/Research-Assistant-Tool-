#!/bin/bash
# Research Assistant CLI Wrapper
# Makes it easier to run the research assistant

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found"
    exit 1
fi

# Run the CLI assistant
python3 cli_assistant.py "$@"
