# Research Assistant AI Providers

AI provider abstractions and implementations for the Research Assistant Tool platform with support for OpenAI and Anthropic models.

## Features

- **Abstract Interface** - AIInterface for decoupling from specific providers
- **OpenAI Support** - GPT-4, GPT-3.5-turbo, and other OpenAI models
- **Anthropic Support** - Claude 3.5 Sonnet, Claude 3 Opus, and other Claude models
- **Streaming** - Both providers support streaming responses
- **Type Safety** - Pydantic models for messages and responses
- **Token Counting** - Estimate token usage before making API calls
- **Unified API** - Same interface for all providers

## Installation

```bash
cd modules/ai-providers
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
```

## Usage

### OpenAI Provider

```python
from research_assistant_ai import OpenAIProvider, AIMessage, MessageRole

# Create provider
provider = OpenAIProvider(
    api_key="sk-...",
    model="gpt-4",
    temperature=0.7,
    max_tokens=4000
)

# Create messages
messages = [
    AIMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
    AIMessage(role=MessageRole.USER, content="What is Python?"),
]

# Generate response
response = provider.generate(messages)
print(response.content)
print(f"Used {response.usage['total_tokens']} tokens")
```

### Anthropic Provider

```python
from research_assistant_ai import AnthropicProvider, AIMessage, MessageRole

# Create provider
provider = AnthropicProvider(
    api_key="sk-ant-...",
    model="claude-3-5-sonnet-20241022",
    temperature=0.5,
    max_tokens=8000
)

# Create messages
messages = [
    AIMessage(role=MessageRole.SYSTEM, content="You are a research assistant."),
    AIMessage(role=MessageRole.USER, content="Explain quantum computing."),
]

# Generate response
response = provider.generate(messages)
print(response.content)
```

### Streaming Responses

```python
from research_assistant_ai import OpenAIProvider, AIMessage, MessageRole

provider = OpenAIProvider(api_key="sk-...", model="gpt-4")

messages = [
    AIMessage(role=MessageRole.USER, content="Write a short story."),
]

# Stream response
for chunk in provider.generate_streaming(messages):
    print(chunk, end="", flush=True)
```

### Parameter Overrides

```python
# Override default temperature and max_tokens per request
response = provider.generate(
    messages,
    temperature=0.9,  # More creative
    max_tokens=2000,  # Shorter response
)
```

### Token Counting

```python
# Count tokens before making API call
text = "This is a long document..."
token_count = provider.count_tokens(text)
print(f"Text contains {token_count} tokens")

# Check if within limits
if token_count > 4000:
    print("Text is too long, need to split it")
```

### Model Information

```python
# Get information about current model
info = provider.get_model_info()
print(f"Provider: {info['provider']}")
print(f"Model: {info['model']}")
print(f"Supports streaming: {info['supports_streaming']}")
```

## API Reference

### AIMessage

Represents a single message in a conversation.

**Fields:**
- `role: MessageRole` - Message role (SYSTEM, USER, or ASSISTANT)
- `content: str` - Message content

**Example:**
```python
msg = AIMessage(role=MessageRole.USER, content="Hello!")
```

### AIResponse

Represents a response from an AI model.

**Fields:**
- `content: str` - Generated content
- `model: str` - Model that generated the response
- `usage: Optional[Dict[str, int]]` - Token usage statistics
  - `prompt_tokens: int` - Tokens in the prompt
  - `completion_tokens: int` - Tokens in the completion
  - `total_tokens: int` - Total tokens used
- `finish_reason: Optional[str]` - Why generation stopped
- `metadata: Dict[str, Any]` - Additional provider-specific metadata

### AIInterface (Abstract Base Class)

**Methods:**

**`generate(messages, temperature=None, max_tokens=None, **kwargs) -> AIResponse`**

Generate a response from the AI model.

Args:
- `messages`: List of AIMessage objects
- `temperature`: Sampling temperature (overrides default)
- `max_tokens`: Maximum tokens to generate (overrides default)
- `**kwargs`: Additional provider-specific parameters

Returns: AIResponse

**`generate_streaming(messages, temperature=None, max_tokens=None, **kwargs) -> Iterator[str]`**

Generate a streaming response.

Args: Same as `generate()`

