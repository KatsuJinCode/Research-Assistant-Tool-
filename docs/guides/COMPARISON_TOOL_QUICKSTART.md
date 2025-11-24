# Document Comparison Tool - Quick Start Guide

## 🚀 Quick Start (30 seconds)

1. **Open the tool**: Click the **📊 Compare** button in the top header
2. **Select documents**: Choose 2+ documents from the dropdown menus
3. **View comparison**: Claims are automatically aligned and color-coded
4. **Analyze consensus**: Click **🔍 Analyze Consensus** for detailed analysis
5. **Export report**: Click **📄 Export Report** to save results

---

## 🎯 Key Features

### Visual Comparison
- **🟠 Unique**: Claims only in one document
- **🟢 Shared**: Claims in all documents
- **🔵 Similar**: Claims in multiple documents
- **🔴 Contradicting**: Opposing claims across documents

### View Modes
- **Side-by-Side**: Parallel panels (default)
- **Unified**: All claims grouped together
- **Claims-Only**: Simple text list

### Consensus Analysis
- **Overall Score**: 0-100% agreement level
- **Agreements**: Claims all documents share
- **Disagreements**: Contradictory positions
- **Partial Agreements**: Claims in some documents
- **Unique Positions**: Document-specific claims

### Export Formats
- **Markdown**: Clean text format (`.md`)
- **HTML**: Fully styled web page (`.html`)
- **JSON**: Structured data (`.json`)

---

## 📋 Common Tasks

### Compare Two Papers
```
1. Click "📊 Compare"
2. Select first paper from "Doc 1" dropdown
3. Select second paper from "Doc 2" dropdown
4. Review side-by-side comparison
```

### Find Agreements
```
1. Load 2+ documents
2. Click "🔍 Analyze Consensus"
3. Look at "✓ Agreements" section
4. See claims all documents share
```

### Find Contradictions
```
1. Load 2+ documents
2. Click "🔍 Analyze Consensus"
3. Look at "⚠ Disagreements" section
4. Review conflicting positions
```

### Export to Markdown
```
1. Click "📄 Export Report"
2. Type: markdown
3. File downloads automatically
4. Open in any text editor
```

---

## 🎨 Understanding the Colors

| Color | Meaning | Example |
|-------|---------|---------|
| 🟠 Orange | Unique | Only Paper A mentions this |
| 🟢 Green | Shared | All papers agree on this |
| 🔵 Blue | Similar | Papers A and B mention this |
| 🔴 Red | Contradicting | Papers disagree on this |

---

## 🔧 Filter Options

- **☑ Unique**: Show/hide unique claims
- **☑ Shared**: Show/hide shared claims
- **☑ Similar**: Show/hide similar claims
- **☑ Auto-align**: Automatically align claims

---

## 💡 Tips

1. **Start with 2-3 documents** for best performance
2. **Use auto-align** to see connections between claims
3. **Export to HTML** for presentations
4. **Export to Markdown** for GitHub/documentation
5. **Export to JSON** for further analysis

---

## 🐛 Troubleshooting

**Q: No documents appear in dropdown**
A: Make sure documents are uploaded and processed first

**Q: Claims don't align**
A: Check that "Auto-align" option is enabled

**Q: Export doesn't work**
A: Ensure you selected a format (markdown/html/json)

**Q: Comparison is slow**
A: Reduce number of documents (<5 recommended)

---

## 📊 Example Use Cases

### Literature Review
Compare 3-5 research papers to find:
- Common findings (agreements)
- Conflicting results (disagreements)
- Research gaps (unique positions)

### Fact Checking
Compare multiple sources on same topic:
- What all sources agree on
- Where sources contradict
- Which claims need verification

### Document Evolution
Compare different versions of same document:
- What was added
- What was removed
- What changed

### Cross-Source Analysis
Compare news articles or reports:
- Consensus across sources
- Bias detection
- Coverage differences

---

## 🎓 Advanced Usage

### Consensus Scoring
```
Score = (Agreements × 1.0 + Partial × 0.5 - Disagreements × 0.5)
```
- 80-100%: Strong consensus
- 60-80%: Moderate consensus
- 40-60%: Weak consensus
- 0-40%: Low/no consensus

### Claim Types
- **Super-claim**: Top-level claim (parent)
- **Sub-claim**: Supporting claim (child)
- All sub-claims shown indented under parent

### Similarity Threshold
Claims are aligned when similarity > 75%
- Based on word overlap (Jaccard similarity)
- Optional: Semantic embeddings (if enabled)

---

## 📝 Report Structure

### Markdown Export
```markdown
# Document Comparison Report
## Documents Compared
## Consensus Analysis
  ### ✓ Agreements
  ### ⚠ Disagreements
  ### ≈ Partial Agreements
  ### ⭐ Unique Positions
## Metrics
## Aligned Claim Groups
```

### HTML Export
- Fully styled standalone page
- Color-coded sections
- Consensus score visualization
- Print-ready format

### JSON Export
```json
{
  "documents": [...],
  "alignedClaims": [...],
  "consensus": {
    "overallConsensus": 0.75,
    "agreements": [...],
    "disagreements": [...]
  }
}
```

---

## 🚦 Best Practices

1. **Compare related documents**: Same topic/domain
2. **Keep it manageable**: 2-5 documents ideal
3. **Review aligned claims**: Check accuracy of matching
4. **Use consensus for insights**: Guide further research
5. **Export for records**: Keep comparison reports

---

## 🔗 Related Features

- **Search**: Find specific claims across documents
- **Graph View**: Visualize document relationships
- **AI Assistant**: Ask questions about comparisons
- **Export Manager**: Save comparison results

---

## 📚 More Information

- Full documentation: `DOCUMENT_COMPARISON_TOOL.md`
- Technical details: See implementation summary
- API integration: Check backend endpoints

---

**Need Help?** Click the **? Help** button in the header

**Quick Access**: Keyboard shortcut (future): `Ctrl+Shift+C`

---

*Generated: November 23, 2025*
*Version: 1.0.0*
