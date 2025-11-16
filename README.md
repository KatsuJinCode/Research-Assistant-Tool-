# Research Assistant Tool

An intelligent AI-powered research assistant that helps you gather, analyze, and synthesize information.

**Supports OpenAI (ChatGPT) and Anthropic (Claude)!**

## 🚀 Quick Start (2 Commands!)

**Ready to use NOW with OpenAI or Anthropic API:**

### On Windows:

```bash
# 1. Clone the repository
git clone https://github.com/KatsuJinCode/Research-Assistant-Tool-.git
cd Research-Assistant-Tool-

# 2. Double-click setup.bat OR run from Command Prompt/PowerShell:
setup.bat
# → Answer prompts to configure OpenAI, Anthropic, or both
# → Choose your preferred model
# → Start using immediately!

# 3. Use your AI research assistant!
research.bat create-project "My Research"
research.bat add-document 1 sample_documents\ai_research.txt
research.bat summarize 1
```

### On macOS/Linux:

```bash
# 1. Clone the repository
git clone https://github.com/KatsuJinCode/Research-Assistant-Tool-.git
cd Research-Assistant-Tool-

# 2. Run interactive setup
./setup.sh
# → Answer prompts to configure OpenAI, Anthropic, or both
# → Choose your preferred model
# → Start using immediately!

# 3. Use your AI research assistant!
./research.sh create-project "My Research"
./research.sh add-document 1 sample_documents/ai_research.txt
./research.sh summarize 1
```

That's it! The interactive setup guides you through everything.

## Overview

The Research Assistant Tool helps researchers, students, and professionals by:

- 📁 **Organizing** research materials into projects
- 🔍 **Searching** across all your documents
- 🤖 **Summarizing** documents with AI
- 💬 **Answering** questions about your research
- 🎯 **Extracting** key points automatically
- 🏷️ **Auto-tagging** documents for easy organization

## ✨ Current Features (CLI Version - Available Now!)

### Working Features
- ✅ **Project Management**: Organize research into separate projects
- ✅ **Document Storage**: Add and manage .txt and .md files
- ✅ **Full-Text Search**: Search across all your documents instantly
- ✅ **AI Summarization**: Get concise summaries of any document (requires OpenAI API)
- ✅ **AI Q&A**: Ask questions and get answers from your documents (requires OpenAI API)
- ✅ **Key Point Extraction**: Automatically extract main points (requires OpenAI API)
- ✅ **Auto-Tagging**: AI-generated tags for organization (requires OpenAI API)
- ✅ **Local Storage**: All data stored in SQLite, no external database needed

### Coming Soon (Web Version)
- 🔜 **PDF Support**: Direct PDF parsing and extraction
- 🔜 **Web Interface**: Beautiful UI for easier interaction
- 🔜 **Semantic Search**: Vector-based similarity search
- 🔜 **Citation Management**: Auto-generate citations in multiple formats
- 🔜 **Collaboration**: Share projects with team members
- 🔜 **Export Options**: Export to PDF, LaTeX, Markdown

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the complete roadmap.

## 📖 Usage Examples

### Basic Commands

```bash
# Create a research project
./research.sh create-project "AI Research" --description "Studying machine learning"

# Add documents to your project
./research.sh add-document 1 my_paper.txt
./research.sh add-document 1 article.md

# Search across all documents
./research.sh search "neural networks"

# View a document
./research.sh view 1

# List all projects
./research.sh list-projects
```

### AI-Powered Commands

**Note: Requires OpenAI API key**

```bash
# Get an AI summary of a document
./research.sh summarize 1

# Ask questions about your research
./research.sh ask 1 "What are the main findings?"
./research.sh ask 1 "What methodology was used?"

# Extract key points
./research.sh keypoints 1 --num 10

# Auto-generate tags
./research.sh auto-tag 1
```

### Try the Demo

```bash
# Run a full demonstration
./demo.sh
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 60-second getting started
- **[MULTI_PROVIDER_GUIDE.md](MULTI_PROVIDER_GUIDE.md)** - Using OpenAI & Anthropic
- **[CLI_README.md](CLI_README.md)** - Complete CLI reference
- **[USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)** - Detailed examples and workflows
- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - Full development roadmap
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

## Technology Stack

### Current (CLI Version)
- **Python 3.7+**: Core application
- **SQLite**: Local database
- **OpenAI API**: ChatGPT models (GPT-3.5, GPT-4, GPT-4o)
- **Anthropic API**: Claude models (3.5 Sonnet, 3 Opus, 3 Haiku)

### Planned (Web Version)
- **Backend**: FastAPI
- **Frontend**: Next.js + React
- **Database**: PostgreSQL with pgvector
- **AI/ML**: OpenAI, LangChain, sentence-transformers
- **Search**: Elasticsearch or Meilisearch

## 🛠️ Requirements

- Python 3.7 or higher
- OpenAI API key **OR** Anthropic API key (for AI features)
  - OpenAI: https://platform.openai.com/api-keys
  - Anthropic: https://console.anthropic.com/
- Internet connection (for API calls)

## 💰 Cost Information

The CLI tool supports both OpenAI and Anthropic with varying costs:

**OpenAI Pricing:**
- GPT-3.5-turbo: ~$0.001-0.01 per operation (most economical)
- GPT-4o: ~$0.005-0.03 per operation (balanced)
- GPT-4-turbo: ~$0.01-0.05 per operation (premium)

**Anthropic Pricing:**
- Claude 3 Haiku: ~$0.001-0.005 per operation (most economical)
- Claude 3.5 Sonnet: ~$0.003-0.015 per operation (recommended)
- Claude 3 Opus: ~$0.015-0.075 per operation (premium)

Basic features (search, view, organize) are completely free - no API needed!

## 🗺️ Development Roadmap

**Current**: ✅ CLI Version with AI features (v0.1)

**Next Steps**:
1. **Phase 1**: Web interface with authentication
2. **Phase 2**: PDF and document processing
3. **Phase 3**: Semantic search with embeddings
4. **Phase 4**: Citation management
5. **Phase 5**: Collaboration features
6. **Phase 6**: Advanced exports and integrations

See [ROADMAP.md](ROADMAP.md) for detailed timeline.

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

*To be determined*

## 🆘 Troubleshooting

**"Dependencies not installed"**
```bash
./setup.sh
```

**"AI features not available"**
```bash
export OPENAI_API_KEY='sk-your-key-here'
```

**Need help?**
```bash
./research.sh --help
```

## ⭐ Star this repo if you find it useful!