Yields: Chunks of generated content as strings

**`count_tokens(text: str) -> int`**

Count tokens in text.

Args:
- `text`: Text to count tokens for

Returns: Number of tokens (int)

**`get_model_info() -> Dict[str, Any]`**

Get information about the current model.

Returns: Dictionary with model information

### OpenAIProvider

OpenAI API provider implementation.

**Constructor:**
```python
OpenAIProvider(
    api_key: str,
    model: str = "gpt-4",
    temperature: float = 0.7,
    max_tokens: int = 4000,
    **kwargs  # Additional OpenAI client parameters
)
```

**Supported Models:**
- `gpt-4` - Most capable model
- `gpt-4-turbo` - Faster GPT-4
- `gpt-3.5-turbo` - Fast and cost-effective
- Other OpenAI chat models

**Features:**
- Uses tiktoken for accurate token counting
- Falls back to approximation if tiktoken unavailable
- Supports all OpenAI chat completion parameters

### AnthropicProvider

Anthropic API provider implementation.

**Constructor:**
```python
AnthropicProvider(
    api_key: str,
    model: str = "claude-3-5-sonnet-20241022",
    temperature: float = 0.5,
    max_tokens: int = 8000,
    **kwargs  # Additional Anthropic client parameters
)
```

**Supported Models:**
- `claude-3-5-sonnet-20241022` - Latest and most capable
- `claude-3-opus-20240229` - Most capable (legacy)
- `claude-3-sonnet-20240229` - Balanced performance
- `claude-3-haiku-20240307` - Fast and compact
- Other Claude 3 models

**Features:**
- Handles system messages separately (Anthropic requirement)
- Approximates token counting (3.5 chars per token)
- Supports all Anthropic message parameters

## Examples

### Example 1: Multi-turn Conversation

```python
from research_assistant_ai import OpenAIProvider, AIMessage, MessageRole

provider = OpenAIProvider(api_key="sk-...", model="gpt-4")

# Build conversation history
messages = [
    AIMessage(role=MessageRole.SYSTEM, content="You are a helpful tutor."),
    AIMessage(role=MessageRole.USER, content="What is recursion?"),
]

# Get first response
response = provider.generate(messages)
print("AI:", response.content)

# Add to conversation
messages.append(AIMessage(role=MessageRole.ASSISTANT, content=response.content))
messages.append(AIMessage(role=MessageRole.USER, content="Can you give an example?"))

# Get second response
response = provider.generate(messages)
print("AI:", response.content)
```

### Example 2: Provider-Agnostic Code

```python
from research_assistant_ai import AIInterface, OpenAIProvider, AnthropicProvider, AIMessage, MessageRole

def ask_ai(provider: AIInterface, question: str) -> str:
    """Ask any AI provider a question."""
    messages = [
        AIMessage(role=MessageRole.USER, content=question)
    ]
    response = provider.generate(messages)
    return response.content

# Use with OpenAI
openai_provider = OpenAIProvider(api_key="sk-...", model="gpt-4")
answer = ask_ai(openai_provider, "What is AI?")

# Use with Anthropic - same code!
anthropic_provider = AnthropicProvider(api_key="sk-ant-...", model="claude-3-5-sonnet-20241022")
answer = ask_ai(anthropic_provider, "What is AI?")
```

### Example 3: Using with Config Module

```python
from research_assistant_config import load_config
from research_assistant_ai import OpenAIProvider, AnthropicProvider

# Load configuration
config = load_config("config/config.yaml")

# Get AI provider config
provider_config = config.get_ai_provider("openai")

# Create provider from config
provider = OpenAIProvider(
    api_key=provider_config.api_key,
    model=provider_config.model,
    temperature=provider_config.temperature,
    max_tokens=provider_config.max_tokens,
)
```

### Example 4: Streaming with Progress

```python
from research_assistant_ai import AnthropicProvider, AIMessage, MessageRole

provider = AnthropicProvider(api_key="sk-ant-...", model="claude-3-5-sonnet-20241022")

messages = [
    AIMessage(role=MessageRole.USER, content="Write a detailed analysis of climate change."),
]

print("Generating response...")
response_text = ""
for chunk in provider.generate_streaming(messages):
    print(chunk, end="", flush=True)
    response_text += chunk

print(f"\n\nGenerated {len(response_text)} characters")
```

