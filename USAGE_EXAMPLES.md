# CLI Research Assistant - Usage Examples

## Complete Workflow Example

This guide shows a complete research workflow using the CLI assistant.

## Setup (One-time)

```bash
# 1. Install dependencies
python3 setup_cli.py

# 2. Set OpenAI API key (for AI features)
export OPENAI_API_KEY='sk-your-key-here'

# Optional: Add to your shell config for persistence
echo 'export OPENAI_API_KEY="sk-your-key"' >> ~/.bashrc
```

## Example 1: Academic Research Project

```bash
# Create a project for your research
python3 cli_assistant_enhanced.py create-project "Deep Learning Survey" \
    --description "Literature review on deep learning techniques"

# Add research papers (as .txt or .md files)
python3 cli_assistant_enhanced.py add-document 1 papers/attention_is_all_you_need.txt
python3 cli_assistant_enhanced.py add-document 1 papers/bert.txt
python3 cli_assistant_enhanced.py add-document 1 papers/gpt3.txt

# Search across all papers
python3 cli_assistant_enhanced.py search "attention mechanism"

# Get AI summary of a paper
python3 cli_assistant_enhanced.py summarize 1

# Ask specific questions
python3 cli_assistant_enhanced.py ask 1 "What is the main contribution of this paper?"
python3 cli_assistant_enhanced.py ask 1 "What are the limitations mentioned?"

# Extract key points
python3 cli_assistant_enhanced.py keypoints 1 --num 10

# Auto-generate tags for organization
python3 cli_assistant_enhanced.py auto-tag 1
```

## Example 2: News Monitoring

```bash
# Create project
python3 cli_assistant_enhanced.py create-project "Tech News" \
    --description "Daily technology news monitoring"

# Add news articles daily
python3 cli_assistant_enhanced.py add-document 2 articles/$(date +%Y%m%d)_ai_news.txt

# Search for specific topics
python3 cli_assistant_enhanced.py search "GPT-4" --project 2
python3 cli_assistant_enhanced.py search "regulation"

# Get daily summaries
python3 cli_assistant_enhanced.py summarize 5
```

## Example 3: Book Notes

```bash
# Create project for book
python3 cli_assistant_enhanced.py create-project "Thinking Fast and Slow" \
    --description "Notes and insights from Daniel Kahneman's book"

# Add chapter notes as separate documents
python3 cli_assistant_enhanced.py add-document 3 notes/chapter1.txt
python3 cli_assistant_enhanced.py add-document 3 notes/chapter2.txt

# Search across all notes
python3 cli_assistant_enhanced.py search "cognitive bias"

# Get key points from each chapter
python3 cli_assistant_enhanced.py keypoints 10

# Ask questions
python3 cli_assistant_enhanced.py ask 10 "What are the two systems of thinking?"
```

## Example 4: Competitive Analysis

```bash
# Create project
python3 cli_assistant_enhanced.py create-project "Competitor Research" \
    --description "Market analysis and competitor tracking"

# Add competitor information
python3 cli_assistant_enhanced.py add-document 4 competitors/company_a_profile.txt
python3 cli_assistant_enhanced.py add-document 4 competitors/company_b_profile.txt

# Compare features
python3 cli_assistant_enhanced.py ask 15 "What are the key differentiators?"

# Extract insights
python3 cli_assistant_enhanced.py keypoints 15 --num 5
```

## Batch Operations

### Add Multiple Files

```bash
# Add all .txt files in a directory
for file in research_papers/*.txt; do
    python3 cli_assistant_enhanced.py add-document 1 "$file"
    echo "Added: $file"
done
```

### Search and Save Results

```bash
# Search and save results to file
python3 cli_assistant_enhanced.py search "machine learning" > ml_results.txt
```

### Bulk Summarization

```bash
# Summarize all documents in a project
for doc_id in {1..10}; do
    echo "Document $doc_id:"
    python3 cli_assistant_enhanced.py summarize $doc_id
    echo "---"
done > all_summaries.txt
```

