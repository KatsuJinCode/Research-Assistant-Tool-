# Robust Document Extraction Pipeline - TODO

## Problem

Current PDF extraction is failing on some documents (e.g., "The Myth of Mental Illness" PDF) with formatting issues:
- Text extraction includes copyright metadata, page headers/footers
- Malformed text causes processing timeouts
- No error recovery mechanism

## Required Solution: Intelligent Extraction Pipeline

### Architecture

```
Document Upload
    ↓
Text Extraction (pdfplumber/PyPDF2)
    ↓
Quality Check Agent ← Detects issues
    ↓
    ├─ PASS → Continue to Claim Extraction
    ↓
    └─ FAIL → Error Recovery Pipeline
              ↓
              Agent-Assisted Re-extraction
              ↓
              ├─ OCR if needed
              ├─ Format correction
              ├─ Metadata removal
              └─ Text cleaning
              ↓
              Retry Quality Check
              ↓
              Continue to Claim Extraction
```

### Components to Build

1. **Quality Check Agent**
   - Detects malformed text (excessive line breaks, garbled characters)
   - Identifies metadata pollution (copyright notices, page numbers)
   - Checks text coherence and readability
   - Returns diagnostic report with specific issues

2. **Error Recovery Agent**
   - Takes quality check report
   - Decides on recovery strategy:
     - Try alternative extraction library (PyPDF2 vs pdfplumber)
     - Apply OCR (Tesseract)
     - Use AI to clean/reformat text
     - Extract by page ranges and merge
   - Iteratively improves extraction until quality check passes

3. **Format-Agnostic Extraction**
   - PDF: pdfplumber → PyPDF2 → OCR fallback
   - DOCX: python-docx → pandoc fallback
   - TXT: Direct read with encoding detection
   - HTML: BeautifulSoup → Readability
   - EPUB: ebooklib
   - Images: Tesseract OCR

4. **Preprocessing Pipeline**
   - Remove headers/footers (detect repeated patterns)
   - Strip metadata sections
   - Fix encoding issues
   - Normalize whitespace
   - Preserve paragraph structure

### Implementation Priority

- [ ] **High**: Quality check agent (detects bad extractions)
- [ ] **High**: Preprocessing pipeline (clean common issues)
- [ ] **Medium**: Alternative extraction methods (fallbacks)
- [ ] **Medium**: Error recovery agent (intelligent retry)
- [ ] **Low**: OCR support for scanned PDFs
- [ ] **Low**: Format-specific extractors (EPUB, HTML)

### Success Criteria

- No extraction failures due to formatting
- All document types supported
- Automatic error recovery (no manual intervention)
- Quality-checked text before claim extraction
- Clear error messages when extraction is impossible

### Current Error Example

```
Command '['claude', '-p', 'Extract factual research claims from this text...']' timed out after 120 seconds
```

**Root Cause**: Text includes copyright boilerplate and malformed content, causing Claude to struggle with extraction.

**Fix**: Add preprocessing to remove metadata and validate text quality before sending to agent.

## Related Files

- `web_ui/document_processor.py` - Main processing logic
- `web_ui/app.py` - Upload handling
- Future: `web_ui/extraction_pipeline.py` - New robust extractor
