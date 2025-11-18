# Multi-Provider AI Support Guide

The Research Assistant Tool supports both **OpenAI (ChatGPT)** and **Anthropic (Claude)** AI providers.

## Supported Providers

### OpenAI (ChatGPT)
- **Models Available**:
  - `gpt-3.5-turbo` - Faster, more economical
  - `gpt-4-turbo` - More capable, higher quality
  - `gpt-4o` - Latest model, balanced performance
- **API Key Format**: Starts with `sk-` or `sk-proj-`
- **Get API Key**: https://platform.openai.com/api-keys

### Anthropic (Claude)
- **Models Available**:
  - `claude-3-5-sonnet-20241022` - Latest, most capable (default)
  - `claude-3-opus-20240229` - Very capable, slower
  - `claude-3-sonnet-20240229` - Balanced performance
  - `claude-3-haiku-20240307` - Fastest, most economical
- **API Key Format**: Starts with `sk-ant-`
- **Get API Key**: https://console.anthropic.com/

## Setup

### Interactive Setup (Recommended)

Run the setup script and follow the prompts:

```bash
./setup.sh
```

The script will:
1. Install required dependencies
2. Ask if you have an OpenAI API key
3. Ask if you have an Anthropic API key
4. Let you choose your preferred model for each provider
5. If you configure both, let you choose which one to use by default

### Manual Configuration

Create a `.research_config` file in the project root:

```bash
# For OpenAI only
OPENAI_API_KEY="sk-your-openai-key-here"
OPENAI_MODEL="gpt-3.5-turbo"
DEFAULT_PROVIDER="openai"
```

```bash
# For Anthropic only
ANTHROPIC_API_KEY="sk-ant-your-anthropic-key-here"
ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
DEFAULT_PROVIDER="anthropic"
```

```bash
# For both providers
OPENAI_API_KEY="sk-your-openai-key-here"
OPENAI_MODEL="gpt-4o"
ANTHROPIC_API_KEY="sk-ant-your-anthropic-key-here"
ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
DEFAULT_PROVIDER="anthropic"  # or "openai"
```

## Usage

Once configured, use the tool normally:

```bash
# The configured provider will be used automatically
./research.sh summarize 1
./research.sh ask 1 "What are the main findings?"
./research.sh keypoints 1
./research.sh auto-tag 1
```

The tool will show which provider is being used:

```
✓ AI features enabled (Anthropic - claude-3-5-sonnet-20241022)
```

or

```
✓ AI features enabled (Openai - gpt-4o)
```

## Switching Providers

### Method 1: Re-run Setup

```bash
./setup.sh
```

This will ask about your configuration again and let you change providers or models.

### Method 2: Edit Config File

Edit `.research_config` and change `DEFAULT_PROVIDER`:

```bash
# Switch to Claude
DEFAULT_PROVIDER="anthropic"

# Switch to ChatGPT
DEFAULT_PROVIDER="openai"
```

### Method 3: Use Environment Variables

Override the config file temporarily:

```bash
# Use OpenAI for this session
export OPENAI_API_KEY='sk-your-key'
./research.sh summarize 1

# Use Anthropic for this session
export ANTHROPIC_API_KEY='sk-ant-your-key'
./research.sh summarize 1
```

## Cost Comparison

### OpenAI Pricing (as of 2024)
- **GPT-3.5 Turbo**: ~$0.001-0.01 per research operation
- **GPT-4 Turbo**: ~$0.01-0.05 per research operation
- **GPT-4o**: ~$0.005-0.03 per research operation

### Anthropic Pricing (as of 2024)
- **Claude 3 Haiku**: ~$0.001-0.005 per research operation
- **Claude 3 Sonnet**: ~$0.003-0.015 per research operation
- **Claude 3.5 Sonnet**: ~$0.003-0.015 per research operation
- **Claude 3 Opus**: ~$0.015-0.075 per research operation

