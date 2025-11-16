# Research Assistant Tool

An intelligent AI-powered research assistant that helps you gather, analyze, and synthesize information.

## 🚀 Quick Start (3 Commands!)

**Ready to use NOW with OpenAI API:**

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Research-Assistant-Tool-

# 2. Run setup (installs dependencies)
./setup.sh

# 3. Set your OpenAI API key and start using!
export OPENAI_API_KEY='sk-your-key-here'
./research.sh create-project "My Research"
./research.sh add-document 1 sample_documents/ai_research.txt
./research.sh summarize 1
```

That's it! You now have an AI research assistant running on your machine.

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

- **[CLI_README.md](CLI_README.md)** - Complete CLI reference
- **[USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)** - Detailed examples and workflows
- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - Full development roadmap
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

## Technology Stack

### Current (CLI Version)
- **Python 3.7+**: Core application
- **SQLite**: Local database
- **OpenAI API**: AI-powered features

### Planned (Web Version)
- **Backend**: FastAPI
- **Frontend**: Next.js + React
- **Database**: PostgreSQL with pgvector
- **AI/ML**: OpenAI, LangChain, sentence-transformers
- **Search**: Elasticsearch or Meilisearch

## 🛠️ Requirements

- Python 3.7 or higher
- OpenAI API key (for AI features)
- Internet connection (for API calls)

## 💰 Cost Information

The CLI tool uses OpenAI's API which has associated costs:
- **Summarization**: ~$0.001-0.01 per document
- **Q&A**: ~$0.001-0.01 per question
- **Key points/Tags**: ~$0.001 per document

Uses GPT-3.5-turbo by default for cost efficiency. Basic features (search, view, organize) are completely free.

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
