# Enhanced Search System - Quick Start Guide

## Getting Started

The Enhanced Search System is now available in the Research Assistant Tool. Access it by:

1. Start the web UI: `python web_ui/app.py`
2. Navigate to http://localhost:5000
3. Click the **Search** tab in the header

## Search Modes

### 1. Simple Mode (Default)
**Best for**: Quick keyword searches

**How to use**:
1. Type your query in the search box
2. Press Enter or click "Search"
3. Results appear with relevance scores

**Example**: `climate change`

---

### 2. Advanced Mode
**Best for**: Filtered searches with specific criteria

**How to use**:
1. Click "Advanced" mode button
2. Click "Filters" button to show filter panel
3. Select filters:
   - ☑️ Types (Claims, Documents, Evidence)
   - 📅 Date range (From/To)
   - 📊 Minimum confidence (0-100%)
   - 🔬 Minimum investigation value (0-100%)
   - 👤 Author/Source
4. Click "Apply Filters"
5. Enter query and search

**Example**: Search for high-confidence claims from 2023

---

### 3. Semantic Mode
**Best for**: Finding similar concepts, even with different wording

**How to use**:
1. Click "Semantic" mode button
2. Adjust similarity threshold (0.5-0.95)
   - Higher = more strict matching
   - Lower = more related results
3. Enter query and search

**Example**: `machine learning` will find:
- "artificial intelligence"
- "neural networks"
- "deep learning"
- "AI models"

---

### 4. Natural Language Mode
**Best for**: Complex queries in plain English

**How to use**:
1. Click "Natural Language" mode button
2. Type a natural language query
3. System parses and extracts filters automatically

**Example queries**:
- "Find claims about climate change from 2023"
- "Show me high-confidence evidence about vaccines"
- "Find contradicting claims"

## Real-Time Search Preview

**Feature**: See results as you type

**How it works**:
1. Start typing in search box (minimum 3 characters)
2. Wait 300ms (debounce delay)
3. Preview dropdown appears with quick results
4. Click any result to view details
5. Or click "See All Results" for full search

**Tip**: Press Escape to close preview

## Search History

**Feature**: Access your recent searches

**How to use**:
1. Click the 📜 icon next to search box
2. Select from recent searches
3. Search is restored and executed

**Details**:
- Stores last 50 searches
- Shows relative time (e.g., "5m ago", "2h ago")
- Includes result count
- Persists in browser localStorage

## Saved Searches

**Feature**: Bookmark frequently used searches

**How to use**:

**To save**:
1. Run a search
2. Click "⭐ Save This Search"
3. Enter a name
4. Search is saved

**To load**:
1. Click on saved search name in panel
2. Search is restored and executed

**To delete**:
1. Click 🗑️ next to saved search

## Faceted Filters

### Type Filter
- ☑️ **Claims** - Research claims and assertions
- ☑️ **Documents** - Source documents
- ☑️ **Evidence** - Supporting evidence

### Date Range
- **From**: Start date (leave empty for no limit)
- **To**: End date (leave empty for no limit)

### Confidence Filter
- **Range**: 0-100%
- **Use**: Filter by claim confidence score

### Investigation Value
- **Range**: 0-100%
- **Use**: Filter by how valuable to investigate

### Author/Source
- **Type**: Multi-select dropdown
- **Use**: Filter by specific authors or sources

### Applying Filters
1. Set desired filters
2. Click "Apply Filters"
3. Filters apply to all searches until reset
4. Click "Reset" to clear all filters

## Understanding Results

### Result Card Components

```
┌─────────────────────────────────────────────┐
│ 📋 Claim Title                      [85% match] │
├─────────────────────────────────────────────┤
│ Type: claim  Confidence: 90%  Date: 2023-11-23 │
├─────────────────────────────────────────────┤
│ ▓▓▓▓▓▓▓▓░░░░ Relevance Breakdown            │
│ ■ Keywords  ■ Semantic  ■ Confidence         │
├─────────────────────────────────────────────┤
│ Highlighted search matches in snippet text... │
├─────────────────────────────────────────────┤
│ [👁️ View] [🔬 Investigate] [🔗 Related]      │
└─────────────────────────────────────────────┘
```

### Relevance Badge Colors
- **Green (90%+)**: Excellent match
- **Blue (70-89%)**: Good match
- **Orange (50-69%)**: Fair match
- **Red (<50%)**: Poor match

### Relevance Breakdown
Visual bar shows contribution from:
- **Green**: Keyword matching
- **Blue**: Semantic similarity
- **Orange**: Confidence score

### Result Actions
- **👁️ View**: Open in property viewer
- **🔬 Investigate**: Launch investigation agent
- **🔗 Related**: Find connected items

## Exporting Results

**Formats Available**:
1. **📄 JSON** - Structured data for programming
2. **📊 CSV** - Spreadsheet-compatible
3. **📝 Markdown** - Human-readable report

**How to export**:
1. Run a search
2. Click export button in results header
3. Select format
4. File downloads automatically

**File naming**: `search-results-{timestamp}.{ext}`

## Keyboard Shortcuts

- **Enter** in search box → Execute search
- **Escape** → Close preview dropdown
- **Click outside** → Close dropdowns

## Tips & Tricks

### Semantic Search Tips
1. **Use concepts, not exact words**
   - Instead of "car"
   - Try "vehicle" or "automobile" or "transportation"

2. **Adjust threshold based on needs**
   - High threshold (0.85+): Very similar results
   - Medium (0.70-0.84): Related concepts
   - Low (0.50-0.69): Broad associations