## Advanced Patterns

### Create Alias for Easier Use

```bash
# Add to ~/.bashrc or ~/.zshrc
alias research="python3 /path/to/Research-Assistant-Tool-/cli_assistant_enhanced.py"

# Then use anywhere:
research create-project "New Project"
research search "keyword"
```

### Integration with Other Tools

```bash
# Download and add web article
curl -s "https://example.com/article" | html2text > article.txt
python3 cli_assistant_enhanced.py add-document 1 article.txt

# Convert PDF to text and add
pdftotext paper.pdf - | python3 cli_assistant_enhanced.py add-document 1 -

# Summarize and email results
python3 cli_assistant_enhanced.py summarize 1 | mail -s "Research Summary" you@example.com
```

### Scheduled Research

```bash
# Add to crontab for daily research digest
# Run every day at 9 AM
0 9 * * * /path/to/script.sh

# script.sh:
#!/bin/bash
cd /path/to/Research-Assistant-Tool-
python3 cli_assistant_enhanced.py search "today's query" > /tmp/daily_research.txt
cat /tmp/daily_research.txt | mail -s "Daily Research Digest" you@example.com
```

## Tips and Best Practices

### 1. Organize with Projects

Create separate projects for different topics:
```bash
python3 cli_assistant_enhanced.py create-project "Work Research"
python3 cli_assistant_enhanced.py create-project "Personal Learning"
python3 cli_assistant_enhanced.py create-project "Thesis Research"
```

### 2. Use Descriptive Filenames

Name files clearly before adding:
```bash
# Good
2024-03-15_transformer_architecture_vaswani.txt
climate_ipcc_report_2023.txt

# Less helpful
paper1.txt
doc.txt
```

### 3. Regular Backups

```bash
# Backup your research database
cp -r data/ backups/data_$(date +%Y%m%d)/

# Or use git
git add data/
git commit -m "Research backup $(date)"
```

### 4. Combine with Version Control

```bash
# Track your documents
git init my_research
cd my_research
# Add documents
python3 ../Research-Assistant-Tool-/cli_assistant_enhanced.py add-document 1 paper.txt
git add paper.txt
git commit -m "Add paper on transformers"
```

### 5. Export and Share

```bash
# View and save formatted output
python3 cli_assistant_enhanced.py view 1 > shared_doc.txt
python3 cli_assistant_enhanced.py summarize 1 > summary_for_team.txt
```

## Troubleshooting Common Issues

### "File not found"
Use absolute paths or check your current directory:
```bash
pwd  # Check current directory
python3 cli_assistant_enhanced.py add-document 1 /full/path/to/file.txt
```

### "AI features not available"
Install dependencies and set API key:
```bash
python3 setup_cli.py
export OPENAI_API_KEY='your-key'
```

### "Document already exists"
The system detects duplicates by content hash. This is normal and prevents duplicates.

### View stored data
```bash
# Check database
sqlite3 data/research.db "SELECT * FROM projects;"
sqlite3 data/research.db "SELECT id, title FROM documents;"
```

## Cost Management for AI Features

### Estimate Costs
- Summarization: ~$0.001-0.01 per document
- Q&A: ~$0.001-0.01 per question
- Key points/tags: ~$0.001 per document

### Save Money
```bash
# Use shorter summaries
python3 cli_assistant_enhanced.py summarize 1 --length 100

# Ask multiple questions in one query
python3 cli_assistant_enhanced.py ask 1 "What are the main points, methods, and conclusions?"

# Cache results - view documents instead of re-summarizing
python3 cli_assistant_enhanced.py view 1  # Free
```

## Next Steps

- Explore the full project plan: [PROJECT_PLAN.md](PROJECT_PLAN.md)
- Contribute improvements: [CONTRIBUTING.md](CONTRIBUTING.md)
- Run the demo: `./demo.sh`
