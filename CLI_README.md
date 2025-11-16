# CLI Research Assistant - Quick Start

A command-line research assistant with AI-powered features that runs directly in your terminal.

## Features

- 📁 **Project Management** - Organize research into projects
- 📄 **Document Storage** - Add and manage research documents
- 🔍 **Search** - Search through all your documents
- 🤖 **AI Summarization** - Get AI-powered summaries
- 💬 **AI Q&A** - Ask questions about your documents
- 🎯 **Key Points** - Extract main points automatically
- 🏷️ **Auto-Tagging** - AI-generated tags

## Quick Setup

### 1. Install Dependencies

```bash
python3 setup_cli.py
```

### 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or add to your `.bashrc` or `.zshrc`:
```bash
echo 'export OPENAI_API_KEY="your-key"' >> ~/.bashrc
```

## Usage

### Basic Commands

```bash
# Use the enhanced version with AI
alias research="python3 cli_assistant_enhanced.py"

# Create a new project
research create-project "My Research Project" --description "Studying AI"

# List all projects
research list-projects

# Add a document (create a .txt file first)
echo "Your research content here" > sample.txt
research add-document 1 sample.txt

# Search documents
research search "keyword"

# View a document
research view 1

# Get project summary
research summary 1
```

### AI-Powered Commands

**Note:** These require OpenAI API key to be set.

```bash
# Summarize a document
research summarize 1

# Summarize with custom length
research summarize 1 --length 300

# Ask a question about a document
research ask 1 "What are the main findings?"

# Extract key points
research keypoints 1

# Extract more key points
research keypoints 1 --num 10

# Auto-generate tags
research auto-tag 1
```

## Example Workflow

```bash
# 1. Install dependencies
python3 setup_cli.py

# 2. Set API key
export OPENAI_API_KEY='sk-...'

# 3. Create a project
python3 cli_assistant_enhanced.py create-project "AI Research"

# 4. Create and add a sample document
cat > ai_paper.txt << 'EOF'
Artificial Intelligence and Machine Learning

Machine learning is a subset of artificial intelligence that focuses on
developing systems that can learn from data. Deep learning, a specialized
form of machine learning, uses neural networks with multiple layers to
process complex patterns.

Recent advances in transformer models have revolutionized natural language
processing, enabling systems like GPT and BERT to achieve human-level
performance on many language tasks.

Key challenges include:
- Data quality and availability
- Model interpretability
- Computational requirements
- Ethical considerations
EOF

python3 cli_assistant_enhanced.py add-document 1 ai_paper.txt

# 5. Try AI features
python3 cli_assistant_enhanced.py summarize 1
python3 cli_assistant_enhanced.py ask 1 "What are the key challenges?"
python3 cli_assistant_enhanced.py keypoints 1
python3 cli_assistant_enhanced.py auto-tag 1

# 6. Search
python3 cli_assistant_enhanced.py search "transformer"
```

## File Support

Currently supported:
- `.txt` - Plain text files
- `.md` - Markdown files

## Data Storage

All data is stored in the `./data/` directory:
- `data/research.db` - SQLite database
- `data/documents/` - Uploaded files

To reset:
```bash
rm -rf data/
```

## Troubleshooting

### "AI features not available"

Run the setup script:
```bash
python3 setup_cli.py
```

### "No OpenAI API key"

Set the environment variable:
```bash
export OPENAI_API_KEY='your-key-here'
```

### Import errors

Make sure you're running from the project directory:
```bash
cd /path/to/Research-Assistant-Tool-
python3 cli_assistant_enhanced.py [command]
```

## Advanced Usage

### Create an alias

Add to your shell config:
```bash
alias research="cd /path/to/Research-Assistant-Tool- && python3 cli_assistant_enhanced.py"
```

Then use from anywhere:
```bash
research create-project "New Project"
```

### Batch operations

```bash
# Add multiple documents
for file in *.txt; do
    python3 cli_assistant_enhanced.py add-document 1 "$file"
done
```

### Export search results

```bash
python3 cli_assistant_enhanced.py search "keyword" > results.txt
```

## API Costs

AI features use OpenAI's API which has costs:
- Summarization: ~$0.001-0.01 per document
- Q&A: ~$0.001-0.01 per question
- Tags/Key points: ~$0.001 per document

GPT-3.5-turbo is used by default for cost efficiency.

## Privacy

- All data stored locally in SQLite
- API calls to OpenAI for AI features
- No telemetry or tracking

## Next Steps

- See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full web application roadmap
- See [README.md](README.md) for project overview
- Contribute: [CONTRIBUTING.md](CONTRIBUTING.md)
