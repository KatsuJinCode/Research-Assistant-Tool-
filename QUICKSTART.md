# Quick Start - 60 Second Setup

Get the Research Assistant running in under a minute!

## For Users with OpenAI API

### 1. Clone & Setup (30 seconds)

```bash
git clone <your-repo-url>
cd Research-Assistant-Tool-
./setup.sh
```

### 2. Set API Key (10 seconds)

```bash
export OPENAI_API_KEY='sk-proj-...'  # Your OpenAI API key
```

### 3. Start Researching! (20 seconds)

```bash
# Create your first project
./research.sh create-project "My First Research"

# Try the sample documents
./research.sh add-document 1 sample_documents/ai_research.txt

# Get an AI summary
./research.sh summarize 1

# Ask a question
./research.sh ask 1 "What are the key challenges mentioned?"
```

## That's It! 🎉

You now have a working AI research assistant.

## What's Next?

### Add Your Own Documents

```bash
# Add any .txt or .md file
./research.sh add-document 1 /path/to/your/document.txt
```

### Search Your Research

```bash
./research.sh search "your search term"
```

### Extract Insights

```bash
./research.sh keypoints 1      # Get key points
./research.sh auto-tag 1       # Generate tags
```

## Common Commands

```bash
# See all commands
./research.sh --help

# List your projects
./research.sh list-projects

# View a document
./research.sh view 1

# Get project summary
./research.sh summary 1

# Run the demo
./demo.sh
```

## For Users WITHOUT OpenAI API

You can still use basic features without an API key:

```bash
# No API key needed for these:
./research.sh create-project "My Research"
./research.sh add-document 1 sample_documents/ai_research.txt
./research.sh search "machine learning"
./research.sh view 1
./research.sh list-projects
```

AI features (summarize, ask, keypoints, auto-tag) require an API key.

## Get an OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign up / Log in
3. Go to API Keys section
4. Create new API key
5. Copy the key (starts with `sk-`)
6. Set it: `export OPENAI_API_KEY='sk-your-key'`

## Troubleshooting

**Problem**: Command not found
**Solution**: Make sure you're in the project directory:
```bash
cd Research-Assistant-Tool-
./setup.sh
```

**Problem**: Python not found
**Solution**: Install Python 3.7+:
- Mac: `brew install python3`
- Ubuntu: `sudo apt install python3`
- Windows: Download from python.org

**Problem**: Dependencies not installing
**Solution**: Run setup again:
```bash
./setup.sh
```

## More Info

- **Full CLI Guide**: [CLI_README.md](CLI_README.md)
- **Usage Examples**: [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- **Project Overview**: [README.md](README.md)

---

**Ready to start researching!** 🚀