### Natural Language Tips
1. **Be specific with dates**
   - ✅ "from 2023"
   - ✅ "after January 2024"
   - ❌ "recent" (too vague)

2. **Include confidence requirements**
   - ✅ "high-confidence claims"
   - ✅ "with confidence above 80%"

3. **Specify intent clearly**
   - ✅ "find contradicting claims"
   - ✅ "compare evidence for and against"

### Filter Combination Tips
1. **Start broad, narrow down**
   - Run search without filters
   - Review results
   - Add filters to refine

2. **Use date ranges for temporal analysis**
   - Compare claims from different time periods
   - Track evolution of claims

3. **Combine confidence + investigation value**
   - High confidence + High investigation = Proven priorities
   - Low confidence + High investigation = Research gaps

## Common Use Cases

### 1. Literature Review
**Mode**: Semantic
**Setup**:
- Threshold: 0.75
- Type: Documents + Claims
- No date filter

**Query**: `machine learning applications`

**Result**: All documents and claims related to ML, including synonyms

---

### 2. Fact Checking
**Mode**: Natural Language
**Query**: `Find contradicting claims about vaccine efficacy`

**Result**: Claims that contradict each other, automatically detected

---

### 3. Research Gap Analysis
**Mode**: Advanced
**Filters**:
- Type: Claims
- Confidence: 0-50%
- Investigation Value: 70-100%

**Query**: Any keyword in your domain

**Result**: Low-confidence but high-value claims needing research

---

### 4. Source Verification
**Mode**: Advanced
**Filters**:
- Author: [Specific source]
- Date: [Specific range]

**Query**: Relevant keywords

**Result**: All content from specific source in timeframe

---

### 5. Trend Analysis
**Mode**: Advanced
**Setup**: Run same query with different date ranges

**Example**:
- 2020: `covid treatment`
- 2021: `covid treatment`
- 2022: `covid treatment`

**Result**: Evolution of claims over time

## Troubleshooting

### Issue: Semantic search returns no results
**Cause**: Nodes don't have embeddings
**Solution**: Ensure documents have been processed and embeddings generated

---

### Issue: Natural language search doesn't work
**Cause**: AI agent not configured
**Solution**: Configure Claude Code, OpenAI, or Gemini CLI in settings

---

### Issue: Preview doesn't show
**Cause**: Query too short (<3 characters)
**Solution**: Type at least 3 characters

---

### Issue: Filters not applying
**Cause**: Forgot to click "Apply Filters"
**Solution**: Click the green "Apply Filters" button after setting filters

---

### Issue: Search is slow
**Cause**: Large dataset or complex semantic search
**Solution**:
- Use keyword search for speed
- Increase semantic threshold for fewer comparisons
- Add more filters to reduce search space

---

### Issue: Saved searches disappeared
**Cause**: Browser localStorage cleared
**Solution**: Searches stored locally, clearing browser data removes them

## Advanced Features

### Combining Searches
1. Run search A, export results
2. Run search B, export results
3. Merge JSON/CSV files externally
4. Or use multiple saved searches

### Regular Expressions (Advanced)
Natural language mode supports regex patterns in queries when AI detects them.

**Example**: `claims matching pattern: COVID-\d+`

### Bulk Operations
1. Run search with filters
2. Export all results
3. Process externally (scripts, spreadsheets)
4. Re-import if needed

## Best Practices

### 1. Name Saved Searches Clearly
✅ "High-confidence vaccine claims 2023"
❌ "Search 1"

### 2. Use Templates
Create saved searches for common patterns:
- "Recent high-confidence"
- "Needs investigation"
- "Contradictions"

### 3. Combine Modes
- Start with Natural Language to explore
- Switch to Semantic to find related
- Use Advanced to filter precisely

### 4. Export Regularly
- Save important results as backups
- Use CSV for analysis in Excel
- Use JSON for programmatic processing

### 5. Review Search History
- Identify patterns in your searches
- Optimize frequently used queries
- Save common searches

## Performance Notes

### Fast Operations
- Keyword search: ~100-500ms
- Real-time preview: ~200-400ms
- Filter application: Instant

### Slower Operations
- Semantic search: ~1-5s (depends on dataset size)
- Natural language: ~2-10s (AI parsing overhead)
- Large exports: ~1-3s

### Optimization Tips
1. Use filters to reduce search space
2. Increase semantic threshold for faster semantic search
3. Export in batches for large result sets

## Support & Feedback

### Debug Mode
Open browser console (F12) to see:
```javascript
[EnhancedSearch] Initializing...
[EnhancedSearch] ✓ Initialized
[EnhancedSearch] Mode set to: semantic
[EnhancedSearch] Filters applied: {...}
```

### Reset Everything
To clear all saved data:
```javascript
// In browser console
localStorage.removeItem('research_search_history');
localStorage.removeItem('research_saved_searches');
location.reload();
```

## Summary

The Enhanced Search System provides powerful search capabilities:
- 🔍 **4 Search Modes**: Simple, Advanced, Semantic, Natural Language
- 🎯 **Smart Filtering**: Type, date, confidence, investigation, author
- 📜 **Search History**: Last 50 searches with quick restore
- ⭐ **Saved Searches**: Bookmark frequent searches
- ⚡ **Real-Time Preview**: See results as you type
- 📊 **Relevance Scoring**: Visual breakdown of match quality
- 📥 **Export**: JSON, CSV, Markdown formats

Start with Simple mode, explore Semantic for related concepts, and use Natural Language for complex queries!
