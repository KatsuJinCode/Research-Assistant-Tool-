"""
Diagnostic test for agent tool calling

Tests the actual Claude Code CLI to see what response format we get.
"""

import json
import tempfile
import subprocess
import os
from pathlib import Path


def test_claude_tool_calling():
    """Test Claude Code CLI with tool calling"""

    # Define a simple tool
    tool_schema = {
        "name": "submit_result",
        "description": "Submit the test result",
        "input_schema": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The answer to the question"
                }
            },
            "required": ["answer"]
        }
    }

    # Create temp file for tools
    fd, tool_file_path = tempfile.mkstemp(suffix='.json', text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump([tool_schema], f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except:
        os.close(fd)
        raise

    print("=" * 80)
    print("TOOL FILE CREATED")
    print("=" * 80)
    with open(tool_file_path, 'r') as f:
        print(f.read())
    print()

    # Test prompt
    prompt = """What is 2+2?

IMPORTANT: You MUST call the submit_result tool with your answer."""

    print("=" * 80)
    print("INVOKING CLAUDE CODE CLI")
    print("=" * 80)
    print(f"Command: claude -p \"{prompt}\" --tools {tool_file_path} --output-format json")
    print()

    # Invoke Claude
    try:
        result = subprocess.run(
            ['claude', '-p', prompt, '--tools', tool_file_path, '--output-format', 'json'],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8'
        )

        print("=" * 80)
        print("RETURN CODE:", result.returncode)
        print("=" * 80)
        print()

        print("=" * 80)
        print("STDOUT (RAW):")
        print("=" * 80)
        print(result.stdout)
        print()

        print("=" * 80)
        print("STDERR:")
        print("=" * 80)
        print(result.stderr)
        print()

        if result.returncode == 0:
            # Try to parse JSON
            print("=" * 80)
            print("PARSED JSON:")
            print("=" * 80)
            try:
                response_data = json.loads(result.stdout.strip())
                print(json.dumps(response_data, indent=2))
                print()

                # Look for tool uses
                print("=" * 80)
                print("SEARCHING FOR TOOL USES:")
                print("=" * 80)

                tool_uses = response_data.get('tool_uses', [])
                print(f"Found in 'tool_uses': {len(tool_uses)} items")

                if 'content' in response_data:
                    print(f"Content blocks: {len(response_data['content'])}")
                    for i, block in enumerate(response_data['content']):
                        print(f"  Block {i}: type={block.get('type')}")
                        if block.get('type') == 'tool_use':
                            print(f"    Tool name: {block.get('name')}")
                            print(f"    Tool input: {block.get('input')}")

                print()

            except json.JSONDecodeError as e:
                print(f"JSON PARSE ERROR: {e}")
                print()

    finally:
        try:
            os.unlink(tool_file_path)
        except:
            pass


def test_claude_simple():
    """Test Claude Code CLI without tools"""

    print("=" * 80)
    print("TESTING SIMPLE INVOCATION (NO TOOLS)")
    print("=" * 80)
    print()

    result = subprocess.run(
        ['claude', '-p', 'What is 2+2? Answer in one word.', '--output-format', 'json'],
        capture_output=True,
        text=True,
        timeout=30,
        encoding='utf-8'
    )

    print(f"Return code: {result.returncode}")
    print(f"STDOUT:\n{result.stdout}")
    print(f"STDERR:\n{result.stderr}")
    print()


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("CLAUDE CODE CLI DIAGNOSTIC TEST")
    print("=" * 80)
    print()

    # Test 1: Simple invocation
    test_claude_simple()

    # Test 2: Tool calling
    test_claude_tool_calling()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