### Example 5: Token Budget Management

```python
from research_assistant_ai import OpenAIProvider, AIMessage, MessageRole

provider = OpenAIProvider(api_key="sk-...", model="gpt-4")

# Set token budget
max_tokens = 4000
reserve_for_response = 1000
max_prompt_tokens = max_tokens - reserve_for_response

# Build prompt
system_msg = "You are a helpful assistant."
user_msg = "Explain quantum mechanics in detail."

# Count tokens
system_tokens = provider.count_tokens(system_msg)
user_tokens = provider.count_tokens(user_msg)
total_prompt_tokens = system_tokens + user_tokens

if total_prompt_tokens > max_prompt_tokens:
    print(f"Warning: Prompt too long ({total_prompt_tokens} tokens)")
    # Truncate or split prompt
else:
    messages = [
        AIMessage(role=MessageRole.SYSTEM, content=system_msg),
        AIMessage(role=MessageRole.USER, content=user_msg),
    ]
    response = provider.generate(messages, max_tokens=reserve_for_response)
```

### Example 6: Error Handling

```python
from research_assistant_ai import OpenAIProvider, AIMessage, MessageRole
import openai

provider = OpenAIProvider(api_key="sk-...", model="gpt-4")

messages = [
    AIMessage(role=MessageRole.USER, content="Hello"),
]

try:
    response = provider.generate(messages)
    print(response.content)
except openai.AuthenticationError:
    print("Error: Invalid API key")
except openai.RateLimitError:
    print("Error: Rate limit exceeded")
except openai.APIError as e:
    print(f"Error: API error - {e}")
```

## Development

### Running Tests

```bash
pytest
```

### Test Coverage

```bash
pytest --cov
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Best Practices

1. **Use environment variables for API keys**
   ```python
   import os
   provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
   ```

2. **Reuse provider instances**
   ```python
   # ✓ Good - create once
   provider = OpenAIProvider(api_key="sk-...")

   # Use multiple times
   response1 = provider.generate(messages1)
   response2 = provider.generate(messages2)

   # ✗ Bad - creating new instance each time
   response1 = OpenAIProvider(api_key="sk-...").generate(messages1)
   response2 = OpenAIProvider(api_key="sk-...").generate(messages2)
   ```

3. **Check token counts before API calls**
   ```python
   prompt = "Very long text..."
   tokens = provider.count_tokens(prompt)
   if tokens > 8000:
       # Handle long prompts
       pass
   ```

4. **Use streaming for long responses**
   ```python
   # For long-form content, use streaming to show progress
   for chunk in provider.generate_streaming(messages):
       print(chunk, end="", flush=True)
   ```

5. **Handle errors gracefully**
   ```python
   try:
       response = provider.generate(messages)
   except Exception as e:
       # Log error and provide fallback
       logger.error(f"AI generation failed: {e}")
       response = AIResponse(content="Error occurred", model="unknown")
   ```

6. **Use appropriate temperature values**
   ```python
   # Factual tasks - low temperature
   response = provider.generate(messages, temperature=0.2)

   # Creative tasks - high temperature
   response = provider.generate(messages, temperature=0.9)
   ```

## Provider-Specific Notes

### OpenAI

- **Token counting**: Uses tiktoken library for accurate counts
- **Rate limits**: Be aware of rate limits on your API key tier
- **Models**: Different models have different context windows
  - GPT-4: 8k or 32k tokens
  - GPT-3.5-turbo: 4k or 16k tokens

### Anthropic

- **System messages**: Handled separately from conversation messages
- **Token counting**: Approximate (1 token ≈ 3.5 characters)
- **Context window**: Claude models have 200k token context windows
- **Streaming**: Uses context manager for streaming responses

## Comparison

| Feature | OpenAI | Anthropic |
|---------|--------|-----------|
| Token Counting | Accurate (tiktoken) | Approximate |
| Streaming | ✓ | ✓ |
| System Messages | In message list | Separate parameter |
| Max Context | 32k-128k tokens | 200k tokens |
| Rate Limits | Per tier | Per tier |
| Pricing | Per 1k tokens | Per 1k tokens |

## License

MIT
