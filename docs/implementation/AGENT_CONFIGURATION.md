# AI Agent Configuration Guide

The Research Assistant Tool is **agent-agnostic** and supports multiple AI CLI tools for claim extraction and analysis.

## Supported Agents

- **Claude Code** (default) - `claude`
- **OpenAI Codex** - `openai` or `codex`
- **Google Gemini Code** - `gemini`
- **Custom CLI Tools** - Configure your own!

---

## Quick Start

### Method 1: Environment Variable (Recommended)

Set the `AI_AGENT_CLI` environment variable:

```bash
# Windows
set AI_AGENT_CLI=claude

# Linux/Mac
export AI_AGENT_CLI=claude
```

Available values: `claude`, `claude-code`, `openai`, `codex`, `gemini`, `gemini-code`

### Method 2: Configuration File

Create `web_ui/agent_config.json`:

```json
{
  "agent": "claude"
}
```

### Method 3: Programmatic Configuration

```python
from web_ui.agent_config import set_agent

# Use Claude Code
set_agent('claude')

# Use OpenAI Codex
set_agent('openai')

# Use Gemini
set_agent('gemini')
```

---

## Custom CLI Adapter

If you have a custom AI CLI tool, you can configure it:

### Via Configuration File

Create `web_ui/agent_config.json`:

```json
{
  "agent": "custom",
  "custom_config": {
    "executable": "my-ai-cli",
    "prompt_flag": "-p",
    "tools_flag": "--tools",
    "output_format_flag": "--json",
    "tool_response_path": "content.0.tool_use.input"
  }
}
```

### Via Python

```python
from web_ui.agent_config import set_agent

custom_config = {
    "executable": "my-ai-cli",
    "prompt_flag": "-p",
    "tools_flag": "--tools",
    "output_format_flag": "--json",
    "tool_response_path": "result.tool_input"
}

set_agent('custom', custom_config, save=True)
```

### Custom Config Options

- **`executable`** (required): CLI command name
- **`prompt_flag`** (optional): Flag for prompt input (e.g., `-p`, `--prompt`)
- **`tools_flag`** (optional): Flag for tool definitions file
- **`output_format_flag`** (optional): Flag for JSON output
- **`tool_response_path`** (required if using tools): Dot-notation path to extract tool input from JSON response

#### Example Response Path

If your CLI returns:
```json
{
  "content": [
    {
      "type": "tool_use",
      "input": {"claims": [...]}
    }
  ]
}
```

Set `tool_response_path` to: `"content.0.input"`

Array indexing uses `[N]` syntax: `"content[0].tool_use.input"`

---

## Agent-Specific Notes

### Claude Code

- **Executable**: `claude`
- **Tool Support**: ✅ Yes (native tool calling)
- **Format**: JSON output with `--output-format json`
- **Tools Flag**: `--tools <file.json>`

### OpenAI Codex

- **Executable**: `openai`
- **Tool Support**: ✅ Yes (function calling)
- **Format**: JSON via `--json`
- **Functions Flag**: `--functions <file.json>`

**Note**: Adapter assumes OpenAI CLI syntax - adjust if needed based on actual CLI

### Google Gemini

- **Executable**: `gemini` or `gcloud`
- **Tool Support**: ✅ Yes
- **Format**: JSON via `--format json`

**Note**: Adapter assumes Gemini CLI syntax - adjust based on actual Google Cloud CLI

---

## Testing Your Configuration

### Check Current Agent

```python
from web_ui.agent_config import get_agent_adapter

adapter = get_agent_adapter()
print(f"Current agent: {adapter.__class__.__name__}")
```

### Test Agent Invocation

```python
from web_ui.agent_config import get_agent_adapter

adapter = get_agent_adapter()

# Test without tools
response = adapter.invoke("What is 2+2?")
print(response)

# Test with tools (if supported)
if adapter.supports_tools():
    tool_schema = {
        "name": "test_tool",
        "description": "Test tool",
        "input_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            },
            "required": ["result"]
        }
    }

    response = adapter.invoke(
        "Call the test_tool with result='success'",
        tools=[tool_schema]
    )
    print(adapter.parse_tool_response(response))
```

---

## Troubleshooting

### Error: "Agent did not call the required tool"

- Check that your agent CLI supports tool calling
- Verify the `tool_response_path` is correct for your CLI's response format
- Enable logging to see the raw response:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Error: "Agent process failed"

- Verify the executable is in your PATH: `which claude` / `where claude`
- Check CLI is installed: `claude --version`
- Test CLI manually: `claude -p "Hello"`

### Wrong Agent Being Used

Configuration priority (highest to lowest):
1. Programmatic `set_agent()` call
2. `AI_AGENT_CLI` environment variable
3. `agent_config.json` file
4. Default (Claude Code)

---

## Example Configurations

### Using Claude Code (Default)

```bash
# No configuration needed - works out of the box
python web_ui/app.py
```

### Using OpenAI Codex

```bash
export AI_AGENT_CLI=openai
python web_ui/app.py
```

### Using Custom LLM CLI

`web_ui/agent_config.json`:
```json
{
  "agent": "custom",
  "custom_config": {
    "executable": "ollama",
    "prompt_flag": "run",
    "output_format_flag": "--format=json",
    "tool_response_path": "message.tool_calls.0.function.arguments"
  }
}
```

---

## Contributing New Adapters

To add a new built-in adapter:

1. Create adapter class inheriting from `AgentAdapter`
2. Implement `invoke()`, `parse_tool_response()`, and `supports_tools()`
3. Register in `AgentConfig.ADAPTERS` dict
4. Add to supported agents list

See `web_ui/agent_config.py` for examples.
