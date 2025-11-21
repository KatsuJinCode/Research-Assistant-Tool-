# Claude Code CLI Research Findings

## Key Discoveries

### 1. No `--tools` Flag in Claude Code CLI

The Claude Code CLI **does not support** a `--tools` flag for forcing tool calling or structured output.

**Official documentation confirms:**
- `--allowedTools`: Controls which tools Claude can use (permissions)
- `--disallowedTools`: Blocks specific tools
- **NO** `--tools` flag for defining custom tool schemas

### 2. Output Format

Claude Code CLI with `--output-format json` returns a **wrapper object**:

```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": 1234,
  "duration_api_ms": 800,
  "num_turns": 1,
  "result": "The actual response text here...",
  "session_id": "abc123",
  "total_cost_usd": 0.003,
  "usage": {...},
  "modelUsage": {...}
}
```

The **actual Claude response** is in the `result` field as plain text.

### 3. Correct Approach for Structured Output

Since there's no tool calling mechanism in Claude Code CLI, use **prompt-based JSON requests**:

```python
prompt = f"""Your task here...

IMPORTANT: You MUST respond with ONLY valid JSON matching this schema:

{json.dumps(schema, indent=2)}

Do NOT include explanatory text, markdown, or code blocks.
Output ONLY the raw JSON object."""

# Invoke WITHOUT --tools flag
result = subprocess.run(['claude', '-p', prompt, '--output-format', 'json'], ...)

# Parse wrapper
wrapper = json.loads(result.stdout)
result_text = wrapper['result']

# Parse JSON from result text
output_json = json.loads(result_text)
```

### 4. JSON Extraction Fallbacks

Claude might return JSON in code blocks despite instructions:

```python
# Try direct parsing first
try:
    return json.loads(result_text)
except json.JSONDecodeError:
    # Extract from markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
```

### 5. Why Our Initial Approach Failed

1. Used non-existent `--tools` flag → Claude Code CLI may have waited for user input or timed out
2. Expected `tool_uses` or `content` arrays in response → These don't exist in CLI output
3. Tried to parse tool calling response format → CLI only returns plain text in `result` field

### 6. Updated Implementation

See `document_processor.py`:
- `_invoke_agent_with_structured_output()` - Correct implementation
- Prompts Claude to return JSON directly
- Parses `result` field from CLI wrapper
- Has fallback for code block extraction

## Documentation References

- [Headless Mode](https://code.claude.com/docs/en/headless.md) - JSON output format
- [CLI Reference](https://code.claude.com/docs/en/cli-reference.md) - Available flags

## Recommendation

The prompt-based approach is the **only** way to get structured JSON output from Claude Code CLI. Tool calling as described in Anthropic API docs (with `tools` parameter) is **not available** in the CLI.

For true tool calling with JSON schemas, would need to:
1. Use Anthropic API directly (not CLI)
2. Or use a different agent system that supports it

Our current implementation with `_invoke_agent_with_structured_output()` is correct for Claude Code CLI.