**Cost-Saving Tips**:
- Use GPT-3.5-turbo or Claude Haiku for everyday research
- Use GPT-4o or Claude 3.5 Sonnet for important analysis
- Cache results - view documents instead of re-summarizing

## Comparison

| Feature | OpenAI (ChatGPT) | Anthropic (Claude) |
|---------|------------------|-------------------|
| **Speed** | Fast (3.5), Moderate (4) | Fast (Haiku), Moderate (Sonnet/Opus) |
| **Cost** | $ to $$$ | $ to $$$ |
| **Context Window** | 16K-128K tokens | 200K tokens |
| **Best For** | Quick summaries, general Q&A | Long documents, detailed analysis |
| **Strengths** | Fast, economical, widely used | Longer context, thoughtful responses |

## Troubleshooting

### "AI features unavailable"

**Solution**: Run `./setup.sh` to configure your API keys.

### "Invalid API key format"

**OpenAI keys** start with:
- `sk-` (legacy)
- `sk-proj-` (new format)

**Anthropic keys** start with:
- `sk-ant-`

### "Provider initialization failed"

1. Check your API key is correct
2. Ensure you have internet connection
3. Verify your API key has not been revoked
4. Check you have credits/billing set up

### "Dependencies not installed"

```bash
pip install openai anthropic
```

Or run:
```bash
./setup.sh
```

## Advanced Configuration

### Using Different Models for Different Tasks

You can manually switch models by editing `.research_config` before running commands:

```bash
# Use fast model for tagging
echo 'OPENAI_MODEL="gpt-3.5-turbo"' > .research_config.tmp
mv .research_config.tmp .research_config
./research.sh auto-tag 1

# Use powerful model for analysis
echo 'ANTHROPIC_MODEL="claude-3-opus-20240229"' > .research_config.tmp
mv .research_config.tmp .research_config
./research.sh ask 1 "Provide detailed analysis"
```

### Using Both Providers

Configure both, then switch as needed:

```bash
# Use OpenAI for quick tasks
./research.sh summarize 1  # Uses default provider

# Temporarily switch to Claude for complex analysis
# (Edit DEFAULT_PROVIDER in .research_config)
./research.sh ask 1 "Detailed question"
```

## Security

- **Never commit `.research_config`** - it's in `.gitignore` by default
- **Don't share your API keys** - they provide access to your account
- **Rotate keys periodically** - especially if exposed
- **Use environment variables** in production - don't hardcode keys
- **Monitor usage** - check your OpenAI/Anthropic dashboard regularly

## Getting API Keys

### OpenAI
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. **Important**: Copy it immediately - you won't see it again!

### Anthropic
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. **Important**: Copy it immediately - you won't see it again!

## FAQ

**Q: Can I use both providers at the same time?**
A: Yes! Configure both, and the tool will use whichever is set as `DEFAULT_PROVIDER`.

**Q: Which provider is better?**
A: Both are excellent. OpenAI is generally faster and cheaper for simple tasks. Anthropic (Claude) handles longer documents better and provides more thoughtful responses.

**Q: Can I change providers mid-project?**
A: Yes! Your research data is stored locally. The provider only affects AI operations.

**Q: Do I need both API keys?**
A: No, you only need one. Configure whichever provider you prefer.

**Q: Which model should I choose?**
A: Start with:
- OpenAI: `gpt-3.5-turbo` (best value)
- Anthropic: `claude-3-5-sonnet-20241022` (latest, best quality)

**Q: How do I check which provider I'm using?**
A: The tool shows this when it starts:
```
✓ AI features enabled (Anthropic - claude-3-5-sonnet-20241022)
```

**Q: Can I use the free tier?**
A: Both providers require payment. OpenAI offers $5 free credit for new users. Check their websites for current offers.

## Next Steps

- Try both providers to see which you prefer
- Experiment with different models
- Monitor your usage and costs
- Join the community to share tips

For more help, see:
- [QUICKSTART.md](QUICKSTART.md) - Get started in 60 seconds
- [CLI_README.md](CLI_README.md) - Complete CLI reference
- [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - Detailed examples
